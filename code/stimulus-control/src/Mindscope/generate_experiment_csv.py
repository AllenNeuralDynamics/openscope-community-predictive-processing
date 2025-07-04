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
    'Y': 0
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
    'Y': 0
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
    
    # Set diameter markers based on context
    if context_type == 'standard':
        normal_diameter = DIAMETER_MARKERS['standard_normal']
        oddball_diameter = DIAMETER_MARKERS['standard_oddball']
    elif context_type == 'jitter':
        normal_diameter = DIAMETER_MARKERS['jitter_normal']
        oddball_diameter = DIAMETER_MARKERS['jitter_oddball']
    elif context_type == 'standard_control':
        normal_diameter = DIAMETER_MARKERS['standard_control']
        oddball_diameter = DIAMETER_MARKERS['standard_control']
    elif context_type == 'jitter_control':
        normal_diameter = DIAMETER_MARKERS['jitter_control']
        oddball_diameter = DIAMETER_MARKERS['jitter_control']
    elif context_type == 'sequential_control':
        normal_diameter = DIAMETER_MARKERS['sequential_control']
        oddball_diameter = DIAMETER_MARKERS['sequential_control']
    else:  # Default case
        normal_diameter = 360
        oddball_diameter = 361
    
    # Add standard trials
    for _ in range(n_standard_trials):
        trial = DEFAULT_PARAMS.copy()
        trial['Diameter'] = normal_diameter
        trials.append(trial)
    
    # Add oddball trials
    for n_trials, modified_params in oddball_configs:
        oddball_params = DEFAULT_PARAMS.copy()
        oddball_params.update(modified_params)
        oddball_params['Diameter'] = oddball_diameter
        
        for _ in range(n_trials):
            trials.append(oddball_params.copy())
    
    # Save to CSV
    filepath = Path(output_file)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = list(DEFAULT_PARAMS.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
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
    """Generate standard control CSV (orientation tuning)."""
    print("=== Generating Standard Control (Orientation Tuning) ===")
    
    # Generate orientations from 0 to 360 degrees
    n_control_per_orientation = 10
    orientations = list(range(0, 360, 15))  # Every 15 degrees: 0, 15, 30, ..., 345
    
    oddball_configs = []
    for orientation in orientations:
        oddball_configs.append((n_control_per_orientation, {'Orientation': orientation}))
    
    generate_experiment_csv("blocks/standard/standard_control.csv", 0, oddball_configs, 'standard_control')


def generate_jitter_control_csv():
    """Generate jitter control CSV (duration tuning)."""
    print("=== Generating Jitter Control (Duration Tuning) ===")
    
    # All durations presented equally
    n_control_per_duration = 50
    durations = [0.050, 0.100, 0.200, 0.343]  # Including the default duration
    
    oddball_configs = []
    for duration in durations:
        oddball_configs.append((n_control_per_duration, {'Duration': duration}))
    
    generate_experiment_csv("blocks/jitter/jitter_control.csv", 0, oddball_configs, 'jitter_control')


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
            
            if orientation == -1:  # halt
                trial['Orientation'] = 0
                trial['Spatial_Frequency'] = 0
            elif orientation == -2:  # omission
                trial['Orientation'] = 0
                trial['Contrast'] = 0
            else:
                trial['Orientation'] = orientation
            
            trials.append(trial)
        
        # Add the omission (5th trial in sequence)
        omission_trial = SEQUENTIAL_PARAMS.copy()
        omission_trial['Contrast'] = 0
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
            fieldnames = list(SEQUENTIAL_PARAMS.keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for trial in trials:
                writer.writerow(trial)
        
        print(f"  Saved {len(trials)} trials to {output_file}")
    
    print(f"\nGenerated {n_variants} sequential variants")
    print(f"Each variant contains {total_sequences} sequences (5 trials each = {total_sequences * 5} total trials)")


def generate_sequential_control_csv():
    """Generate sequential control CSV (orientation tuning with sequential parameters)."""
    print("=== Generating Sequential Control (Orientation Tuning) ===")
    
    # Generate orientations from 0 to 360 degrees with sequential parameters
    n_control_per_orientation = 10
    orientations = list(range(0, 360, 15))  # Every 15 degrees: 0, 15, 30, ..., 345
    
    trials = []
    
    # Add orientation trials with sequential parameters
    for orientation in orientations:
        for _ in range(n_control_per_orientation):
            trial = SEQUENTIAL_PARAMS.copy()
            trial['Orientation'] = orientation
            trial['Diameter'] = DIAMETER_MARKERS['sequential_control']
            trials.append(trial)
    
    # Add omission trials (same number as one orientation)
    for _ in range(n_control_per_orientation):
        omission_trial = SEQUENTIAL_PARAMS.copy()
        omission_trial['Contrast'] = 0
        omission_trial['Diameter'] = DIAMETER_MARKERS['sequential_control']
        trials.append(omission_trial)
    
    # Save to CSV
    filepath = Path("blocks/sequentials/sequential_control.csv")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = list(SEQUENTIAL_PARAMS.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for trial in trials:
            writer.writerow(trial)
    
    print(f"Generated {len(trials)} trials:")
    print(f"  - {len(orientations)} orientations × {n_control_per_orientation} trials each = {len(orientations) * n_control_per_orientation} orientation trials")
    print(f"  - {n_control_per_orientation} omission trials")
    print(f"  - All trials use sequential parameters (duration: {SEQUENTIAL_PARAMS['Duration']}s, delay: {SEQUENTIAL_PARAMS['Delay']}s)")
    print(f"  - Diameter marker: {DIAMETER_MARKERS['sequential_control']}")
    print(f"Saved to: blocks/sequentials/sequential_control.csv")


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
    
    print("All CSV files generated successfully!")
    print("Files created:")
    print("  - blocks/standard/standard_control.csv")
    print("  - blocks/jitter/jitter_control.csv")
    print("  - blocks/sequentials/sequential_control.csv")
    for variant in range(1, 11):
        print(f"  - blocks/standard/standard_oddball_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/jitter/jitter_variant_{variant:02d}.csv")
    for variant in range(1, 11):
        print(f"  - blocks/sequentials/sequential_variant_{variant:02d}.csv")


if __name__ == "__main__":
    main()
