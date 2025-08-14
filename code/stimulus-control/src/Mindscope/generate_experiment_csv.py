#!/usr/bin/env python3
"""
Drifting Grating Experiment CSV Generator

This script generates a CSV file with parameters for a drifting grating experiment
for recordings in mice. It creates standard trials with default parameters
and allows adding oddball trials with modified parameters.

Usage:
    python generate_experiment_csv.py
"""

import csv
from pathlib import Path
import random

# Standard column order for all CSV files
STANDARD_FIELDNAMES = [
    'Contrast', 'Delay', 'Diameter', 'Duration', 'Orientation', 
    'Spatial_Frequency', 'Temporal_Frequency', 'X', 'Y', 
    'Phase', 'Trial_Type', 'Block_Type'
]

# Default parameters for standard trials
DEFAULT_PARAMS = {
    'Contrast': 1,
    'Delay': 0.343,
    'Diameter': 360,  # Standard oddball context
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
    'Diameter': 340,  # Sequential context
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

# Diameter markers for different contexts
DIAMETER_MARKERS = {
    'sequential_normal': 340,
    'sequential_oddball': 341,
    'jitter_normal': 350,
    'jitter_oddball': 351,
    'standard_normal': 360,
    'standard_oddball': 361,
    'standard_control': 370,  # For standard control (orientation tuning)
    'jitter_control': 380,   # For jitter control (duration tuning)
    'sequential_control': 390  # For sequential control (if needed)
}

def generate_experiment_csv(output_file, n_standard_trials, oddball_configs, context_type='standard'):
    """
    Generate experiment CSV with standard and oddball trials.
    
    Args:
        output_file: Path to output CSV file
        n_standard_trials: Number of standard trials
        oddball_configs: List of tuples (n_trials, modified_params_dict)
        context_type: Type of context ('standard', 'jitter', 'control')
    """
    trials = []
    
    # Set diameter markers and block type based on context
    if context_type == 'standard':
        normal_diameter = DIAMETER_MARKERS['standard_normal']
        oddball_diameter = DIAMETER_MARKERS['standard_oddball']
        block_type = 'standard_oddball'
    elif context_type == 'jitter':
        normal_diameter = DIAMETER_MARKERS['jitter_normal']
        oddball_diameter = DIAMETER_MARKERS['jitter_oddball']
        block_type = 'jitter_oddball'
    elif context_type == 'standard_control':
        normal_diameter = DIAMETER_MARKERS['standard_control']
        oddball_diameter = DIAMETER_MARKERS['standard_control']
        block_type = 'standard_control'
    elif context_type == 'jitter_control':
        normal_diameter = DIAMETER_MARKERS['jitter_control']
        oddball_diameter = DIAMETER_MARKERS['jitter_control']
        block_type = 'jitter_control'
    elif context_type == 'sequential_control':
        normal_diameter = DIAMETER_MARKERS['sequential_control']
        oddball_diameter = DIAMETER_MARKERS['sequential_control']
        block_type = 'sequential_control'
    else:  # Default case
        normal_diameter = 360
        oddball_diameter = 361
        block_type = 'standard_oddball'
    
    # Add standard trials
    for _ in range(n_standard_trials):
        trial = DEFAULT_PARAMS.copy()
        trial['Diameter'] = normal_diameter
        trial['Trial_Type'] = 'standard'
        trial['Block_Type'] = block_type
        trials.append(trial)
    
    # Add oddball trials
    for n_trials, modified_params in oddball_configs:
        oddball_params = DEFAULT_PARAMS.copy()
        oddball_params.update(modified_params)
        oddball_params['Diameter'] = oddball_diameter
        oddball_params['Block_Type'] = block_type
        
        # Determine trial type based on modified parameters
        if 'Duration' in modified_params and modified_params.get('Contrast', 1) > 0:
            trial_type = 'jitter'
        elif modified_params.get('Contrast', 1) == 0:
            trial_type = 'omission'
        elif modified_params.get('Temporal_Frequency', 2) == 0:
            trial_type = 'halt'
        elif modified_params.get('Orientation', 0) == 45:
            trial_type = 'orientation_45'
        elif modified_params.get('Orientation', 0) == 90:
            trial_type = 'orientation_90'
        elif 'Orientation' in modified_params and context_type in ['standard_control', 'jitter_control', 'sequential_control']:
            trial_type = 'single'
        else:
            trial_type = 'standard'
        
        oddball_params['Trial_Type'] = trial_type
        
        for _ in range(n_trials):
            trials.append(oddball_params.copy())
            trials.append(oddball_params.copy())
    
    # Save to CSV
    filepath = Path(output_file)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        
        writer.writeheader()
        for trial in trials:
            writer.writerow(trial)
    
    print(f"Generated {len(trials)} trials:")
    print(f"  - {n_standard_trials} standard trials (diameter: {normal_diameter})")
    for n_trials, params in oddball_configs:
        print(f"  - {n_trials} oddball trials with: {params} (diameter: {oddball_diameter})")
    print(f"Saved to: {output_file}")


def generate_standard_oddball_variants(n_variants=10):
    """Generate multiple shuffled variants of standard oddball experiment."""
    print("=== Generating Standard Oddball Variants ===")
    
    # Standard oddball configuration
    n_standard_trials = 1000
    oddball_configs = [
        (10, {'Orientation': 45}),   # 45 degrees
        (10, {'Orientation': 90}),   # 90 degrees  
        (10, {'Spatial_Frequency': 0}),  # Spatial frequency 0 (halt)
        (10, {'Contrast': 0})        # Contrast 0 (omission)
    ]
    
    for variant in range(n_variants):
        print(f"Generating standard oddball variant {variant + 1}/{n_variants}")
        
        # Generate trials
        trials = []
        
        # Add standard trials
        for _ in range(n_standard_trials):
            trial = DEFAULT_PARAMS.copy()
            trial['Diameter'] = DIAMETER_MARKERS['standard_normal']
            trials.append(trial)
        
        # Add oddball trials
        for n_trials, modified_params in oddball_configs:
            oddball_params = DEFAULT_PARAMS.copy()
            oddball_params.update(modified_params)
            oddball_params['Diameter'] = DIAMETER_MARKERS['standard_oddball']
            
            for _ in range(n_trials):
                trials.append(oddball_params.copy())
        
        # Shuffle trials for this variant
        import random
        random.seed(variant * 123)  # Different seed than sequential
        random.shuffle(trials)
        
        # Save to CSV
        output_file = f"blocks/standard/standard_oddball_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = list(DEFAULT_PARAMS.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for trial in trials:
                writer.writerow(trial)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated {n_variants} standard oddball variants")
    print(f"Each variant contains {n_standard_trials} standard + {sum(n for n, _ in oddball_configs)} oddball trials")


def generate_jitter_variants(n_variants=10):
    """Generate multiple shuffled variants of jitter experiment."""
    print("=== Generating Jitter Variants ===")
    
    # Jitter configuration
    n_standard_trials = 1000
    oddball_configs = [
        (10, {'Duration': 0.050}),   # 50ms duration
        (10, {'Duration': 0.100}),   # 100ms duration
        (10, {'Duration': 0.200}),   # 200ms duration
        (10, {'Contrast': 0})        # Contrast 0 (omission)
    ]
    
    for variant in range(n_variants):
        print(f"Generating jitter variant {variant + 1}/{n_variants}")
        
        # Generate trials
        trials = []
        
        # Add standard trials
        for _ in range(n_standard_trials):
            trial = DEFAULT_PARAMS.copy()
            trial['Diameter'] = DIAMETER_MARKERS['jitter_normal']
            trials.append(trial)
        
        # Add oddball trials
        for n_trials, modified_params in oddball_configs:
            oddball_params = DEFAULT_PARAMS.copy()
            oddball_params.update(modified_params)
            oddball_params['Diameter'] = DIAMETER_MARKERS['jitter_oddball']
            
            for _ in range(n_trials):
                trials.append(oddball_params.copy())
        
        # Shuffle trials for this variant
        import random
        random.seed(variant * 456)  # Different seed than sequential and standard
        random.shuffle(trials)
        
        # Save to CSV
        output_file = f"blocks/jitter/jitter_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = list(DEFAULT_PARAMS.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for trial in trials:
                writer.writerow(trial)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated {n_variants} jitter variants")
    print(f"Each variant contains {n_standard_trials} standard + {sum(n for n, _ in oddball_configs)} oddball trials")


def generate_standard_oddball_csv():
    """Generate standard oddball experiment CSV."""
    print("=== Generating Standard Oddball Experiment ===")
    
    # Standard oddball configuration
    n_standard_trials = 1000
    oddball_configs = [
        (10, {'Orientation': 45}),   # 45 degrees
        (10, {'Orientation': 90}),   # 90 degrees  
        (10, {'Spatial_Frequency': 0}),  # Spatial frequency 0 (halt)
        (10, {'Contrast': 0})        # Contrast 0 (omission)
    ]
    
    generate_experiment_csv("blocks/standard/standard_oddball.csv", n_standard_trials, oddball_configs, 'standard')


def generate_jitter_csv():
    """Generate jitter experiment CSV."""
    print("=== Generating Jitter Experiment ===")
    
    # Jitter configuration
    n_standard_trials = 1000
    oddball_configs = [
        (10, {'Duration': 0.050}),   # 50ms duration
        (10, {'Duration': 0.100}),   # 100ms duration
        (10, {'Duration': 0.200}),   # 200ms duration
        (10, {'Contrast': 0})        # Contrast 0 (omission)
    ]
    
    generate_experiment_csv("blocks/jitter/jitter.csv", n_standard_trials, oddball_configs, 'jitter')


def generate_standard_control_csv():
    """Generate standard control CSV variants (orientation tuning)."""
    print("=== Generating Standard Control (Orientation Tuning) Variants ===")
    
    # Generate orientations from 0 to 360 degrees
    n_control_per_orientation = 10
    orientations = list(range(0, 360, 15))  # Every 15 degrees: 0, 15, 30, ..., 345
    
    for variant in range(10):
        print(f"Generating standard control variant {variant + 1}/10")
        
        trials = []
        
        # Add orientation trials
        for orientation in orientations:
            for _ in range(n_control_per_orientation):
                trial = DEFAULT_PARAMS.copy()
                trial['Orientation'] = orientation
                trial['Diameter'] = DIAMETER_MARKERS['standard_control']
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'standard_control'
                trials.append(trial)
        
        # Shuffle trials for this variant
        import random
        random.seed(variant * 101)  # Different seed for control variants
        random.shuffle(trials)
        
        # Save to CSV
        output_file = f"blocks/standard/standard_control_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            writer.writeheader()
            writer.writerows(trials)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated 10 standard control variants")
    print(f"Each variant contains {len(orientations)} orientations × {n_control_per_orientation} trials each = {len(orientations) * n_control_per_orientation} orientation trials")


def generate_jitter_control_csv():
    """Generate jitter control CSV variants (duration tuning)."""
    print("=== Generating Jitter Control (Duration Tuning) Variants ===")
    
    # All durations presented equally
    n_control_per_duration = 50
    durations = [0.050, 0.100, 0.200, 0.343]  # Including the default duration
    
    for variant in range(10):
        print(f"Generating jitter control variant {variant + 1}/10")
        
        trials = []
        
        # Add duration trials
        for duration in durations:
            for _ in range(n_control_per_duration):
                trial = DEFAULT_PARAMS.copy()
                trial['Duration'] = duration
                trial['Diameter'] = DIAMETER_MARKERS['jitter_control']
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'jitter_control'
                trials.append(trial)
        
        # Shuffle trials for this variant
        import random
        random.seed(variant * 102)  # Different seed for jitter control variants
        random.shuffle(trials)
        
        # Save to CSV
        output_file = f"blocks/jitter/jitter_control_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            writer.writeheader()
            writer.writerows(trials)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated 10 jitter control variants")
    print(f"Each variant contains {len(durations)} durations × {n_control_per_duration} trials each = {len(durations) * n_control_per_duration} duration trials")


def generate_sequential_csv(n_normal_sequences, n_oddball_45, n_oddball_90, n_oddball_halt, n_oddball_omission, shuffle_variant=0):
    """
    Generate sequential experiment CSV with sequences of 4 gratings + omission.
    
    Args:
        n_normal_sequences: Number of normal sequences (90°, 45°, 0°, 45°)
        n_oddball_45: Number of sequences with 45° replacing 3rd grating
        n_oddball_90: Number of sequences with 90° replacing 3rd grating  
        n_oddball_halt: Number of sequences with halt replacing 3rd grating
        n_oddball_omission: Number of sequences with omission replacing 3rd grating
        shuffle_variant: Variant number for shuffling (0-9)
    """
    import random
    
    # Standard sequence: 90°, 45°, 0°, 45°, omission
    standard_sequence = [90, 45, 0, 45]
    
    # Create list of all sequences to generate
    sequence_types = []
    
    # Add normal sequences
    for _ in range(n_normal_sequences):
        sequence_types.append(('normal', standard_sequence))
    
    # Add oddball sequences
    for _ in range(n_oddball_45):
        oddball_seq = [90, 45, 45, 45]  # Replace 3rd grating with 45°
        sequence_types.append(('oddball_45', oddball_seq))
    
    for _ in range(n_oddball_90):
        oddball_seq = [90, 45, 90, 45]  # Replace 3rd grating with 90°
        sequence_types.append(('oddball_90', oddball_seq))
    
    for _ in range(n_oddball_halt):
        oddball_seq = [90, 45, -1, 45]  # Replace 3rd grating with halt
        sequence_types.append(('oddball_halt', oddball_seq))
    
    for _ in range(n_oddball_omission):
        oddball_seq = [90, 45, -2, 45]  # Replace 3rd grating with omission
        sequence_types.append(('oddball_omission', oddball_seq))
    
    # Shuffle the sequence order for this variant
    random.seed(shuffle_variant * 42)
    random.shuffle(sequence_types)
    
    trials = []
    
    for seq_type, sequence in sequence_types:
        # Determine if this is a normal or oddball sequence
        is_oddball = seq_type != 'normal'
        
        # Add the 4 gratings
        for orientation in sequence:
            trial = SEQUENTIAL_PARAMS.copy()
            
            # Set diameter marker based on sequence type
            if is_oddball:
                trial['Diameter'] = DIAMETER_MARKERS['sequential_oddball']
            else:
                trial['Diameter'] = DIAMETER_MARKERS['sequential_normal']
            
            # Set trial type and block type
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
                if is_oddball:
                    if orientation == 45:
                        trial['Trial_Type'] = 'orientation_45'
                    elif orientation == 90:
                        trial['Trial_Type'] = 'orientation_90'
                    else:
                        trial['Trial_Type'] = 'standard'
                else:
                    trial['Trial_Type'] = 'standard'
            
            trials.append(trial)
        
        # Add the omission (5th trial in sequence)
        omission_trial = SEQUENTIAL_PARAMS.copy()
        omission_trial['Contrast'] = 0
        omission_trial['Trial_Type'] = 'omission'
        omission_trial['Block_Type'] = 'sequential_oddball'
        # Set diameter marker for omission trial
        if is_oddball:
            omission_trial['Diameter'] = DIAMETER_MARKERS['sequential_oddball']
        else:
            omission_trial['Diameter'] = DIAMETER_MARKERS['sequential_normal']
        trials.append(omission_trial)
    
    return trials


def generate_all_sequential_variants(n_normal_sequences=80, n_oddball_45=5, n_oddball_90=5, n_oddball_halt=5, n_oddball_omission=5, n_variants=10):
    """Generate all sequential experiment variants."""
    print("=== Generating Sequential Experiments ===")
    
    total_sequences = n_normal_sequences + n_oddball_45 + n_oddball_90 + n_oddball_halt + n_oddball_omission
    print(f"Each variant will have {total_sequences} sequences:")
    print(f"  - {n_normal_sequences} normal sequences")
    print(f"  - {n_oddball_45} oddball sequences (45° replacing 3rd grating)")
    print(f"  - {n_oddball_90} oddball sequences (90° replacing 3rd grating)")
    print(f"  - {n_oddball_halt} oddball sequences (halt replacing 3rd grating)")
    print(f"  - {n_oddball_omission} oddball sequences (omission replacing 3rd grating)")
    print()
    
    for variant in range(n_variants):
        print(f"Generating sequential variant {variant + 1}/{n_variants}")
        
        trials = generate_sequential_csv(n_normal_sequences, n_oddball_45, n_oddball_90, 
                                       n_oddball_halt, n_oddball_omission, shuffle_variant=variant)
        
        # Save to CSV
        output_file = f"blocks/sequentials/sequential_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            
            writer.writeheader()
            for trial in trials:
                writer.writerow(trial)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated {n_variants} sequential variants")
    print(f"Each variant contains {total_sequences} sequences (5 trials each = {total_sequences * 5} total trials)")


def generate_sequential_control_csv():
    """Generate sequential control CSV variants (orientation tuning with sequential parameters)."""
    print("=== Generating Sequential Control (Orientation Tuning) Variants ===")
    
    # Generate orientations from 0 to 360 degrees with sequential parameters
    n_control_per_orientation = 10
    orientations = list(range(0, 360, 15))  # Every 15 degrees: 0, 15, 30, ..., 345
    
    for variant in range(10):
        print(f"Generating sequential control variant {variant + 1}/10")
        
        trials = []
        
        # Add orientation trials with sequential parameters
        for orientation in orientations:
            for _ in range(n_control_per_orientation):
                trial = SEQUENTIAL_PARAMS.copy()
                trial['Orientation'] = orientation
                trial['Diameter'] = DIAMETER_MARKERS['sequential_control']
                trial['Trial_Type'] = 'single'
                trial['Block_Type'] = 'sequential_control'
                trials.append(trial)
        
        # Add omission trials (same number as one orientation)
        for _ in range(n_control_per_orientation):
            omission_trial = SEQUENTIAL_PARAMS.copy()
            omission_trial['Contrast'] = 0
            omission_trial['Diameter'] = DIAMETER_MARKERS['sequential_control']
            omission_trial['Trial_Type'] = 'omission'
            omission_trial['Block_Type'] = 'sequential_control'
            trials.append(omission_trial)
        
        # Shuffle trials for this variant
        import random
        random.seed(variant * 103)  # Different seed for sequential control variants
        random.shuffle(trials)
        
        # Save to CSV
        output_file = f"blocks/sequentials/sequential_control_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            writer.writeheader()
            writer.writerows(trials)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated 10 sequential control variants")
    print(f"Each variant contains {len(orientations)} orientations × {n_control_per_orientation} trials + {n_control_per_orientation} omission trials = {len(orientations) * n_control_per_orientation + n_control_per_orientation} total trials")


def generate_motor_oddball_csv(duration_seconds=600, frame_rate=60, n_oddball_per_type=20, min_interval_seconds=2.0, n_variants=10):
    """
    Generate motor oddball CSV files with frame-by-frame control information.
    
    Args:
        duration_seconds: Total duration of the stimulus in seconds
        frame_rate: Frame rate in Hz
        n_oddball_per_type: Number of oddballs per type
        min_interval_seconds: Minimum interval between oddballs in seconds
        n_variants: Number of shuffled variants to generate
    """
    print("=== Generating Motor Oddball Variants ===")
    
    total_frames = int(duration_seconds * frame_rate)
    min_interval_frames = int(min_interval_seconds * frame_rate)
    oddball_duration_frames = int(0.343 * frame_rate)  # 0.343s in frames
    frame_duration = 1.0 / frame_rate  # Duration per frame
    
    # Oddball types with their parameters (motor oddball uses delay=0 and halt uses temporal_frequency=0)
    oddball_types = [
        {'name': 'halt', 'Orientation': 0, 'Spatial_Frequency': 0.04, 'Temporal_Frequency': 0, 'Contrast': 1, 'Delay': 0, 'Diameter': 361, 'Phase': 'fixed'},
        {'name': 'omission', 'Orientation': 0, 'Spatial_Frequency': 0.04, 'Temporal_Frequency': 2, 'Contrast': 0, 'Delay': 0, 'Diameter': 361, 'Phase': 0},
        {'name': 'orientation_45', 'Orientation': 45, 'Spatial_Frequency': 0.04, 'Temporal_Frequency': 2, 'Contrast': 1, 'Delay': 0, 'Diameter': 361, 'Phase': 0},
        {'name': 'orientation_90', 'Orientation': 90, 'Spatial_Frequency': 0.04, 'Temporal_Frequency': 2, 'Contrast': 1, 'Delay': 0, 'Diameter': 361, 'Phase': 0}
    ]
    
    # Default parameters for normal frames (controlled by wheel)
    default_params = {
        'Orientation': 0,
        'Spatial_Frequency': 0.04,
        'Temporal_Frequency': 0,  # Set to 0 for normal frames
        'Contrast': 1,
        'Delay': 0,
        'Diameter': 360,  # Normal frame marker
        'X': 0,
        'Y': 0,
        'Phase': 'wheel',
        'Trial_Type': 'standard',
        'Block_Type': 'motor_oddball'
    }
    
    total_oddballs = n_oddball_per_type * len(oddball_types)
    
    print(f"Motor oddball parameters:")
    print(f"  - Duration: {duration_seconds}s ({total_frames} frames)")
    print(f"  - Frame rate: {frame_rate} Hz")
    print(f"  - {n_oddball_per_type} oddballs per type × {len(oddball_types)} types = {total_oddballs} total oddballs")
    print(f"  - Minimum interval: {min_interval_seconds}s ({min_interval_frames} frames)")
    print(f"  - Oddball duration: {0.343}s ({oddball_duration_frames} frames)")
    print()
    
    for variant in range(n_variants):
        print(f"Generating motor oddball variant {variant + 1}/{n_variants}")
        
        import random
        random.seed(variant * 789)  # Different seed for motor oddballs
        
        # Generate list of possible frame numbers (avoiding edges)
        edge_buffer_frames = int(5 * frame_rate)  # 5 second buffer from start/end
        possible_frames = list(range(edge_buffer_frames, total_frames - edge_buffer_frames))
        
        # Shuffle possible frames
        random.shuffle(possible_frames)
        
        # Select frames ensuring minimum interval
        selected_frames = []
        for frame in possible_frames:
            # Check if this frame is far enough from all previously selected frames
            if all(abs(frame - selected) >= min_interval_frames for selected in selected_frames):
                selected_frames.append(frame)
                if len(selected_frames) >= total_oddballs:
                    break
        
        if len(selected_frames) < total_oddballs:
            print(f"  Warning: Could only fit {len(selected_frames)} oddballs instead of {total_oddballs}")
        
        # Sort selected frames
        selected_frames.sort()
        
        # Create a shuffled list of oddball types
        oddball_type_list = []
        for oddball_type in oddball_types:
            for _ in range(n_oddball_per_type):
                oddball_type_list.append(oddball_type)
        
        # Shuffle the oddball types to interleave them
        random.shuffle(oddball_type_list)
        
        # Create a set of oddball start frames for easy lookup
        oddball_start_frames = set()
        oddball_frame_map = {}
        for i, oddball_type in enumerate(oddball_type_list):
            if i < len(selected_frames):
                start_frame = selected_frames[i]
                oddball_start_frames.add(start_frame)
                oddball_frame_map[start_frame] = oddball_type
        
        # Generate frame-by-frame data
        all_frames = []
        frame_num = 0
        
        while frame_num < total_frames:
            if frame_num in oddball_start_frames:
                # This is an oddball start frame - add single row for entire oddball
                oddball_type = oddball_frame_map[frame_num]
                frame_data = {
                    'Contrast': oddball_type['Contrast'],
                    'Delay': oddball_type['Delay'],
                    'Diameter': oddball_type['Diameter'],
                    'Duration': 0.343,  # Oddball duration
                    'Orientation': oddball_type['Orientation'],
                    'Spatial_Frequency': oddball_type['Spatial_Frequency'],
                    'Temporal_Frequency': oddball_type['Temporal_Frequency'],
                    'X': oddball_type.get('X', 0),
                    'Y': oddball_type.get('Y', 0),
                    'Phase': oddball_type['Phase'],
                    'Trial_Type': oddball_type['name'],
                    'Block_Type': 'motor_oddball'
                }
                all_frames.append(frame_data)
                
                # Skip ahead by the oddball duration
                frame_num += oddball_duration_frames
            else:
                # This is a normal frame (controlled by wheel)
                frame_data = {
                    'Contrast': default_params['Contrast'],
                    'Delay': default_params['Delay'],
                    'Diameter': default_params['Diameter'],
                    'Duration': frame_duration,  # Single frame duration
                    'Orientation': default_params['Orientation'],
                    'Spatial_Frequency': default_params['Spatial_Frequency'],
                    'Temporal_Frequency': default_params['Temporal_Frequency'],
                    'X': default_params['X'],
                    'Y': default_params['Y'],
                    'Phase': default_params['Phase'],
                    'Trial_Type': default_params['Trial_Type'],
                    'Block_Type': default_params['Block_Type']
                }
                all_frames.append(frame_data)
                frame_num += 1
        
        # Save to CSV
        output_file = f"blocks/motor/motor_oddball_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            
            writer.writeheader()
            for frame in all_frames:
                writer.writerow(frame)
        
        print(f"  Saved {len(all_frames)} frames to {output_file}")
        
        # Count trial types from all frames
        type_counts = {}
        for frame in all_frames:
            trial_type = frame['Trial_Type']
            type_counts[trial_type] = type_counts.get(trial_type, 0) + 1
        
        print(f"    Trial type counts: {type_counts}")
    
    print(f"\nGenerated {n_variants} motor oddball variants")
    print(f"Each variant contains frame-by-frame control data over {duration_seconds}s duration")


def generate_motor_control_csv(duration_seconds=600, frame_rate=60, n_variants=10):
    """
    Generate motor control CSV files that simulate a mouse moving and providing a phase.
    Each variant simulates a different mouse behavior pattern with realistic wheel movement.
    
    Args:
        duration_seconds: Total duration of the stimulus in seconds
        frame_rate: Frame rate in Hz
        n_variants: Number of variants to generate
    """
    print("=== Generating Motor Control Variants ===")
    
    import numpy as np
    import random
    
    total_frames = int(duration_seconds * frame_rate)
    frame_duration = 1.0 / frame_rate  # Duration per frame
    
    # Default parameters for motor control (controlled by wheel movement)
    default_params = {
        'Contrast': 1,
        'Delay': 0,
        'Diameter': 370,  # Motor control marker
        'Duration': frame_duration,
        'Orientation': 0,
        'Spatial_Frequency': 0.04,
        'Temporal_Frequency': 0,  # Set to 0 for wheel-controlled
        'X': 0,
        'Y': 0,
        'Phase': 0,  # Will be updated with realistic values
        'Trial_Type': 'standard',
        'Block_Type': 'motor_control'
    }
    
    print(f"Motor control parameters:")
    print(f"  - Duration: {duration_seconds}s ({total_frames} frames)")
    print(f"  - Frame rate: {frame_rate} Hz")
    print(f"  - Phase simulates recorded mouse wheel movement")
    print(f"  - Continuous drifting grating stimulus")
    print()
    
    for variant in range(n_variants):
        print(f"Generating motor control variant {variant + 1}/{n_variants}")
        
        # Set random seed for reproducible mouse behavior per variant
        random.seed(variant * 42)
        np.random.seed(variant * 42)
        
        # Generate realistic mouse wheel movement pattern
        phase_values = generate_mouse_wheel_behavior(total_frames, variant)
        
        # Generate frame-by-frame data
        all_frames = []
        
        for frame_num in range(total_frames):
            frame_data = default_params.copy()
            frame_data['Phase'] = phase_values[frame_num]
            all_frames.append(frame_data)
        
        # Save to CSV
        output_file = f"blocks/motor/motor_control_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            
            writer.writeheader()
            for frame in all_frames:
                writer.writerow(frame)
        
        print(f"  Saved {len(all_frames)} frames to {output_file}")
        
        # Print phase statistics for this variant
        phase_range = max(phase_values) - min(phase_values)
        avg_speed = abs(np.diff(phase_values)).mean() * frame_rate  # degrees per second
        print(f"    Phase range: {min(phase_values):.2f}° to {max(phase_values):.2f}° (total: {phase_range:.2f}°)")
        print(f"    Average speed: {avg_speed:.2f}°/sec")
    
    print(f"\nGenerated {n_variants} motor control variants")
    print(f"Each variant contains frame-by-frame control data over {duration_seconds}s duration")
    print(f"Phase values simulate realistic mouse wheel movement patterns")


def generate_mouse_wheel_behavior(total_frames, variant_seed):
    """
    Generate realistic mouse wheel movement patterns with bidirectional rotation.
    Each pattern simulates different mouse behaviors (active, moderate, slow, mixed).
    
    Args:
        total_frames: Total number of frames to generate
        variant_seed: Seed for variant-specific behavior patterns
    
    Returns:
        List of phase values in radians (0 to 2π, wrapping around)
    """
    import numpy as np
    import random
    import math
    
    # Set seed for reproducible behavior
    random.seed(variant_seed)
    np.random.seed(variant_seed)
    
    # Define different mouse behavior patterns
    behavior_patterns = [
        {'name': 'active_runner', 'base_speed': 0.15, 'variability': 0.8, 'pause_prob': 0.02, 'reverse_prob': 0.05},
        {'name': 'moderate_walker', 'base_speed': 0.08, 'variability': 0.6, 'pause_prob': 0.05, 'reverse_prob': 0.08},
        {'name': 'slow_explorer', 'base_speed': 0.04, 'variability': 0.4, 'pause_prob': 0.08, 'reverse_prob': 0.12},
        {'name': 'burst_runner', 'base_speed': 0.12, 'variability': 1.2, 'pause_prob': 0.03, 'reverse_prob': 0.06},
        {'name': 'intermittent_walker', 'base_speed': 0.06, 'variability': 0.9, 'pause_prob': 0.10, 'reverse_prob': 0.10},
        {'name': 'steady_jogger', 'base_speed': 0.10, 'variability': 0.3, 'pause_prob': 0.02, 'reverse_prob': 0.04},
        {'name': 'variable_pacer', 'base_speed': 0.14, 'variability': 1.5, 'pause_prob': 0.06, 'reverse_prob': 0.09},
        {'name': 'cautious_mover', 'base_speed': 0.05, 'variability': 0.5, 'pause_prob': 0.12, 'reverse_prob': 0.15},
        {'name': 'energetic_sprinter', 'base_speed': 0.20, 'variability': 1.0, 'pause_prob': 0.01, 'reverse_prob': 0.03},
        {'name': 'back_and_forth', 'base_speed': 0.09, 'variability': 0.7, 'pause_prob': 0.15, 'reverse_prob': 0.25}
    ]
    
    # Select behavior pattern for this variant
    pattern = behavior_patterns[variant_seed % len(behavior_patterns)]
    
    # Generate phase values
    phase_values = []
    current_phase = random.uniform(0, 2 * math.pi)  # Start at random phase
    current_velocity = 0.0  # Current velocity (can be positive or negative)
    direction = 1  # 1 for forward, -1 for backward
    
    for frame in range(total_frames):
        # Every 30-300 frames (0.5-5 seconds), potentially change behavior
        if frame % random.randint(30, 300) == 0:
            # Determine if mouse changes direction
            if random.random() < pattern['reverse_prob']:
                direction *= -1  # Reverse direction
                current_velocity *= random.uniform(0.3, 0.8)  # Slow down during direction change
            
            # Determine if mouse pauses
            elif random.random() < pattern['pause_prob']:
                current_velocity *= random.uniform(0.0, 0.2)  # Pause or near-pause
                
            # Otherwise, change speed
            else:
                # Generate new target velocity
                base_speed = pattern['base_speed']
                variability = pattern['variability']
                
                # Add random variation to speed (radians per frame)
                speed_variation = random.gauss(0, variability * base_speed)
                target_velocity = direction * (base_speed + speed_variation)
                
                # Gradually change velocity towards target
                velocity_change = (target_velocity - current_velocity) * random.uniform(0.1, 0.3)
                current_velocity += velocity_change
                
                # Occasionally add brief bursts or slowdowns
                if random.random() < 0.02:  # 2% chance of burst
                    current_velocity *= random.uniform(1.5, 3.0)
                elif random.random() < 0.03:  # 3% chance of slowdown
                    current_velocity *= random.uniform(0.2, 0.6)
        
        # Add small random noise to velocity
        velocity_noise = random.gauss(0, 0.01)
        actual_velocity = current_velocity + velocity_noise
        
        # Apply friction to make movement more realistic
        current_velocity *= 0.998
        
        # Clamp velocity to reasonable bounds (prevent unrealistic speeds)
        max_velocity = 0.5  # Maximum ~5 rotations per second
        current_velocity = max(-max_velocity, min(max_velocity, current_velocity))
        
        # Update phase
        current_phase += actual_velocity
        
        # Wrap phase to stay within 0-2π range
        current_phase = current_phase % (2 * math.pi)
        
        phase_values.append(current_phase)
    
    return phase_values


def generate_test_variants():
    """Generate short (1 minute) test versions of each experiment type for rapid Bonsai validation.
    
    Creates test files in subfolders that mirror the normal file structure:
    - blocks/test/standard/standard_oddball_variant_01.csv
    - blocks/test/standard/standard_control_variant_01.csv
    - blocks/test/jitter/jitter_variant_01.csv
    - blocks/test/jitter/jitter_control_variant_01.csv
    - blocks/test/sequentials/sequential_variant_01.csv
    - blocks/test/sequentials/sequential_control_variant_01.csv
    - blocks/test/motor/motor_oddball_variant_01.csv
    - blocks/test/motor/motor_control_variant_01.csv
    """
    
    # Create test directories if they don't exist
    test_dirs = {
        'standard': Path("blocks/test/standard"),
        'jitter': Path("blocks/test/jitter"),
        'sequentials': Path("blocks/test/sequentials"),
        'motor': Path("blocks/test/motor")
    }
    
    for test_dir in test_dirs.values():
        test_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating test variants (1 minute each) in subfolder structure...")
    
    # Test variant for standard oddball (60 seconds with 1 oddball)
    rows = []
    # Add 12 standard trials (5 seconds each = 60 seconds total)
    for i in range(12):
        row = DEFAULT_PARAMS.copy()
        row['Trial_Type'] = 'standard'
        row['Block_Type'] = 'standard_oddball'
        rows.append(row)
    
    # Add 1 oddball trial (replace the 7th trial)
    oddball_row = DEFAULT_PARAMS.copy()
    oddball_row['Diameter'] = 180  # Oddball diameter
    oddball_row['Trial_Type'] = 'oddball'
    oddball_row['Block_Type'] = 'standard_oddball'
    rows[6] = oddball_row  # Replace 7th trial
    
    filename = test_dirs['standard'] / "standard_oddball_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for jitter (60 seconds with 1 oddball)
    rows = []
    # Add 12 jitter trials (5 seconds each = 60 seconds total)
    for i in range(12):
        row = DEFAULT_PARAMS.copy()
        row['Diameter'] = 320  # Jitter context
        row['Duration'] = 0.500  # Jitter duration
        row['Trial_Type'] = 'standard'
        row['Block_Type'] = 'jitter'
        rows.append(row)
    
    # Add 1 oddball trial (replace the 7th trial)
    oddball_row = DEFAULT_PARAMS.copy()
    oddball_row['Diameter'] = 320  # Jitter context
    oddball_row['Duration'] = 0.100  # Oddball duration
    oddball_row['Trial_Type'] = 'oddball'
    oddball_row['Block_Type'] = 'jitter'
    rows[6] = oddball_row  # Replace 7th trial
    
    filename = test_dirs['jitter'] / "jitter_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for sequential (60 seconds with 1 oddball)
    rows = []
    # Add 240 sequential trials (0.25 seconds each = 60 seconds total)
    for i in range(240):
        row = SEQUENTIAL_PARAMS.copy()
        row['Orientation'] = 0  # Standard orientation
        row['Trial_Type'] = 'standard'
        row['Block_Type'] = 'sequential'
        rows.append(row)
    
    # Add 1 oddball trial (replace the 120th trial)
    oddball_row = SEQUENTIAL_PARAMS.copy()
    oddball_row['Orientation'] = 90  # Oddball orientation
    oddball_row['Trial_Type'] = 'oddball'
    oddball_row['Block_Type'] = 'sequential'
    rows[119] = oddball_row  # Replace 120th trial
    
    filename = test_dirs['sequentials'] / "sequential_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for motor oddball (60 seconds with halts every ~1 second)
    rows = []
    frame_rate = 60
    total_frames = 60 * frame_rate  # 60 seconds
    frame_duration = 1.0 / frame_rate  # Duration per frame (0.016666...)
    oddball_duration = 0.343  # Oddball duration (same as regular motor oddball)
    
    # Add halts every ~1 second (every 60 frames) for rapid validation
    halt_frames = set(range(60, total_frames, 60))  # Frames 60, 120, 180, ..., 3540
    
    for frame in range(total_frames):
        if frame in halt_frames:
            # This is a halt frame - use oddball duration
            row = {
                'Contrast': 1,
                'Delay': 0,  # Motor oddball uses 0 delay
                'Diameter': 360,  # Motor oddball uses 360 diameter
                'Duration': oddball_duration,  # Oddball duration (0.343 seconds)
                'Orientation': 0,
                'Spatial_Frequency': 0.04,
                'Temporal_Frequency': 0,  # Motor oddball uses 0 temporal frequency
                'X': 0,
                'Y': 0,
                'Phase': 'wheel',  # Motor oddball uses 'wheel' phase
                'Trial_Type': 'halt',
                'Block_Type': 'motor_oddball'
            }
        else:
            # This is a normal frame - use frame duration
            row = {
                'Contrast': 1,
                'Delay': 0,  # Motor oddball uses 0 delay
                'Diameter': 360,  # Motor oddball uses 360 diameter
                'Duration': frame_duration,  # Frame duration (1/60 seconds)
                'Orientation': 0,
                'Spatial_Frequency': 0.04,
                'Temporal_Frequency': 0,  # Motor oddball uses 0 temporal frequency
                'X': 0,
                'Y': 0,
                'Phase': 'wheel',  # Motor oddball uses 'wheel' phase
                'Trial_Type': 'standard',
                'Block_Type': 'motor_oddball'
            }
        rows.append(row)
    
    filename = test_dirs['motor'] / "motor_oddball_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for standard control (orientation tuning)
    rows = []
    orientations = [0, 45, 90, 135, 180, 225, 270, 315]
    
    # 2 repetitions of each orientation (16 trials total, ~1 minute)
    for rep in range(2):
        for orientation in orientations:
            row = DEFAULT_PARAMS.copy()
            row['Orientation'] = orientation
            row['Trial_Type'] = 'standard'
            row['Block_Type'] = 'standard_control'
            rows.append(row)
    
    # Shuffle the trials
    random.shuffle(rows)
    
    filename = test_dirs['standard'] / "standard_control_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for jitter control (duration tuning)
    rows = []
    durations = [0.100, 0.200, 0.300, 0.400, 0.500, 0.600, 0.700, 0.800]
    
    # 2 repetitions of each duration (16 trials total, ~1 minute)
    for rep in range(2):
        for duration in durations:
            row = DEFAULT_PARAMS.copy()
            row['Diameter'] = 320  # Jitter context
            row['Duration'] = duration
            row['Trial_Type'] = 'standard'
            row['Block_Type'] = 'jitter_control'
            rows.append(row)
    
    # Shuffle the trials
    random.shuffle(rows)
    
    filename = test_dirs['jitter'] / "jitter_control_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for sequential control (orientation tuning with sequential parameters)
    rows = []
    orientations = [0, 45, 90, 135, 180, 225, 270, 315]
    
    # 30 repetitions of each orientation (240 trials total, ~1 minute)
    for rep in range(30):
        for orientation in orientations:
            row = SEQUENTIAL_PARAMS.copy()
            row['Orientation'] = orientation
            row['Trial_Type'] = 'standard'
            row['Block_Type'] = 'sequential_control'
            rows.append(row)
    
    # Shuffle the trials
    random.shuffle(rows)
    
    filename = test_dirs['sequentials'] / "sequential_control_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    # Test variant for motor control (wheel-controlled phase)
    rows = []
    frame_rate = 60
    total_frames = 60 * frame_rate  # 60 seconds
    frame_duration = 1.0 / frame_rate  # Duration per frame (0.016666...)
    
    # Generate realistic mouse wheel movement for test (using variant 0 behavior)
    test_phase_values = generate_mouse_wheel_behavior(total_frames, 0)
    
    # Default parameters for motor control test
    default_params = {
        'Contrast': 1,
        'Delay': 0,
        'Diameter': 370,  # Motor control marker
        'Duration': frame_duration,
        'Orientation': 0,
        'Spatial_Frequency': 0.04,
        'Temporal_Frequency': 0,  # Set to 0 for wheel-controlled
        'X': 0,
        'Y': 0,
        'Phase': 0,  # Will be updated with realistic values
        'Trial_Type': 'standard',
        'Block_Type': 'motor_control'
    }
    
    # Generate frame-by-frame data for 60 seconds
    for frame_num in range(total_frames):
        frame_data = default_params.copy()
        frame_data['Phase'] = test_phase_values[frame_num]
        rows.append(frame_data)
    
    filename = test_dirs['motor'] / "motor_control_variant_01.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {filename}")
    
    total_files = sum(len(list(test_dir.glob('*.csv'))) for test_dir in test_dirs.values())
    print(f"\nGenerated {total_files} test CSV files in subfolder structure:")
    for test_dir in test_dirs.values():
        for csv_file in test_dir.glob('*.csv'):
            print(f"  - {csv_file}")


def generate_motor_nooddball_csv(duration_seconds=2100, frame_rate=60, n_variants=10):
    """
    Generate motor no-oddball CSV files with pure close-loop control for 35 minutes.
    
    This creates blocks that are purely close-loop - all frames have wheel control
    for the Phase column, with no oddballs whatsoever. This is useful for testing
    sustained close-loop behavior.
    
    Args:
        duration_seconds: Total duration of the stimulus in seconds (default 35 min = 2100s)
        frame_rate: Frame rate in Hz
        n_variants: Number of variants to generate
    """
    print("=== Generating Motor No-Oddball Variants (Pure Close-Loop) ===")
    
    total_frames = int(duration_seconds * frame_rate)
    frame_duration = 1.0 / frame_rate  # Duration per frame
    
    # Default parameters for motor no-oddball (all frames controlled by wheel movement)
    default_params = {
        'Contrast': 1,
        'Delay': 0,
        'Diameter': 380,  # Motor no-oddball marker (different from oddball=360 and control=370)
        'Duration': frame_duration,
        'Orientation': 0,
        'Spatial_Frequency': 0.04,
        'Temporal_Frequency': 0,  # Set to 0 for wheel-controlled
        'X': 0,
        'Y': 0,
        'Phase': 'wheel',  # All frames use wheel control
        'Trial_Type': 'standard',
        'Block_Type': 'motor_nooddball'
    }
    
    print(f"Motor no-oddball parameters:")
    print(f"  - Duration: {duration_seconds}s ({duration_seconds/60:.1f} minutes, {total_frames} frames)")
    print(f"  - Frame rate: {frame_rate} Hz")
    print(f"  - Phase: ALL frames controlled by wheel ('wheel' value)")
    print(f"  - NO oddballs - pure close-loop control")
    print(f"  - Block type: motor_nooddball")
    print()
    
    for variant in range(n_variants):
        print(f"Generating motor no-oddball variant {variant + 1}/{n_variants}")
        
        # Generate frame-by-frame data - all frames are identical close-loop
        all_frames = []
        
        for frame_num in range(total_frames):
            frame_data = default_params.copy()
            # Every frame uses wheel control - no variation needed
            all_frames.append(frame_data)
        
        # Save to CSV in the motor_nooddball subfolder
        output_file = f"blocks/motor_nooddball/motor_nooddball_variant_{variant + 1:02d}.csv"
        filepath = Path(output_file)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=STANDARD_FIELDNAMES)
            writer.writeheader()
            writer.writerows(all_frames)
        
        print(f"  Saved: {output_file} ({len(all_frames)} frames)")
    
    print(f"\nGenerated {n_variants} motor no-oddball variants (35 minutes each, pure close-loop)")
    print(f"All files saved in: blocks/motor_nooddball/")
    print()


def main():
    """Main function - generate all experiment CSV files."""
    print("Generating all experiment CSV files...")
    print()
    
    # Generate standard oddball variants (10 shuffled versions)
    generate_standard_oddball_variants(n_variants=10)
    print()
    
    # Generate jitter variants (10 shuffled versions)
    generate_jitter_variants(n_variants=10)
    print()
    
    # Generate standard control (orientation tuning)
    generate_standard_control_csv()
    print()
    
    # Generate jitter control (duration tuning)
    generate_jitter_control_csv()
    print()
    
    # Generate sequential control (orientation tuning with sequential parameters)
    generate_sequential_control_csv()
    print()
    
    # Generate sequential variants
    generate_all_sequential_variants(n_normal_sequences=80, n_oddball_45=5, n_oddball_90=5, 
                                   n_oddball_halt=5, n_oddball_omission=5, n_variants=10)
    print()
    
    # Generate motor oddball variants (frame-based oddballs)
    generate_motor_oddball_csv(duration_seconds=600, frame_rate=60, n_oddball_per_type=20, 
                              min_interval_seconds=2.0, n_variants=10)
    print()
    
    # Generate motor control variants (wheel-controlled phase)
    generate_motor_control_csv(duration_seconds=600, frame_rate=60, n_variants=10)
    print()
    
    # Generate test variants (1 minute each) - for rapid Bonsai validation
    generate_test_variants()
    print()
    
    # Generate motor no-oddball variants (pure close-loop)
    generate_motor_nooddball_csv(duration_seconds=2100, frame_rate=60, n_variants=1)
    print()
    
    print("All CSV files generated successfully!")
    print("Files created:")
    # Control variants
    for variant in range(1, 11):
        print(f"  - blocks/standard/standard_control_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/jitter/jitter_control_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/sequentials/sequential_control_variant_{variant:02d}.csv")
    # Oddball variants  
    for variant in range(1, 11):
        print(f"  - blocks/standard/standard_oddball_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/jitter/jitter_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/sequentials/sequential_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/motor/motor_oddball_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/motor/motor_control_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/motor_nooddball/motor_nooddball_variant_{variant:02d}.csv")
    # Test files (organized in subfolders matching normal structure)
    test_base = Path("blocks/test")
    for subfolder in ['standard', 'jitter', 'sequentials', 'motor']:
        test_dir = test_base / subfolder
        if test_dir.exists():
            for test_file in test_dir.glob("*.csv"):
                print(f"  - {test_file}")


if __name__ == "__main__":
    main()
