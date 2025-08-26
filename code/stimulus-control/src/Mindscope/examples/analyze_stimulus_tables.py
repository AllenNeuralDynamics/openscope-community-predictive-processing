#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stimulus Table Analyzer and Visualizer

This script analyzes the generated stimulus tables and creates visualizations
showing the temporal structure of experimental sessions, including:
- Block durations and types
- Oddball occurrence patterns
- Trial timing structure

Usage:
    python analyze_stimulus_tables.py [--session-type visual_mismatch] [--output-dir plots]
"""

import csv
import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict, Counter
import seaborn as sns

# Set style for better plots
plt.style.use('default')
sns.set_palette("husl")

def load_stimulus_table(csv_path):
    """Load a stimulus table CSV file and return trials data."""
    trials = []
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                for field in ['Block_Number', 'Trial_Number', 'Sequence_Number', 'Trial_In_Sequence',
                             'Block_Duration_Minutes', 'Contrast', 'Delay', 'Diameter', 'Duration', 
                             'Orientation', 'Spatial_Frequency', 'Temporal_Frequency', 'X', 'Y', 'Phase']:
                    if field in row and row[field]:
                        try:
                            if field in ['Block_Number', 'Trial_Number', 'Sequence_Number', 'Trial_In_Sequence', 
                                       'Orientation', 'X', 'Y', 'Phase']:
                                if row[field] != 'wheel':  # Handle special case for motor blocks
                                    row[field] = int(float(row[field]))
                            else:
                                row[field] = float(row[field])
                        except (ValueError, TypeError):
                            pass  # Keep original value if conversion fails
                
                trials.append(row)
        
        print("Loaded %d trials from %s" % (len(trials), os.path.basename(csv_path)))
        return trials
        
    except Exception as e:
        print("Error loading %s: %s" % (csv_path, e))
        return []

def analyze_block_structure(trials):
    """Analyze the block structure of trials."""
    blocks = {}
    
    for trial in trials:
        block_num = trial.get('Block_Number', 0)
        
        if block_num not in blocks:
            blocks[block_num] = {
                'label': trial.get('Block_Label', 'Unknown'),
                'type': trial.get('Block_Type', 'Unknown'),
                'duration_minutes': trial.get('Block_Duration_Minutes', 0),
                'trials': [],
                'trial_types': Counter(),
                'start_trial': float('inf'),
                'end_trial': 0
            }
        
        blocks[block_num]['trials'].append(trial)
        blocks[block_num]['trial_types'][trial.get('Trial_Type', 'unknown')] += 1
        
        trial_num = trial.get('Trial_Number', 0)
        blocks[block_num]['start_trial'] = min(blocks[block_num]['start_trial'], trial_num)
        blocks[block_num]['end_trial'] = max(blocks[block_num]['end_trial'], trial_num)
    
    return blocks

def calculate_cumulative_time(trials, blocks):
    """Calculate cumulative time for trials using block boundaries as reference."""
    print("  Plotting all %d trials..." % len(trials))
    
    # Create a mapping from block number to block start time (in seconds)
    block_start_times = {}
    current_time = 0
    for block_num in sorted(blocks.keys()):
        block_start_times[block_num] = current_time
        current_time += blocks[block_num]['duration_minutes'] * 60
    
    times = []
    
    # Calculate trial times based on their position within their block
    for trial in trials:
        block_num = trial.get('Block_Number', 1)
        trial_num = trial.get('Trial_Number', 1)
        
        # Get block start time and info
        block_start = block_start_times.get(block_num, 0)
        block_info = blocks.get(block_num, {})
        
        # Calculate relative position within the block
        if 'start_trial' in block_info and 'end_trial' in block_info:
            block_start_trial = block_info['start_trial']
            block_end_trial = block_info['end_trial']
            trials_in_block = block_end_trial - block_start_trial + 1
            
            if trials_in_block > 0:
                # Position within block (0.0 to 1.0)
                block_progress = (trial_num - block_start_trial) / trials_in_block
                # Scale to block duration
                block_duration = block_info['duration_minutes'] * 60
                trial_time = block_start + (block_progress * block_duration)
            else:
                trial_time = block_start
        else:
            trial_time = block_start
        
        times.append(trial_time)
    
    return np.array(times)

def plot_session_structure(trials, session_type, output_dir):
    """Create a comprehensive visualization of the session structure."""
    
    print("  Creating visualization (this may take a moment for large datasets)...")
    
    # Analyze blocks
    blocks = analyze_block_structure(trials)
    
    # Calculate trial times using all trials
    trial_times = calculate_cumulative_time(trials, blocks)
    
    # Create figure with subplots (optimized for presentation slides)
    fig, axes = plt.subplots(3, 1, figsize=(20, 16))
    fig.suptitle('Stimulus Table Structure: %s' % session_type.replace('_', ' ').title(), 
                 fontsize=24, fontweight='bold')
    
    # Define colors for different block types
    block_colors = {
        'standard_control': '#E8F4FD',      # Light blue
        'standard_oddball': '#FFE6E6',      # Light red
        'motor_oddball': '#FFE6CC',         # Light orange  
        'sequential_oddball': '#E6F3E6',    # Light green
        'jitter_oddball': '#F0E6FF',        # Light purple
        'sequential_long': '#E6F3E6',       # Light green
        'motor_long': '#FFE6CC',            # Light orange
        'sequential_control_block': '#F5F5F5',  # Light gray
        'jitter_control': '#FFF0E6',        # Light beige
        'open_loop_prerecorded': '#E6E6FF', # Light lavender
        'rf_mapping': '#FFFFCC'             # Light yellow
    }
    
    # Calculate total session duration for consistent x-axis scaling
    total_session_duration = sum(blocks[block_num]['duration_minutes'] * 60 
                                for block_num in sorted(blocks.keys()))
    
    # Plot 1: Block timeline with durations
    ax1 = axes[0]
    ax1.set_title('Block Structure and Timeline', fontsize=18, fontweight='bold')
    
    current_time = 0
    block_positions = []
    
    for block_num in sorted(blocks.keys()):
        block = blocks[block_num]
        duration_seconds = block['duration_minutes'] * 60
        block_type = block['type']
        
        # Get color for block type
        color = block_colors.get(block_type, '#F0F0F0')
        
        # Draw block rectangle
        rect = patches.Rectangle((current_time, 0), duration_seconds, 1, 
                               facecolor=color, edgecolor='black', linewidth=1)
        ax1.add_patch(rect)
        
        # Create informative label based on block type
        block_type_descriptions = {
            'standard_control': 'Control\n(Standard\nstimuli)',
            'standard_oddball': 'Visual\nMismatch\n(Orientation\noddballs)',
            'motor_oddball': 'Sensory-Motor\nMismatch\n(Motor\ncoupling)',
            'sequential_oddball': 'Sequence\nMismatch\n(Sequential\nlearning)',
            'jitter_oddball': 'Duration\nMismatch\n(Temporal\noddballs)',
            'sequential_long': 'Sequence\nControl\n(No oddballs)',
            'motor_long': 'Motor\nControl\n(No oddballs)',
            'sequential_control_block': 'Control\n(Shuffled\nsequences)',
            'jitter_control': 'Control\n(Duration\ntuning)',
            'open_loop_prerecorded': 'Control\n(Pre-recorded)',
            'rf_mapping': 'RF Mapping\n(Spatial\ntuning)'
        }
        
        type_description = block_type_descriptions.get(block_type, block_type.replace('_', ' ').title())
        
        # Determine appropriate font size based on block duration
        # Larger fonts for presentation readability
        if duration_seconds < 300:  # Less than 5 minutes
            font_size = 10
        elif duration_seconds < 600:  # Less than 10 minutes
            font_size = 12
        else:
            font_size = 14
        
        # Add block label with improved formatting
        label_text = "Block %d\n%s\n(%.1f min)" % (
            block_num, type_description, block['duration_minutes'])
        
        # Use bbox for better readability
        ax1.text(current_time + duration_seconds/2, 0.5, label_text,
                ha='center', va='center', fontsize=font_size, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8, edgecolor='none'))
        
        block_positions.append((current_time, current_time + duration_seconds, block_num, block_type))
        current_time += duration_seconds
    
    # Use consistent x-axis range for all plots
    ax1.set_xlim(0, total_session_duration)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel('Time (seconds)', fontsize=16)
    ax1.set_ylabel('Blocks', fontsize=16)
    ax1.set_yticks([])
    ax1.tick_params(axis='x', labelsize=14)
    
    # Convert x-axis to minutes for readability
    ax1_twin = ax1.twiny()
    ax1_twin.set_xlim(0, total_session_duration/60)
    ax1_twin.set_xlabel('Time (minutes)', fontsize=16)
    ax1_twin.tick_params(axis='x', labelsize=14)
    
    # Plot 2: Orientation timeline showing grating orientations over time
    ax2 = axes[1]
    ax2.set_title('Grating Orientations Over Time', fontsize=18, fontweight='bold')
    
    # Extract orientation data from trials
    orientation_times = []
    orientations = []
    
    # Color map for different orientations (expanded for more orientations)
    orientation_colors = {
        0: '#1f77b4',    # Blue (vertical)
        45: '#ff7f0e',   # Orange 
        90: '#2ca02c',   # Green (horizontal)
        135: '#d62728',  # Red
        22.5: '#9467bd', # Purple
        67.5: '#8c564b', # Brown  
        112.5: '#e377c2',# Pink
        157.5: '#7f7f7f',# Gray
        180: '#bcbd22',  # Olive
        225: '#17becf',  # Cyan
        270: '#ff9896',  # Light red
        315: '#98df8a'   # Light green
    }
    
    print("    Extracting orientation data...")
    
    for i, trial in enumerate(trials):
        # Only plot trials that have meaningful orientations (not omissions, etc.)
        trial_type = trial.get('Trial_Type', 'standard')
        if trial_type not in ['omission', 'sequence_omission']:
            orientation = trial.get('Orientation', 0)
            
            # Handle numeric orientations
            if isinstance(orientation, (int, float)):
                orientation_times.append(trial_times[i])
                orientations.append(orientation)
    
    print("    Found %d trials with orientation data..." % len(orientation_times))
    
    if orientation_times:
        # Use binning for very large datasets to improve performance
        if len(orientation_times) > 2000:
            print("    Using binned representation for orientations...")
            # Create time bins
            n_bins = min(300, len(orientation_times) // 10)
            time_bins = np.linspace(0, total_session_duration, n_bins)
            
            # Group orientations by value
            unique_orientations = sorted(list(set(orientations)))
            
            for orientation in unique_orientations:
                # Get times for this orientation
                orient_times = [orientation_times[j] for j, o in enumerate(orientations) if o == orientation]
                
                if orient_times:
                    # Bin the times
                    counts, bin_edges = np.histogram(orient_times, bins=time_bins)
                    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
                    
                    # Plot as scatter points where counts > 0
                    mask = counts > 0
                    if np.any(mask):
                        color = orientation_colors.get(orientation, 'gray')
                        ax2.scatter(bin_centers[mask], [orientation] * np.sum(mask), 
                                  c=color, alpha=0.7, s=30, label='%d°' % orientation)
        else:
            # Plot individual points for smaller datasets
            for i, (time, orientation) in enumerate(zip(orientation_times, orientations)):
                color = orientation_colors.get(orientation, 'gray')
                ax2.scatter(time, orientation, c=color, alpha=0.7, s=25)
        
        # Set y-axis to show orientation values
        if orientations:
            unique_orientations = sorted(list(set(orientations)))
            ax2.set_yticks(unique_orientations)
            ax2.set_yticklabels(['%d°' % o for o in unique_orientations])
        
        # Add legend for orientations
        unique_orientations = sorted(list(set(orientations)))
        legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                     markerfacecolor=orientation_colors.get(o, 'gray'),
                                     label='%d°' % o, markersize=10) for o in unique_orientations[:8]]  # Limit legend
        if legend_elements:
            ax2.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.12, 1),
                      fontsize=12, frameon=True, fancybox=True, shadow=True)
    
    # Use consistent x-axis range with other plots
    ax2.set_xlim(0, total_session_duration)
    ax2.set_xlabel('Time (seconds)', fontsize=16)
    ax2.set_ylabel('Orientation (degrees)', fontsize=16)
    ax2.tick_params(axis='both', labelsize=14)
    
    # Add grid for better readability
    ax2.grid(True, alpha=0.3)
    
    # Add vertical lines for block boundaries to show where different blocks are
    current_time = 0
    for block_num in sorted(blocks.keys()):
        block = blocks[block_num]
        duration_seconds = block['duration_minutes'] * 60
        ax2.axvline(current_time, color='black', linestyle='--', alpha=0.3, linewidth=0.8)
        current_time += duration_seconds
    ax2.axvline(current_time, color='black', linestyle='--', alpha=0.3, linewidth=0.8)  # Final boundary
    
    # Plot 3: Oddball distribution analysis (optimized)
    ax3 = axes[2] 
    ax3.set_title('Oddball Events Distribution', fontsize=18, fontweight='bold')
    
    # Find oddball events (more efficiently)
    oddball_types = ['orientation_45', 'orientation_90', 'halt', 'omission', 'jitter']
    oddball_events = []
    
    for i, trial in enumerate(trials):
        trial_type = trial.get('Trial_Type', 'standard')
        if trial_type in oddball_types:
            oddball_events.append((trial_times[i], trial_type, trial.get('Block_Number', 0)))
    
    print("    Found %d oddball events to plot..." % len(oddball_events))
    
    # Group oddball events by type for efficient plotting
    oddball_by_type = {}
    for time, oddball_type, block_num in oddball_events:
        if oddball_type not in oddball_by_type:
            oddball_by_type[oddball_type] = []
        oddball_by_type[oddball_type].append(time)
    
    # Plot oddball events by type with specific colors for oddball types
    oddball_colors = {
        'orientation_45': 'red',
        'orientation_90': 'orange', 
        'halt': 'purple',
        'omission': 'green',
        'jitter': 'magenta'
    }
    
    for oddball_type, times in oddball_by_type.items():
        color = oddball_colors.get(oddball_type, 'gray')
        y_pos = [oddball_type] * len(times)
        ax3.scatter(times, y_pos, c=color, alpha=0.8, s=80, marker='o', label=oddball_type)
    
    # Add vertical lines for block boundaries
    current_time = 0
    for block_num in sorted(blocks.keys()):
        block = blocks[block_num]
        duration_seconds = block['duration_minutes'] * 60
        ax3.axvline(current_time, color='black', linestyle='--', alpha=0.5, linewidth=0.5)
        current_time += duration_seconds
    ax3.axvline(current_time, color='black', linestyle='--', alpha=0.5, linewidth=0.5)  # Final boundary
    
    # Use consistent x-axis range with other plots
    ax3.set_xlim(0, total_session_duration)
    ax3.set_xlabel('Time (seconds)', fontsize=16)
    ax3.set_ylabel('Oddball Type', fontsize=16)
    ax3.tick_params(axis='both', labelsize=14)
    
    # Add oddball legend
    if oddball_by_type:
        ax3.legend(loc='upper right', bbox_to_anchor=(1.12, 1),
                  fontsize=12, frameon=True, fancybox=True, shadow=True)
    
    # Adjust layout to prevent legend overlap
    plt.subplots_adjust(right=0.88)  # Make room for legends
    plt.tight_layout(rect=[0, 0, 0.88, 1])  # Adjust for legends
    
    # Save plot
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, '%s_structure_analysis.png' % session_type)
    plt.savefig(output_path, dpi=200, bbox_inches='tight', pad_inches=0.2)  # Higher DPI for text clarity
    print("  Saved plot: %s" % output_path)
    
    return fig

def create_summary_statistics(trials, session_type, output_dir):
    """Create summary statistics for the session."""
    
    blocks = analyze_block_structure(trials)
    
    # Create summary report
    summary_path = os.path.join(output_dir, '%s_summary_stats.txt' % session_type)
    
    with open(summary_path, 'w') as f:
        f.write("STIMULUS TABLE ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write("Session Type: %s\n" % session_type.replace('_', ' ').title())
        f.write("Total Trials: %d\n" % len(trials))
        f.write("Total Blocks: %d\n" % len(blocks))
        f.write("\n")
        
        # Calculate total session duration
        total_duration = sum(block['duration_minutes'] for block in blocks.values())
        f.write("Total Session Duration: %.1f minutes (%.1f hours)\n" % (
            total_duration, total_duration/60))
        f.write("\n")
        
        # Block-by-block breakdown
        f.write("BLOCK BREAKDOWN:\n")
        f.write("-" * 30 + "\n")
        
        for block_num in sorted(blocks.keys()):
            block = blocks[block_num]
            f.write("Block %d: %s\n" % (block_num, block['label']))
            f.write("  Type: %s\n" % block['type'])
            f.write("  Duration: %.1f minutes\n" % block['duration_minutes'])
            f.write("  Trials: %d\n" % len(block['trials']))
            
            # Trial type breakdown
            f.write("  Trial Types:\n")
            for trial_type, count in block['trial_types'].most_common():
                percentage = 100.0 * count / len(block['trials'])
                f.write("    %s: %d (%.1f%%)\n" % (trial_type, count, percentage))
            f.write("\n")
        
        # Overall trial type statistics
        f.write("OVERALL TRIAL TYPE STATISTICS:\n")
        f.write("-" * 35 + "\n")
        
        all_trial_types = Counter()
        for trial in trials:
            all_trial_types[trial.get('Trial_Type', 'unknown')] += 1
        
        for trial_type, count in all_trial_types.most_common():
            percentage = 100.0 * count / len(trials)
            f.write("%s: %d trials (%.1f%%)\n" % (trial_type, count, percentage))
        
        f.write("\n")
        
        # Oddball analysis
        oddball_types = ['orientation_45', 'orientation_90', 'halt', 'omission', 'jitter']
        oddball_counts = {ot: all_trial_types[ot] for ot in oddball_types if ot in all_trial_types}
        
        if oddball_counts:
            f.write("ODDBALL ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            total_oddballs = sum(oddball_counts.values())
            f.write("Total Oddball Events: %d\n" % total_oddballs)
            
            for oddball_type, count in oddball_counts.items():
                percentage = 100.0 * count / len(trials)
                f.write("%s: %d events (%.1f%% of all trials)\n" % (
                    oddball_type, count, percentage))
            
            f.write("Oddball Rate: %.1f events per minute\n" % (total_oddballs / total_duration))
    
    print("Saved summary: %s" % summary_path)

def main():
    """Main function to analyze all example stimulus tables."""
    
    parser = argparse.ArgumentParser(
        description="Analyze stimulus tables and create visualizations"
    )
    parser.add_argument('--session-type', 
                       help='Specific session type to analyze (default: analyze all)')
    parser.add_argument('--output-dir', default='analysis_plots',
                       help='Directory to save plots and analysis (default: analysis_plots)')
    
    args = parser.parse_args()
    
    # Find example files in the current directory (since script is now in examples/)
    examples_dir = os.path.dirname(__file__)
    
    print("Looking for example files in: %s" % examples_dir)
    
    # Get list of example files to analyze
    example_files = []
    
    if args.session_type:
        # Analyze specific session type
        filename = '%s_example.csv' % args.session_type
        filepath = os.path.join(examples_dir, filename)
        if os.path.exists(filepath):
            example_files.append((args.session_type, filepath))
        else:
            print("Example file not found: %s" % filepath)
            return
    else:
        # Analyze all example files
        for filename in os.listdir(examples_dir):
            if filename.endswith('_example.csv'):
                session_type = filename.replace('_example.csv', '')
                filepath = os.path.join(examples_dir, filename)
                example_files.append((session_type, filepath))
    
    if not example_files:
        print("No example files found in %s" % examples_dir)
        return
    
    print("Analyzing %d stimulus tables..." % len(example_files))
    print()
    
    # Analyze each file
    for session_type, filepath in example_files:
        print("Analyzing %s..." % session_type)
        
        # Load stimulus table
        trials = load_stimulus_table(filepath)
        
        if not trials:
            print("  Skipping %s (no trials loaded)" % session_type)
            continue
        
        # Create visualization
        try:
            fig = plot_session_structure(trials, session_type, args.output_dir)
            plt.close(fig)  # Close to save memory
        except Exception as e:
            print("  Error creating plot for %s: %s" % (session_type, e))
        
        # Create summary statistics
        try:
            create_summary_statistics(trials, session_type, args.output_dir)
        except Exception as e:
            print("  Error creating summary for %s: %s" % (session_type, e))
        
        print("  Completed analysis for %s" % session_type)
        print()
    
    print("Analysis complete! Check '%s' directory for results." % args.output_dir)

if __name__ == "__main__":
    main()
