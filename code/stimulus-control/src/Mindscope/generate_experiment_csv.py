#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experimental Session CSV Generator for Visual Mismatch Paradigms

This script generates CSV files for visual mismatch paradigms in mice, organized into
separate folders with multiple variants per session type.

Usage:
    python generate_experiment_csv.py  # Generate all session folders with 10 variants each
    python generate_experiment_csv.py --session-type sensorimotor_mismatch --output-path /path/to/file.csv --seed 12345

This generates 6 session folders, each with 10 variants:
1. Visual Mismatch (Standard oddball)
2. Sensory-Motor Mismatch (Motor coupling)  
3. Sequence Mismatch (Sequential learning)
4. Duration Mismatch (Temporal oddball)
5. Sequence No-Oddball (long blocks without oddballs)
6. Sensory-Motor No-Oddball (long blocks without oddballs)

Each session includes appropriate control blocks and RF mapping.
"""

import csv
from pathlib import Path
import random
import numpy as np
import math
import os
import argparse
import sys

# Standard column order for all CSV files
STANDARD_FIELDNAMES = [
    'Contrast', 'Delay', 'Diameter', 'Duration', 'Orientation', 
    'Spatial_Frequency', 'Temporal_Frequency', 'X', 'Y', 
    'Phase', 'Trial_Type', 'Block_Type'
]

# Default stimulus size
DEFAULT_STIMULUS_SIZE = 360  # degrees (full field)

# Default parameters for standard trials
DEFAULT_PARAMS = {
    'Contrast': 1,
    'Delay': 0.343,
    'Diameter': DEFAULT_STIMULUS_SIZE,  # Full field stimulus
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
    'Diameter': DEFAULT_STIMULUS_SIZE,  # Full field stimulus
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
    'motor_halt': {'Temporal_Frequency': 0, 'Delay': 0, 'Trial_Type': 'halt'},
    'motor_omission': {'Contrast': 0, 'Delay': 0, 'Trial_Type': 'omission'},
    'motor_orientation_45': {'Orientation': 45, 'Delay': 0, 'Trial_Type': 'orientation_45'},
    'motor_orientation_90': {'Orientation': 90, 'Delay': 0, 'Trial_Type': 'orientation_90'}
}

def generate_rf_mapping_positions():
    """
    Generate (X, Y) positions for a 9x9 RF mapping grid.
    Grid spans from -40 to +40 degrees in 10-degree steps.
    
    Returns:
        List of (x, y) tuples for RF mapping positions.
    """
    positions = []
    for x in range(-40, 50, 10):  # -40 to +40 in 10° steps (9 positions)
        for y in range(-40, 50, 10):  # -40 to +40 in 10° steps (9 positions)
            positions.append((x, y))
    return positions

def main_single_csv():
    """Main function for generating separate CSV files for each session type."""
    
    print("Generating session folders with multiple variants...")
    print()

    # Generate 10 variants for each session type in separate folders
    session_files = generate_separate_session_csvs(n_variants=10)
    
    print("\nSuccess! Generated session folders with variants:")
    print("\nEach session type has its own folder with 10 variants:")
    print("- visual_mismatch/")
    print("- sensorimotor_mismatch/") 
    print("- sequence_mismatch/")
    print("- duration_mismatch/")
    print("- sequence_mismatch_no_oddball/")
    print("- sensorimotor_mismatch_no_oddball/")
    print("\nEach folder contains variant_01.csv through variant_10.csv")
    print("Load the appropriate CSV file in Bonsai for your experiment.")

def generate_separate_session_csvs(n_variants=10):
    """
    Generate separate CSV files for each session type matching the experimental diagram.
    
    Each session has the same control block structure but different mismatch blocks:
    1. Visual Mismatch Session (visual_mismatch_session.csv)
    2. Sensory-Motor Mismatch Session (sensorimotor_mismatch_session.csv)  
    3. Sequence Mismatch Session (sequence_mismatch_session.csv)
    4. Duration Mismatch Session (duration_mismatch_session.csv)
    5. Sequence No-Oddball Session (sequence_mismatch_no_oddball_session.csv)
    6. Sensory-Motor No-Oddball Session (sensorimotor_mismatch_no_oddball_session.csv)
    
    Args:
        n_variants: Number of session variants to generate (default 1)
    
    Returns:
        Dictionary mapping session type to generated file path
    """
    
    print("="*80)
    print("GENERATING SEPARATE SESSION CSV FILES")
    print("="*80)
    print()
    print("Creating 6 separate CSV files, one for each experimental session:")
    print("1. Visual Mismatch (Standard oddball)")
    print("2. Sensory-Motor Mismatch (Motor coupling)")  
    print("3. Sequence Mismatch (Sequential learning)")
    print("4. Duration Mismatch (Temporal oddball)")
    print("5. Sequence No-Oddball (Long sequential blocks)")
    print("6. Sensory-Motor No-Oddball (Long motor blocks)")
    print()
    
    # Standard fieldnames - no session metadata needed since each file is one session
    fieldnames = [
        'Block_Number', 'Block_Label', 'Block_Duration_Minutes',
        'Trial_Number', 'Sequence_Number', 'Trial_In_Sequence',
    ] + STANDARD_FIELDNAMES
    
    # Session configurations matching the diagram
    session_configs = {
        'visual_mismatch': {
            'folder': 'visual_mismatch',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'standard_oddball', 'duration_minutes': 26, 'label': 'Standard mismatch block', 
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        
        'sensorimotor_mismatch': {
            'folder': 'sensorimotor_mismatch',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'motor_oddball', 'duration_minutes': 26, 'label': 'Sensory-motor mismatch block',
                 'oddball_config': {'motor_orientation_45': 1.35, 'motor_orientation_90': 1.35, 'motor_halt': 1.35, 'motor_omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        
        'sequence_mismatch': {
            'folder': 'sequence_mismatch',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'sequential_oddball', 'duration_minutes': 26, 'label': 'Sequence mismatch block',
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        
        'duration_mismatch': {
            'folder': 'duration_mismatch',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'jitter_oddball', 'duration_minutes': 26, 'label': 'Duration mismatch block',
                 'oddball_config': {'jitter_150': 1.35, 'jitter_350': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        
        # No-oddball versions (long blocks without oddballs, all other blocks preserved)
        'sequence_mismatch_no_oddball': {
            'folder': 'sequence_mismatch_no_oddball',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'sequential_long', 'duration_minutes': 26, 'label': 'Sequence long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        
        'sensorimotor_mismatch_no_oddball': {
            'folder': 'sensorimotor_mismatch_no_oddball',
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'motor_long', 'duration_minutes': 26, 'label': 'Sensory-motor long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        }
    }
    
    session_files = {}
    
    # Generate each session separately
    for session_variant in range(n_variants):
        print("Generating session variant %d/%d" % (session_variant + 1, n_variants))
        
        for session_type, session_config in session_configs.items():
            print("  Processing %s session..." % session_type)
            
            all_trials = []
            trial_counter = 0
            
            # Generate each block in the session
            for block_number, block_config in enumerate(session_config['blocks'], 1):
                block_type = block_config['type']
                duration_minutes = block_config['duration_minutes']
                block_label = block_config['label']
                oddball_config = block_config.get('oddball_config', None)
                
                print("    Block %d: %s (%.1f min)" % (block_number, block_label, duration_minutes))
                
                # Generate trials for this block
                block_trials = generate_block_trials(
                    block_type=block_type,
                    duration_minutes=duration_minutes,
                    oddball_config=oddball_config,
                    variant=session_variant
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
                    
                    # Add metadata (no session info since each file is one session)
                    enriched_trial = {
                        'Block_Number': block_number,
                        'Block_Label': block_label,
                        'Block_Duration_Minutes': duration_minutes,
                        'Trial_Number': trial_counter,
                        'Sequence_Number': sequence_counter,
                        'Trial_In_Sequence': trial_in_sequence,
                        **trial  # Add all the stimulus parameters
                    }
                    
                    all_trials.append(enriched_trial)
            
            # Save this session's CSV in the appropriate folder with variant naming
            session_folder = session_config['folder']
            folder_path = Path(session_folder)
            folder_path.mkdir(exist_ok=True)
            
            variant_filename = "variant_%02d.csv" % (session_variant + 1)
            filepath = folder_path / variant_filename
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_trials)
            
            session_files["%s_variant_%02d" % (session_type, session_variant + 1)] = str(filepath)
            
            # Print session summary
            print("    Generated %d trials -> %s" % (len(all_trials), filepath))
    
    # Print overall summary
    print()
    print("="*80)
    print("SESSION CSV GENERATION COMPLETE")
    print("="*80)
    print()
    print("Generated session folders and variants:")
    
    # Group files by session type for display
    session_folders = {}
    for key, filepath in session_files.items():
        session_type = key.split('_variant_')[0]
        if session_type not in session_folders:
            session_folders[session_type] = []
        session_folders[session_type].append(filepath)
    
    for session_type, filepaths in session_folders.items():
        folder_name = session_configs[session_type]['folder']
        print("  %s/  (%d variants)" % (folder_name, len(filepaths)))
        for filepath in sorted(filepaths):
            variant_name = Path(filepath).name
            print("    %s" % variant_name)
    
    print()
    print("Each CSV file contains one complete experimental session:")
    print("- 7 blocks total (Control 1.1 → Mismatch → Control 1.2 → Control 2 → Control 3 → Control 4 → RF mapping)")
    print("- Block structure matches the experimental diagram exactly")
    print("- Use Block_Number column to run blocks sequentially")
    print("- Use Sequence_Number for sequential block analysis")
    
    return session_files

def generate_block_trials(block_type, duration_minutes, oddball_config=None, variant=0):
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
                trial['Diameter'] = DEFAULT_STIMULUS_SIZE
                all_trials_pool.append(trial)
        
        # Add omission trials (same number of repeats)
        for _ in range(n_repeats):
            trial = DEFAULT_PARAMS.copy()
            trial['Contrast'] = 0
            trial['Trial_Type'] = 'omission'
            trial['Block_Type'] = 'standard_control'
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Add halt trials (same number of repeats)
        for _ in range(n_repeats):
            trial = DEFAULT_PARAMS.copy()
            trial['Temporal_Frequency'] = 0
            trial['Trial_Type'] = 'halt'
            trial['Block_Type'] = 'standard_control'
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
                trial['Diameter'] = DEFAULT_STIMULUS_SIZE
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'jitter_control'
                trials.append(trial)
    
    elif block_type == 'open_loop_prerecorded':
        # Open-loop pre-recorded sequence (Control block 4)
        # Simulates a pre-recorded sensory-motor sequence where visual stimuli change 
        # independently of wheel input, representing playback of a recorded session
        
        # Frame rate for temporal sampling
        frame_rate = 60
        total_frames = int(duration_seconds * frame_rate)
        frame_duration = 1.0 / frame_rate
        
        # Create a simulated pre-recorded sensory-motor sequence pattern
        # In sensory-motor paradigms, orientation stays constant (vertical)
        # and only phase varies based on recorded wheel movement
        
        # Simulate realistic wheel-driven phase changes over time
        
        for frame in range(total_frames):
            # Time-based phase evolution (simulating recorded wheel movement)
            time_seconds = frame / frame_rate
            
            # Orientation stays constant at vertical (0°) for sensory-motor paradigm
            # Only phase changes to simulate the pre-recorded wheel movement
            final_orientation = 0  # Always vertical for sensory-motor
            
            # Phase changes over time (simulating continuous motion from recorded wheel data)
            # This creates realistic wheel-driven motion patterns
            # Use multiple frequency components to simulate natural wheel movement
            base_phase = time_seconds * 120  # Base drift rate
            fine_motion = 30 * math.sin(time_seconds * 8)  # Higher frequency component
            micro_motion = 10 * math.sin(time_seconds * 25)  # Fine-scale motion
            simulated_phase = (base_phase + fine_motion + micro_motion) % 360
            
            trial = {
                'Contrast': 1,
                'Delay': 0,
                'Diameter': DEFAULT_STIMULUS_SIZE,
                'Duration': frame_duration,
                'Orientation': int(final_orientation),
                'Spatial_Frequency': 0.04,
                'Temporal_Frequency': 0,  # Static, phase controlled by prerecorded data
                'X': 0,
                'Y': 0,
                'Phase': int(simulated_phase),  # Prerecorded phase evolution
                'Trial_Type': 'prerecorded',
                'Block_Type': 'open_loop_prerecorded'
            }
            trials.append(trial)
    
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
                trial['Diameter'] = DEFAULT_STIMULUS_SIZE
                all_trials_pool.append(trial)
        
        # Add omission trials (70 repeats)
        for _ in range(n_repeats):
            trial = SEQUENTIAL_PARAMS.copy()
            trial['Contrast'] = 0
            trial['Trial_Type'] = 'omission'
            trial['Block_Type'] = 'sequential_control_block'
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
            all_trials_pool.append(trial)
        
        # Add halt trials (70 repeats)
        for _ in range(n_repeats):
            trial = SEQUENTIAL_PARAMS.copy()
            trial['Temporal_Frequency'] = 0
            trial['Trial_Type'] = 'halt'
            trial['Block_Type'] = 'sequential_control_block'
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
                trial['Diameter'] = DEFAULT_STIMULUS_SIZE
                trial['Block_Type'] = 'sequential_long'
                
                if trial_in_seq == 4:  # Last trial is omission
                    trial['Contrast'] = 0
                    trial['Trial_Type'] = 'omission'
                else:
                    trial['Orientation'] = standard_sequence[trial_in_seq]
                    trial['Trial_Type'] = 'standard'
                
                trials.append(trial)
    
    elif block_type == 'motor_long':
        # Long motor block without oddballs - just continuous closed-loop control
        frame_rate = 60
        total_frames = int(duration_seconds * frame_rate)
        frame_duration = 1.0 / frame_rate
        
        # Generate frame-by-frame trials with wheel-controlled phase
        for frame in range(total_frames):
            trial = {
                'Contrast': 1,
                'Delay': 0,
                'Diameter': DEFAULT_STIMULUS_SIZE,
                'Duration': frame_duration,
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
        n_repeats = 10  # 10 repeats (corrected from 5)
        
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
                        'Diameter': size,
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
    
    elif block_type in ['standard_oddball', 'jitter_oddball', 'sequential_oddball']:
        # Oddball blocks with specified mismatch rates
        trials = generate_oddball_block_trials(block_type, duration_minutes, oddball_config, variant)
    
    elif block_type in ['motor_oddball', 'motor_control']:
        # Motor blocks - frame-by-frame control
        trials = generate_motor_block_trials(block_type, duration_minutes, oddball_config, variant)
    
    # Shuffle trials (except for those which maintains structure)
    if block_type not in ['open_loop_prerecorded', 'sequential_oddball', 'sequential_long']:
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
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
                    trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
            trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
                    trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
            for orientation in sequence:
                trial = SEQUENTIAL_PARAMS.copy()
                trial['Diameter'] = DEFAULT_STIMULUS_SIZE
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
                    trial['Trial_Type'] = 'standard'
                
                trials.append(trial)
            
            # Add sequence-ending omission
            omission_trial = SEQUENTIAL_PARAMS.copy()
            omission_trial['Contrast'] = 0
            omission_trial['Trial_Type'] = 'omission'
            omission_trial['Block_Type'] = 'sequential_oddball'
            omission_trial['Diameter'] = DEFAULT_STIMULUS_SIZE
            trials.append(omission_trial)
    
    return trials

def generate_motor_block_trials(block_type, duration_minutes, oddball_config, variant):
    """Generate frame-by-frame trials for motor blocks."""
    random.seed(variant * 789 + hash(block_type))
    
    frame_rate = 60
    duration_seconds = duration_minutes * 60
    total_frames = int(duration_seconds * frame_rate)
    frame_duration = 1.0 / frame_rate
    
    trials = []
    
    if block_type == 'motor_control':
        # Pure closed-loop control - generate realistic wheel movement
        phase_values = []
        current_phase = 0.0
        velocity = 0.0
        
        for frame in range(total_frames):
            # Simple mouse wheel simulation
            if frame % 60 == 0:  # Update behavior every second
                velocity += random.gauss(0, 0.05)
                velocity *= 0.95  # friction
                velocity = max(-0.3, min(0.3, velocity))
            
            current_phase += velocity
            current_phase = current_phase % (2 * math.pi)
            phase_values.append(current_phase)
        
        for frame in range(total_frames):
            trial = {
                'Contrast': 1,
                'Delay': 0,
                'Diameter': DEFAULT_STIMULUS_SIZE,
                'Duration': frame_duration,
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
        min_interval_frames = 120  # 2 seconds minimum
        oddball_duration_frames = 21  # ~0.35 seconds
        
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
                    'Diameter': DEFAULT_STIMULUS_SIZE,
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
                # Normal frame
                trial = {
                    'Contrast': 1,
                    'Delay': 0,
                    'Diameter': DEFAULT_STIMULUS_SIZE,
                    'Duration': frame_duration,
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
        'visual_mismatch': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'standard_oddball', 'duration_minutes': 26, 'label': 'Standard mismatch block', 
                 'oddball_config': {'orientation_45': 1.35, 'orientation_90': 1.35, 'halt': 1.35, 'omission': 1.35}},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
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
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
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
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
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
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        'sequence_mismatch_no_oddball': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'sequential_long', 'duration_minutes': 26, 'label': 'Sequence long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        },
        'sensorimotor_mismatch_no_oddball': {
            'blocks': [
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.1'},
                {'type': 'motor_long', 'duration_minutes': 26, 'label': 'Sensory-motor long block (no oddball)'},
                {'type': 'standard_control', 'duration_minutes': 6.4, 'label': 'Control block 1.2'},
                {'type': 'sequential_control_block', 'duration_minutes': 4.7, 'label': 'Control block 2'},
                {'type': 'jitter_control', 'duration_minutes': 6.4, 'label': 'Control block 3'},
                {'type': 'open_loop_prerecorded', 'duration_minutes': 6.4, 'label': 'Control block 4'},
                {'type': 'rf_mapping', 'duration_minutes': 10, 'label': 'RF mapping'}
            ]
        }
    }
    
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
            variant=0  # Single variant for launcher mode
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
                **trial  # Add all the stimulus parameters
            }
            
            all_trials.append(enriched_trial)
    
    # Save the CSV file
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_trials)
        
        print("Successfully generated %d trials" % len(all_trials))
        print("Saved to: %s" % output_path)
        return True
        
    except Exception as e:
        print("Error saving CSV file: %s" % e)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate experimental session CSV files for visual mismatch paradigms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all session folders with 10 variants each (original mode)
  python generate_experiment_csv.py
  
  # Generate single session file for launcher (new mode)
  python generate_experiment_csv.py --session-type sensorimotor_mismatch --output-path /path/to/file.csv --seed 12345
  
Available session types:
  - visual_mismatch
  - sensorimotor_mismatch  
  - sequence_mismatch
  - duration_mismatch
  - sequence_mismatch_no_oddball
  - sensorimotor_mismatch_no_oddball
        """
    )
    
    parser.add_argument(
        '--session-type', 
        help='Type of session to generate (for single file mode)'
    )
    parser.add_argument(
        '--output-path',
        help='Output path for the CSV file (for single file mode)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility (for single file mode)'
    )
    
    args = parser.parse_args()
    
    if args.session_type and args.output_path:
        # Single session mode (for launcher integration)
        print("="*80)
        print("SINGLE SESSION CSV GENERATOR")
        print("="*80)
        success = generate_single_session_csv(
            session_type=args.session_type,
            output_path=args.output_path,
            seed=args.seed
        )
        sys.exit(0 if success else 1)
    else:
        # Original batch mode (generate all folders with variants)
        print("="*80)
        print("EXPERIMENTAL SESSION CSV GENERATOR")
        print("="*80)
        print()
        print("This script generates separate CSV files for each experimental session")
        print("matching the visual mismatch paradigm diagram:")
        print("1. Visual Mismatch Session")
        print("2. Sensory-Motor Mismatch Session")  
        print("3. Sequence Mismatch Session")
        print("4. Duration Mismatch Session")
        print("5. Sequence No-Oddball Session (long blocks without oddballs)")
        print("6. Sensory-Motor No-Oddball Session (long blocks without oddballs)")
        print()
        print("Each session has the same control block structure but different main blocks.")
        print()
        
        # Generate separate session CSV files
        main_single_csv()
