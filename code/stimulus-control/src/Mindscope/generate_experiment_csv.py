# -*- coding: utf-8 -*-
"""
Experimental Session CSV Generator (Single-Session Mode Only)

Simplified to ONLY support the entrypoint used by the Bonsai experiment launcher.
All former multi-session / variant / example generation code has been removed to
reduce maintenance overhead and avoid divergent stimulus definitions.

Usage (launcher / manual):
        python generate_experiment_csv.py --session-type sensorimotor_mismatch --output-path C:/path/to/file.csv --seed 12345

Available session types (single complete session per invocation):
    - visual_mismatch
    - sensorimotor_mismatch  
    - sequence_mismatch
    - duration_mismatch
    - sequence_mismatch_no_oddball
    - sensorimotor_mismatch_no_oddball

NOTES:
    * open_loop_prerecorded blocks now include explicit oddball_config so prerecorded
        phase segments receive motor oddballs (same rates as motor_oddball blocks).
    * Strict phase loading: no fallbacks; raises RuntimeError on any data issue.
    * Python 2.7 compatible.
"""

import csv
import random
import numpy as np
import math
import os
import argparse
import sys
import glob

# Standard column order for all CSV files
STANDARD_FIELDNAMES = [
    'Contrast', 'Delay', 'DiameterX', 'DiameterY', 'Duration', 'Orientation', 
    'Spatial_Frequency', 'Temporal_Frequency', 'X', 'Y', 
    'Phase', 'Trial_Type', 'Block_Type'
]

# Default stimulus size
DEFAULT_STIMULUS_SIZE = 360  # degrees (full field)

# Default parameters for standard trials
DEFAULT_PARAMS = {
    'Contrast': 1,
    'Delay': 0.343,
    'DiameterX': DEFAULT_STIMULUS_SIZE,  # Full field horizontal extent
    'DiameterY': DEFAULT_STIMULUS_SIZE,  # Full field vertical extent
    'Duration': 0.343,
    'Orientation': 0,  # degrees
    'Spatial_Frequency': 0.04,
    'Temporal_Frequency': 2,
    'X': 0,
    'Y': 0,
    'Phase': 0,  # Default phase
    'Trial_Type': 'standard',
    'Block_Type': 'standard_oddball'
}

# Default parameters for sequential trials
SEQUENTIAL_PARAMS = {
    'Contrast': 1,
    'Delay': 0,  # 0 delay for sequential
    'DiameterX': DEFAULT_STIMULUS_SIZE,  # Full field horizontal extent
    'DiameterY': DEFAULT_STIMULUS_SIZE,  # Full field vertical extent
    'Duration': 0.250,  # 250ms duration
    'Orientation': 0,  # will be overridden
    'Spatial_Frequency': 0.04,
    'Temporal_Frequency': 2,
    'X': 0,
    'Y': 0,
    'Phase': 0,  # Default phase
    'Trial_Type': 'standard',
    'Block_Type': 'sequential_oddball'
}

# Oddball type definitions for flexible configuration
ODDBALL_TYPES = {
    'orientation_45': {'Orientation': 45, 'Trial_Type': 'orientation_45'},
    'orientation_90': {'Orientation': 90, 'Trial_Type': 'orientation_90'},
    'halt': {'Temporal_Frequency': 0, 'Trial_Type': 'halt'},
    'omission': {'Contrast': 0, 'Trial_Type': 'omission'},
    'jitter_150': {'Duration': 0.150, 'Trial_Type': 'jitter'},
    'jitter_350': {'Duration': 0.350, 'Trial_Type': 'jitter'},
    # Motor-prefixed variants keep distinct Trial_Type labels for clarity in CSV
    'motor_halt': {'Temporal_Frequency': 0, 'Delay': 0, 'Trial_Type': 'motor_halt'},
    'motor_omission': {'Contrast': 0, 'Delay': 0, 'Trial_Type': 'motor_omission'},
    'motor_orientation_45': {'Orientation': 45, 'Delay': 0, 'Temporal_Frequency': 2, 'Trial_Type': 'motor_orientation_45'},
    'motor_orientation_90': {'Orientation': 90, 'Delay': 0, 'Temporal_Frequency': 2, 'Trial_Type': 'motor_orientation_90'}
}

def generate_rf_mapping_positions():
    """Return (x,y) positions for 9x9 grid spanning -40..+40 deg in 10 deg steps."""
    positions = []
    for x in range(-40, 50, 10):
        for y in range(-40, 50, 10):
            positions.append((x, y))
    return positions

def _load_pre_recorded_phases_radians(duration_seconds, variant_seed):
    """Strictly load contiguous wheel-derived phase samples (radians) at 30Hz.

    Requirements (no fallbacks):
      * running_phases/ directory adjacent to this script.
      * At least one CSV file present.
      * One of columns: Phase_Radians OR (Phase_Degrees / Phase / PhaseDegrees / Phase_deg) for degrees.
      * Sufficient rows (>= duration_seconds * 30).
    Raises RuntimeError on any violation.
    """
    base_dir = os.path.join(os.path.dirname(__file__), 'running_phases')
    target = int(duration_seconds * 30)
    if target <= 0:
        raise RuntimeError('Requested non-positive duration for prerecorded phases')
    if not os.path.isdir(base_dir):
        raise RuntimeError('Missing running_phases directory: %s' % base_dir)
    files = glob.glob(os.path.join(base_dir, '*.csv'))
    if not files:
        raise RuntimeError('No CSV files found in running_phases directory')
    rng = random.Random(variant_seed + 1337)
    chosen = rng.choice(files)
    with open(chosen, 'r') as f:
        header = f.readline().strip().split(',')
        name_to_idx = {}
        for i, name in enumerate(header):
            name_to_idx[name.strip()] = i
        phase_col = name_to_idx['Phase_Radians']
        phases = []
        for line in f:
            if not line.strip():
                continue
            parts = line.rstrip().split(',')
            if phase_col >= len(parts):
                continue
            val = float(parts[phase_col])
            phases.append(val)
    if len(phases) < target:
        raise RuntimeError('Not enough samples in %s (have %d need %d)' % (os.path.basename(chosen), len(phases), target))
    max_start = len(phases) - target
    start = rng.randint(0, max_start)
    return phases[start:start + target]

def _inject_prerecorded_mismatch(trials, duration_minutes, variant_seed, oddball_config):
    """Inject motor oddball events into prerecorded trials according to rates.

    Ensures ~2s minimum spacing (at 30Hz -> 60 trial minimum) and 5s start/end buffer.
    Modifies trials in place.
    """
    if not trials or not oddball_config:
        return
    total_trials = len(trials)
    r = random.Random(variant_seed + 4242)
    min_interval_trials = int(2.0 * 30)
    buffer_trials = int(5.0 * 30)
    candidates = list(range(buffer_trials, max(buffer_trials, total_trials - buffer_trials)))
    r.shuffle(candidates)
    # Build list of oddball types to place
    oddball_types = []
    for odd_type, rate in oddball_config.items():
        count = int(rate * duration_minutes)
        oddball_types.extend([odd_type] * count)
    r.shuffle(oddball_types)
    if not oddball_types:
        return
    placed_indices = []
    for idx in candidates:
        if all(abs(idx - p) >= min_interval_trials for p in placed_indices):
            placed_indices.append(idx)
            if len(placed_indices) >= len(oddball_types):
                break
    placed_indices.sort()
    if not placed_indices:
        return
    # Trim or extend oddball_types to match
    if len(placed_indices) < len(oddball_types):
        oddball_types = oddball_types[:len(placed_indices)]
    elif len(placed_indices) > len(oddball_types):
        last = oddball_types[-1]
        while len(oddball_types) < len(placed_indices):
            oddball_types.append(last)
    for idx, odd_type in zip(placed_indices, oddball_types):
        if idx < 0 or idx >= total_trials:
            continue
        trial = trials[idx]
        params = ODDBALL_TYPES.get(odd_type)
        if not params:
            continue
        if 'Orientation' in params:
            trial['Orientation'] = params['Orientation']
        if 'Contrast' in params:
            trial['Contrast'] = params['Contrast']
        # Temporal frequency rules: halt -> 0, orientation/omission -> 2Hz drifting
        if params.get('Trial_Type') == 'motor_halt':
            trial['Temporal_Frequency'] = 0
        else:
            trial['Temporal_Frequency'] = 2
        trial['Duration'] = 0.343  # Match standard oddball duration
        trial['Trial_Type'] = params['Trial_Type']
        # Ensure block type stays consistent
        trial['Block_Type'] = 'open_loop_prerecorded'

def generate_block_trials(block_type, duration_minutes, oddball_config=None, variant=0, block_config=None):
    """
    Generate trials for a specific block type.
    
    Args:
        block_type: Type of block to generate
        duration_minutes: Duration of the block in minutes
        oddball_config: Dictionary of oddball configurations
        variant: Variant number for randomization
        
    Returns:
        List of trial dictionaries
    """
    random.seed(variant * 42 + hash(block_type))
    
    duration_seconds = duration_minutes * 60
    trials = []
    
    if block_type == 'standard_control':
        # Control block 1: 14 orientations + omissions + halts, shuffled
        # Similar to sequential_control_block but with standard trial duration (343ms)
        
        # 14 directions (every 22.5 degrees)
        orientations = list(np.arange(0, 360, 22.5)[:14])  # 14 orientations
        n_repeats = max(1, int(duration_minutes * 60 / (len(orientations) + 2) / 0.686))  # +2 for omission and halt types
        
        all_trials_pool = []
        
        # Add orientation trials
        for orientation in orientations:
            for _ in range(n_repeats):
                trial = DEFAULT_PARAMS.copy()
                trial['Orientation'] = orientation
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'standard_control'
                trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                all_trials_pool.append(trial)
        
        # Add omission trials (same number of repeats)
        for _ in range(n_repeats):
            trial = DEFAULT_PARAMS.copy()
            trial['Contrast'] = 0
            trial['Trial_Type'] = 'omission'
            trial['Block_Type'] = 'standard_control'
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Add halt trials (same number of repeats)
        for _ in range(n_repeats):
            trial = DEFAULT_PARAMS.copy()
            trial['Temporal_Frequency'] = 0
            trial['Trial_Type'] = 'halt'
            trial['Block_Type'] = 'standard_control'
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Shuffle all trials
        random.shuffle(all_trials_pool)
        trials.extend(all_trials_pool)
    
    elif block_type == 'jitter_control':
        # Duration tuning
        durations = [0.050, 0.100, 0.200, 0.343]
        n_repeats = max(1, int(duration_minutes * 60 / (len(durations) * 0.686)))
        
        for duration in durations:
            for _ in range(n_repeats):
                trial = DEFAULT_PARAMS.copy()
                trial['Duration'] = duration
                trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'jitter_control'
                trials.append(trial)
    
    elif block_type == 'open_loop_prerecorded':
        # Pre-recorded wheel-driven phases (radians only, strict, no fallback)
        grating_update_rate = 30
        grating_duration = 1.0 / grating_update_rate
        phase_rads = _load_pre_recorded_phases_radians(duration_seconds, variant)
        for p in phase_rads:
            trial = {
                'Contrast': 1,
                'Delay': 0,
                'DiameterX': DEFAULT_STIMULUS_SIZE,
                'DiameterY': DEFAULT_STIMULUS_SIZE,
                'Duration': grating_duration,
                'Orientation': 0,
                'Spatial_Frequency': 0.04,
                'Temporal_Frequency': 0,
                'X': 0,
                'Y': 0,
                'Phase': p,  # radians
                'Trial_Type': 'prerecorded',
                'Block_Type': 'open_loop_prerecorded'
            }
            trials.append(trial)
        _inject_prerecorded_mismatch(trials, duration_minutes, variant, oddball_config)
    
    elif block_type == 'sequential_control_block':
        # Control block 2: Sequential-like stimuli but shuffled (not in sequences)
        # 14 orientations + omissions + halts, each repeated 70 times, shuffled
        # Uses 250ms duration like sequential blocks but without sequence structure
        
        # 14 directions (every 22.5 degrees)
        orientations = list(np.arange(0, 360, 22.5)[:14])  # 14 orientations
        n_repeats = 70
        
        all_trials_pool = []
        
        # Add orientation trials
        for orientation in orientations:
            for _ in range(n_repeats):
                trial = SEQUENTIAL_PARAMS.copy()
                trial['Orientation'] = orientation
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'sequential_control_block'
                trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                all_trials_pool.append(trial)
        
        # Add omission trials (70 repeats)
        for _ in range(n_repeats):
            trial = SEQUENTIAL_PARAMS.copy()
            trial['Contrast'] = 0
            trial['Trial_Type'] = 'omission'
            trial['Block_Type'] = 'sequential_control_block'
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Add halt trials (70 repeats)
        for _ in range(n_repeats):
            trial = SEQUENTIAL_PARAMS.copy()
            trial['Temporal_Frequency'] = 0
            trial['Trial_Type'] = 'halt'
            trial['Block_Type'] = 'sequential_control_block'
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Shuffle all trials
        random.shuffle(all_trials_pool)
        trials.extend(all_trials_pool)
    
    elif block_type == 'sequential_long':
        # Long sequential block without oddballs - just repeating standard sequences
        sequence_duration = 1.25  # 5 × 0.250s
        total_sequences = int(duration_seconds / sequence_duration)
        
        # Standard sequence pattern repeated for the entire duration
        standard_sequence = [90, 45, 0, 45]
        
        for _ in range(total_sequences):
            # Generate 5 trials per sequence (4 gratings + 1 omission)
            for trial_in_seq in range(5):
                trial = SEQUENTIAL_PARAMS.copy()
                trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                trial['Block_Type'] = 'sequential_long'
                
                if trial_in_seq == 4:  # Last trial is sequence omission (not oddball)
                    trial['Contrast'] = 0
                    trial['Trial_Type'] = 'sequence_omission'
                else:
                    trial['Orientation'] = standard_sequence[trial_in_seq]
                    trial['Trial_Type'] = 'standard'
                
                trials.append(trial)
    
    elif block_type == 'motor_long':
        # Long motor block without oddballs - just continuous closed-loop control
        # Use 60Hz timing but limit grating updates to 30Hz for better Bonsai performance
        frame_rate = 60
        grating_update_rate = 30  # Grating changes at 30Hz (every 2 frames)
        total_frames = int(duration_seconds * frame_rate)
        frame_duration = 1.0 / frame_rate  # 16.67ms per frame
        grating_duration = 1.0 / grating_update_rate  # 33.33ms per grating update
        
        # Generate frame-by-frame trials with wheel-controlled phase
        for frame in range(total_frames):
            # Skip every other frame to achieve 30Hz grating updates at 60Hz frame rate
            if frame % 2 == 0:  # Only add trials every 2 frames (30Hz grating rate)
                trial = {
                    'Contrast': 1,
                    'Delay': 0,
                    'DiameterX': DEFAULT_STIMULUS_SIZE,
                    'DiameterY': DEFAULT_STIMULUS_SIZE,
                    'Duration': grating_duration,  # 33.33ms for 30Hz grating updates
                    'Orientation': 0,
                    'Spatial_Frequency': 0.04,
                    'Temporal_Frequency': 0,  # Wheel-controlled
                    'X': 0,
                    'Y': 0,
                    'Phase': 'wheel',  # Phase controlled by wheel
                    'Trial_Type': 'standard',
                    'Block_Type': 'motor_long'
                }
                trials.append(trial)
    
    elif block_type == 'rf_mapping':
        # RF mapping with parameters matching create_receptive_field_mapping()
        rf_positions = generate_rf_mapping_positions()  # 81 positions (9×9 grid)
        orientations = [0, 45, 90]  # 3 orientations  
        # Target ~5 minutes: 81 positions * 3 orientations * repeats * 0.25s ≈ 60.75s * repeats
        # repeats=5 gives ~304s (~5.07 min)
        n_repeats = 5
        
        # Parameters matching experimental code
        contrast = 0.8
        spatial_frequency = 0.08  # cycles/degree
        temporal_frequency = 4.0  # Hz
        sweep_length = 0.25  # seconds
        size = 20  # degrees diameter
        
        for x, y in rf_positions:
            for orientation in orientations:
                for _ in range(n_repeats):
                    trial = {
                        'Contrast': contrast,
                        'Delay': 0.0,  # No ISI (blank_length=0.0)
                        'DiameterX': size,
                        'DiameterY': size,
                        'Duration': sweep_length,
                        'Orientation': orientation,
                        'Spatial_Frequency': spatial_frequency,
                        'Temporal_Frequency': temporal_frequency,
                        'X': x,
                        'Y': y,
                        'Phase': 0,
                        'Trial_Type': 'rf_mapping',
                        'Block_Type': 'rf_mapping'
                    }
                    trials.append(trial)
        # Explicit shuffle to randomize RF mapping order (positions × orientations × repeats)
        random.shuffle(trials)
    
    elif block_type.startswith('movie_'):
        # Movie presentation blocks
        width = (block_config or {}).get('width', 120)
        height = (block_config or {}).get('height', 95)
        repeats = (block_config or {}).get('repeats', 1)
        movie_duration_s = (block_config or {}).get('movie_duration_s', int(duration_minutes*60))
        # Each repeat is one row; duration stored in Duration (seconds), Delay=0
        for rep in range(repeats):
            trial = {
                'Contrast': 1,
                'Delay': 0,
                'DiameterX': width,
                'DiameterY': height,
                'Duration': movie_duration_s,
                'Orientation': 0,
                'Spatial_Frequency': 0,
                'Temporal_Frequency': 0,  
                'X': 0,
                'Y': 0,
                'Phase': 0,
                'Trial_Type': 'single',
                'Block_Type': 'movie'
            }
            trials.append(trial)

    elif block_type in ['standard_oddball', 'jitter_oddball', 'sequential_oddball']:
        # Oddball blocks with specified mismatch rates
        trials = generate_oddball_block_trials(block_type, duration_minutes, oddball_config, variant)
    
    elif block_type in ['motor_oddball', 'motor_control']:
        # Motor blocks - frame-by-frame control
        trials = generate_motor_block_trials(block_type, duration_minutes, oddball_config, variant)
    
    # Shuffle trials (except for those which maintains structure)
    if block_type not in ['open_loop_prerecorded', 'sequential_oddball', 'sequential_long']:
        # Don't shuffle movie or rf mapping order
        if not block_type.startswith('movie_'):
            random.shuffle(trials)
    
    return trials

def generate_oddball_block_trials(block_type, duration_minutes, oddball_config, variant):
    """Generate trials for oddball blocks (standard, jitter, sequential)."""
    random.seed(variant * 123 + hash(block_type))
    
    duration_seconds = duration_minutes * 60
    trials = []
    
    if block_type == 'standard_oddball':
        trial_duration = 0.686  # 0.343s + 0.343s delay
        total_trials = int(duration_seconds / trial_duration)
        
        # Calculate oddball trials
        total_oddball_rate = sum(oddball_config.values()) if oddball_config else 8.0  # per minute
        total_oddballs = int(total_oddball_rate * duration_minutes)
        n_standards = total_trials - total_oddballs
        
        # Add standard trials
        for _ in range(n_standards):
            trial = DEFAULT_PARAMS.copy()
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            trial['Trial_Type'] = 'standard'
            trial['Block_Type'] = 'standard_oddball'
            trials.append(trial)
        
        # Add oddball trials
        if oddball_config:
            for oddball_type, rate_per_minute in oddball_config.items():
                n_oddballs = int(rate_per_minute * duration_minutes)
                oddball_params = ODDBALL_TYPES[oddball_type]
                
                for _ in range(n_oddballs):
                    trial = DEFAULT_PARAMS.copy()
                    trial.update(oddball_params)
                    trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                    trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                    trial['Block_Type'] = 'standard_oddball'
                    trials.append(trial)
    
    elif block_type == 'jitter_oddball':
        # Similar logic for jitter oddball
        trial_duration = 0.686
        total_trials = int(duration_seconds / trial_duration)
        
        total_oddball_rate = sum(oddball_config.values()) if oddball_config else 4.0
        total_oddballs = int(total_oddball_rate * duration_minutes)
        n_standards = total_trials - total_oddballs
        
        # Add standard trials (using jitter context)
        for _ in range(n_standards):
            trial = DEFAULT_PARAMS.copy()
            trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            trial['Trial_Type'] = 'standard'
            trial['Block_Type'] = 'jitter_oddball'
            trials.append(trial)
        
        # Add oddball trials
        if oddball_config:
            for oddball_type, rate_per_minute in oddball_config.items():
                n_oddballs = int(rate_per_minute * duration_minutes)
                oddball_params = ODDBALL_TYPES[oddball_type]
                
                for _ in range(n_oddballs):
                    trial = DEFAULT_PARAMS.copy()
                    trial.update(oddball_params)
                    trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                    trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                    trial['Block_Type'] = 'jitter_oddball'
                    trials.append(trial)
    
    elif block_type == 'sequential_oddball':
        # Sequential blocks work with sequences (5 trials each)
        sequence_duration = 1.25  # 5 × 0.250s
        total_sequences = int(duration_seconds / sequence_duration)
        
        total_oddball_rate = sum(oddball_config.values()) if oddball_config else 2.0  # sequences per minute
        total_oddball_sequences = int(total_oddball_rate * duration_minutes)
        n_standard_sequences = total_sequences - total_oddball_sequences
        
        # Generate sequences
        sequences = []
        
        # Standard sequences
        standard_sequence = [90, 45, 0, 45]
        for _ in range(n_standard_sequences):
            sequences.append(('normal', standard_sequence))
        
        # Oddball sequences
        if oddball_config:
            oddball_sequences_per_type = total_oddball_sequences // len(oddball_config)
            for oddball_type in oddball_config:
                for _ in range(oddball_sequences_per_type):
                    if oddball_type == 'orientation_45':
                        sequences.append(('oddball_45', [90, 45, 45, 45]))
                    elif oddball_type == 'orientation_90':
                        sequences.append(('oddball_90', [90, 45, 90, 45]))
                    elif oddball_type == 'halt':
                        sequences.append(('oddball_halt', [90, 45, -1, 45]))  # -1 = halt
                    elif oddball_type == 'omission':
                        sequences.append(('oddball_omission', [90, 45, -2, 45]))  # -2 = omission
        
        # Shuffle sequences
        random.shuffle(sequences)
        
        # Convert sequences to trials
        for seq_type, sequence in sequences:
            is_oddball = seq_type != 'normal'
            
            # Generate 5 trials per sequence
            for trial_pos, orientation in enumerate(sequence):
                trial = SEQUENTIAL_PARAMS.copy()
                trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
                trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
                trial['Block_Type'] = 'sequential_oddball'
                
                if orientation == -1:  # halt
                    trial['Orientation'] = 0
                    trial['Spatial_Frequency'] = 0
                    trial['Trial_Type'] = 'halt'
                elif orientation == -2:  # omission
                    trial['Orientation'] = 0
                    trial['Contrast'] = 0
                    trial['Trial_Type'] = 'omission'
                else:
                    trial['Orientation'] = orientation
                    # Check if this is the oddball trial (position 2, which is 3rd trial)
                    if is_oddball and trial_pos == 2:  # 0-indexed, so position 2 = 3rd trial
                        if seq_type == 'oddball_45':
                            trial['Trial_Type'] = 'orientation_45'
                        elif seq_type == 'oddball_90':
                            trial['Trial_Type'] = 'orientation_90'
                        else:
                            trial['Trial_Type'] = 'standard'
                    else:
                        trial['Trial_Type'] = 'standard'
                
                trials.append(trial)
            
            # Add sequence-ending omission (not counted as oddball)
            omission_trial = SEQUENTIAL_PARAMS.copy()
            omission_trial['Contrast'] = 0
            omission_trial['Trial_Type'] = 'sequence_omission'  # Different from oddball omission
            omission_trial['Block_Type'] = 'sequential_oddball'
            omission_trial['DiameterX'] = DEFAULT_STIMULUS_SIZE
            omission_trial['DiameterY'] = DEFAULT_STIMULUS_SIZE
            trials.append(omission_trial)
    
    return trials

def generate_motor_block_trials(block_type, duration_minutes, oddball_config, variant):
    """Generate frame-by-frame trials for motor blocks."""
    random.seed(variant * 789 + hash(block_type))
    
    # Use 60Hz timing but limit grating updates to 30Hz for better Bonsai performance
    frame_rate = 60
    grating_update_rate = 30  # Grating changes at 30Hz (every 2 frames)
    duration_seconds = duration_minutes * 60
    total_frames = int(duration_seconds * frame_rate)
    frame_duration = 1.0 / frame_rate  # 16.67ms per frame
    grating_duration = 1.0 / grating_update_rate  # 33.33ms per grating update
    
    trials = []
    
    if block_type == 'motor_control':
        # Pure closed-loop control - generate realistic wheel movement
        phase_values = []
        current_phase = 0.0
        velocity = 0.0
        
        for frame in range(total_frames):
            # Simple mouse wheel simulation - update behavior every second (60 frames at 60Hz)
            if frame % 60 == 0:  # Update behavior every second (60 frames at 60Hz)
                velocity += random.gauss(0, 0.05)
                velocity *= 0.95  # friction
                velocity = max(-0.3, min(0.3, velocity))
            
            current_phase += velocity
            current_phase = current_phase % (2 * math.pi)
            phase_values.append(current_phase)
        
        for frame in range(total_frames):
            # Skip every other frame to achieve 30Hz grating updates at 60Hz frame rate
            if frame % 2 == 0:  # Only add trials every 2 frames (30Hz grating rate)
                trial = {
                    'Contrast': 1,
                    'Delay': 0,
                    'DiameterX': DEFAULT_STIMULUS_SIZE,
                    'DiameterY': DEFAULT_STIMULUS_SIZE,
                    'Duration': grating_duration,  # 33.33ms for 30Hz grating updates
                    'Orientation': 0,
                    'Spatial_Frequency': 0.04,
                    'Temporal_Frequency': 0,  # Wheel-controlled
                    'X': 0,
                    'Y': 0,
                    'Phase': phase_values[frame],
                    'Trial_Type': 'standard',
                    'Block_Type': 'motor_control'
                }
                trials.append(trial)
    
    elif block_type == 'motor_oddball':
        # Motor oddball with discrete oddball events
        min_interval_frames = 120  # 2 seconds minimum at 60Hz
        oddball_duration_frames = 21  # ~0.35 seconds at 60Hz
        
        # Calculate oddball positions
        total_oddball_rate = sum(oddball_config.values()) if oddball_config else 8.0
        total_oddballs = int(total_oddball_rate * duration_minutes)
        
        # Generate oddball positions with minimum intervals
        possible_frames = list(range(300, total_frames - 300))  # 5s buffer
        random.shuffle(possible_frames)
        
        oddball_frames = []
        for frame in possible_frames:
            if all(abs(frame - selected) >= min_interval_frames for selected in oddball_frames):
                oddball_frames.append(frame)
                if len(oddball_frames) >= total_oddballs:
                    break
        
        oddball_frames.sort()
        
        # Assign oddball types
        oddball_types_list = []
        if oddball_config:
            for oddball_type, rate in oddball_config.items():
                n_type = int(rate * duration_minutes)
                oddball_types_list.extend([oddball_type] * n_type)
        random.shuffle(oddball_types_list)
        
        # Generate frame-by-frame trials
        frame = 0
        oddball_index = 0
        
        while frame < total_frames:
            if oddball_index < len(oddball_frames) and frame == oddball_frames[oddball_index]:
                # This is an oddball frame
                oddball_type = oddball_types_list[oddball_index] if oddball_index < len(oddball_types_list) else 'motor_halt'
                oddball_params = ODDBALL_TYPES[oddball_type]
                
                trial = {
                    'Contrast': oddball_params.get('Contrast', 1),
                    'Delay': 0,
                    'DiameterX': DEFAULT_STIMULUS_SIZE,
                    'DiameterY': DEFAULT_STIMULUS_SIZE,
                    'Duration': 0.343,  # Oddball duration
                    'Orientation': oddball_params.get('Orientation', 0),
                    'Spatial_Frequency': 0.04,
                    'Temporal_Frequency': oddball_params.get('Temporal_Frequency', 2),
                    'X': 0,
                    'Y': 0,
                    'Phase': 'wheel',
                    'Trial_Type': oddball_params['Trial_Type'],
                    'Block_Type': 'motor_oddball'
                }
                trials.append(trial)
                
                frame += oddball_duration_frames
                oddball_index += 1
            else:
                # Normal frame - use 30Hz grating updates (every 2 frames)
                if frame % 2 == 0:  # Only add trials every 2 frames (30Hz grating rate)
                    trial = {
                        'Contrast': 1,
                        'Delay': 0,
                        'DiameterX': DEFAULT_STIMULUS_SIZE,
                        'DiameterY': DEFAULT_STIMULUS_SIZE,
                        'Duration': grating_duration,  # 33.33ms for 30Hz grating updates
                        'Orientation': 0,
                        'Spatial_Frequency': 0.04,
                        'Temporal_Frequency': 0,
                        'X': 0,
                        'Y': 0,
                        'Phase': 'wheel',
                        'Trial_Type': 'standard',
                        'Block_Type': 'motor_oddball'
                    }
                    trials.append(trial)
                frame += 1
    
    return trials

def generate_single_session_csv(session_type, output_path, seed=None):
    """
    Generate a single session CSV file for the specified session type.
    
    Args:
        session_type (str): Type of session ('visual_mismatch', 'sensorimotor_mismatch', etc.)
        output_path (str): Path where the CSV file should be saved
        seed (int, optional): Random seed for reproducibility
        
    Returns:
        bool: True if successful, False otherwise
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        print("Using random seed: %d" % seed)
    
    # Session configurations matching the existing structure
    session_configs = {
        'short_test': {
            # ~5 minute comprehensive test covering each block type with at least one oddball of each configured kind
            'blocks': [
                # Standard oddball (1.0 min) -> ensures >=1 of each orientation/halt/omission
                {'type': 'standard_oddball', 'duration_minutes': 1.0, 'label': 'Std mismatch (test)',
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                # Motor oddball (1.0 min)
                {'type': 'motor_oddball', 'duration_minutes': 1.0, 'label': 'Motor mismatch (test)',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                # Sequential oddball (0.75 min)
                {'type': 'sequential_oddball', 'duration_minutes': 0.75, 'label': 'Seq mismatch (test)',
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                # Jitter (duration) oddball (0.75 min)
                {'type': 'jitter_oddball', 'duration_minutes': 0.75, 'label': 'Duration mismatch (test)',
                 'oddball_config': {'jitter_150': 1.35, 'jitter_350': 1.35}},
                # Open loop prerecorded with motor oddballs (0.75 min)
                {'type': 'open_loop_prerecorded', 'duration_minutes': 0.75, 'label': 'Open loop (test)',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                # Short movies (Trippy 15s, Zebra 15s)
                {'type': 'movie_trippy', 'duration_minutes': 0.25, 'label': 'Trippy (test)', 'movie_duration_s': 15, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 0.25, 'label': 'Zebra (test)', 'movie_duration_s': 15, 'repeats': 1, 'width': 120, 'height': 95},
                # Very short RF mapping sample (15s ~ 0.25 min): reduces repeats to shorten duration
                {'type': 'rf_mapping', 'duration_minutes': 0.25, 'label': 'RF mapping (test)'}
            ]
        },
        'visual_mismatch': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'standard_oddball', 'duration_minutes': 26, 'label': 'Standard mismatch block', 
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        },
        'sensorimotor_mismatch': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'motor_oddball', 'duration_minutes': 26, 'label': 'Sensory-motor mismatch block',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        },
        'sequence_mismatch': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'sequential_oddball', 'duration_minutes': 26, 'label': 'Sequence mismatch block',
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        },
        'duration_mismatch': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'jitter_oddball', 'duration_minutes': 26, 'label': 'Duration mismatch block',
                 'oddball_config': {'jitter_150': 1.35, 'jitter_350': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        },
        'sequence_mismatch_no_oddball': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'sequential_long', 'duration_minutes': 26, 'label': 'Sequence long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        },
        'sensorimotor_mismatch_no_oddball': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'motor_long', 'duration_minutes': 26, 'label': 'Sensory-motor long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'movie_trippy', 'duration_minutes': 5, 'label': 'Trippy', 'movie_duration_s': 150, 'repeats': 2, 'width': 120, 'height': 95},
                {'type': 'movie_zebra', 'duration_minutes': 5, 'label': 'Zebra', 'movie_duration_s': 300, 'repeats': 1, 'width': 120, 'height': 95},
                {'type': 'rf_mapping', 'duration_minutes': 5, 'label': 'RF mapping'}
            ]
        }
    }
    
    # Add shorter aliases for convenience
    if session_type == 'sensorimotor_no_oddball':
        session_type = 'sensorimotor_mismatch_no_oddball'
    elif session_type == 'sequence_no_oddball':
        session_type = 'sequence_mismatch_no_oddball'
    
    if session_type not in session_configs:
        print("Error: Unknown session type '%s'" % session_type)
        print("Available session types: %s" % ', '.join(session_configs.keys()))
        return False
    
    session_config = session_configs[session_type]
    
    print("Generating %s session CSV..." % session_type)
    
    # Standard fieldnames
    fieldnames = [
        'Block_Number', 'Block_Label', 'Block_Duration_Minutes',
        'Trial_Number', 'Sequence_Number', 'Trial_In_Sequence',
    ] + STANDARD_FIELDNAMES
    
    all_trials = []
    trial_counter = 0
    
    # Generate each block in the session
    for block_number, block_config in enumerate(session_config['blocks'], 1):
        block_type = block_config['type']
        duration_minutes = block_config['duration_minutes']
        block_label = block_config['label']
        oddball_config = block_config.get('oddball_config', None)
        
        print("  Block %d: %s (%.1f min)" % (block_number, block_label, duration_minutes))
        
        # Generate trials for this block
        block_trials = generate_block_trials(
            block_type=block_type,
            duration_minutes=duration_minutes,
            oddball_config=oddball_config,
            variant=0,  # Single variant for launcher mode
            block_config=block_config  # Pass full config so movie repeats/durations are applied
        )
        
        # Add block metadata to each trial
        sequence_counter = 0
        current_sequence_trial = 0
        
        for i, trial in enumerate(block_trials):
            trial_counter += 1
            
            # Handle sequence numbering for sequential blocks
            if block_type in ['sequential_oddball', 'open_loop_prerecorded']:
                if current_sequence_trial == 0:
                    sequence_counter += 1
                current_sequence_trial = (current_sequence_trial + 1) % 5
                trial_in_sequence = current_sequence_trial if current_sequence_trial > 0 else 5
            else:
                sequence_counter = 0
                trial_in_sequence = 0
            
            # Add metadata
            enriched_trial = {
                'Block_Number': block_number,
                        'Block_Label': block_label,
                'Block_Duration_Minutes': duration_minutes,
                'Trial_Number': trial_counter,
                'Sequence_Number': sequence_counter,
                'Trial_In_Sequence': trial_in_sequence,
            }
            # Add all the stimulus parameters (Python 2.7 compatible)
            enriched_trial.update(trial)
            
            all_trials.append(enriched_trial)
    
    # Save the CSV file
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'wb') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_trials)
        
        print("Successfully generated %d trials" % len(all_trials))
        print("Saved to: %s" % output_path)
        return True
        
    except Exception as e:
        print("Error saving CSV file: %s" % e)
        return False

## Example generation removed.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a single experimental session CSV (launcher mode only)")
    parser.add_argument('--session-type', required=True, help='Session type identifier')
    parser.add_argument('--output-path', required=True, help='Destination CSV path')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')

    args = parser.parse_args()

    print("="*80)
    print("SINGLE SESSION CSV GENERATOR (SIMPLIFIED MODE)")
    print("="*80)
    success = generate_single_session_csv(
        session_type=args.session_type,
        output_path=args.output_path,
        seed=args.seed
    )
    sys.exit(0 if success else 1)
