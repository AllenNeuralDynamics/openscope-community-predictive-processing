#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate NWB file by creating plots directly from the file

This script reads a SLAP2 NWB file and creates validation plots similar to those
created by the original load_slap2.py script, but directly from the NWB file
using pynwb instead of the original SLAP2 code.

Author: GitHub Copilot (based on original SLAP2 code by Jerome Lecoq)
"""

import os
import re
import sys
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import colors as mcolors
import argparse
from matplotlib.colors import LinearSegmentedColormap

# Import PyNWB modules
from pynwb import NWBHDF5IO
from pynwb.image import ImageSeries
from pynwb.ophys import TwoPhotonSeries, OpticalChannel, ImageSegmentation, Fluorescence, DfOverF, RoiResponseSeries

# The SLAP2 NWB layout changed across acquisition periods (all present on DANDI 001424):
#   - early 2025 sessions: summary images in acquisition, one 'stimulus_presentations'
#     table, a DfOverF container named 'dff', image masks
#   - mid/late 2025 sessions: summary images in processing/ophys, stimulus tables named
#     by block ('gratings', 'standard_control', ...), dF/F stored as 'DMD<n>_dFF[_<channel>]'
#     inside per-DMD Fluorescence containers, pixel masks, continuous (not trial) recording
# The helpers below look the data up by type rather than by a fixed name.


def get_stimulus_table(nwbfile):
    """
    Return all stimulus presentations as one DataFrame (or None)

    Files with a 'stimulus_presentations' table use it as is. Otherwise every
    TimeIntervals table in nwbfile.intervals is treated as a stimulus block and the
    tables are concatenated, with the table name kept in a 'stimulus_block' column.
    """
    intervals = nwbfile.intervals
    if intervals is None or len(intervals) == 0:
        return None
    if 'stimulus_presentations' in intervals:
        return intervals['stimulus_presentations'].to_dataframe()

    tables = []
    for name, table in intervals.items():
        if name in ('trials', 'epochs', 'invalid_times'):
            continue
        df = table.to_dataframe()
        df['stimulus_block'] = name
        tables.append(df)
    if not tables:
        return None
    return pd.concat(tables).sort_values('start_time').reset_index(drop=True)


def get_summary_images(nwbfile):
    """
    Return the single-frame summary images (mean / activity images) by name

    Early files keep them in acquisition, later files in processing/ophys.
    """
    containers = [nwbfile.acquisition]
    if 'ophys' in nwbfile.processing:
        containers.append(nwbfile.processing['ophys'].data_interfaces)

    summary_images = {}
    for container in containers:
        for name, obj in container.items():
            if isinstance(obj, ImageSeries) and not isinstance(obj, TwoPhotonSeries):
                summary_images[name] = obj
    return summary_images


def get_image_frame(img_series):
    """Return the first frame of an ImageSeries as a 2D array"""
    # Some files store the frame as (height, width, 1)
    return np.squeeze(np.asarray(img_series.data[0]))


def get_trace_series(ophys):
    """
    Find the ROI traces to plot

    Returns (trace_type, {series_name: RoiResponseSeries}). dF/F is preferred: either
    the series of a DfOverF container (whatever its name) or series named '*dFF*' kept
    inside a Fluorescence container. Falls back to the other Fluorescence series.
    """
    dff_series = {}
    fluo_series = {}
    for interface in ophys.data_interfaces.values():
        if isinstance(interface, DfOverF):
            dff_series.update(interface.roi_response_series)
        elif isinstance(interface, Fluorescence):
            for name, series in interface.roi_response_series.items():
                if 'dff' in name.lower():
                    dff_series[name] = series
                else:
                    fluo_series[name] = series

    if dff_series:
        return 'DfOverF', dff_series
    if fluo_series:
        return 'Fluorescence', fluo_series
    return None, {}


def get_timestamps(series):
    """Return the timestamps of a TimeSeries, from timestamps or starting_time/rate"""
    if series.timestamps is not None:
        return np.asarray(series.timestamps[:])
    n = series.data.shape[0]
    return series.starting_time + np.arange(n) / series.rate


def load_nwb_file(nwb_path):
    """
    Load an NWB file
    
    Parameters
    ----------
    nwb_path : str
        Path to the NWB file
        
    Returns
    -------
    nwbfile : NWBFile
        The loaded NWB file
    io : NWBHDF5IO
        The I/O object for the NWB file (needed to close the file properly)
    """
    io = NWBHDF5IO(nwb_path, 'r')
    nwbfile = io.read()
    return nwbfile, io


def validate_nwb(nwb_path, output_dir=None, window_start=None, window_length=30.0):
    """
    Validate an NWB file by creating plots
    
    Parameters
    ----------
    nwb_path : str
        Path to the NWB file
    output_dir : str, optional
        Path to the output directory for plots
    window_start : float, optional
        Start time (s) of the zoomed trace plot for continuous recordings
        (default: first stimulus onset)
    window_length : float, optional
        Length (s) of the zoomed trace plot for continuous recordings
        
    Returns
    -------
    output_dir : str
        Path to the output directory where plots were saved
    """
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(nwb_path), 'validation')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load NWB file
    nwbfile, io = load_nwb_file(nwb_path)
    
    try:
        # 1. Plot metadata and basic information
        plot_metadata(nwbfile, output_dir)
        
        # 2. Plot stimulus information
        plot_stimulus_info(nwbfile, output_dir)
        
        # 3. Plot summary images
        plot_summary_images(nwbfile, output_dir)
        
        # 4. Plot traces with stimulus overlays
        plot_traces_with_stimuli(nwbfile, output_dir, window_start, window_length)
        
        # 5. Plot segmentation masks
        plot_segmentation_masks(nwbfile, output_dir)
        
        print(f"Validation plots saved to {output_dir}")
    finally:
        # Close the NWB file
        io.close()
    
    return output_dir


def plot_metadata(nwbfile, output_dir):
    """
    Plot metadata from the NWB file
    
    Parameters
    ----------
    nwbfile : NWBFile
        The NWB file
    output_dir : str
        Path to the output directory for plots
    """
    # Create figure for metadata
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axis('off')
    
    # Collect metadata
    metadata = [
        f"File ID: {nwbfile.identifier}",
        f"Session Description: {nwbfile.session_description}",
        f"Session Start Time: {nwbfile.session_start_time}",
        f"Experimenter(s): {', '.join(nwbfile.experimenter) if isinstance(nwbfile.experimenter, (list, tuple)) else nwbfile.experimenter}",
        f"Lab: {nwbfile.lab}",
        f"Institution: {nwbfile.institution}",
    ]
    
    # Add subject information if available
    if nwbfile.subject is not None:
        metadata.extend([
            f"Subject ID: {nwbfile.subject.subject_id}",
            f"Species: {nwbfile.subject.species}",
        ])
        
        # Add optional subject fields if they exist
        if hasattr(nwbfile.subject, 'age') and nwbfile.subject.age is not None:
            metadata.append(f"Age: {nwbfile.subject.age}")
        if hasattr(nwbfile.subject, 'sex') and nwbfile.subject.sex is not None:
            metadata.append(f"Sex: {nwbfile.subject.sex}")
        if hasattr(nwbfile.subject, 'genotype') and nwbfile.subject.genotype is not None:
            metadata.append(f"Genotype: {nwbfile.subject.genotype}")
    
    # Add notes if available
    if hasattr(nwbfile, 'notes') and nwbfile.notes is not None:
        metadata.append(f"Notes: {nwbfile.notes}")
    
    # Display metadata
    ax.text(0.05, 0.95, '\n'.join(metadata), va='top', fontsize=12, transform=ax.transAxes)
    
    # Save figure
    plt.title("NWB File Metadata")
    plt.savefig(os.path.join(output_dir, 'metadata.png'), dpi=150, bbox_inches='tight')
    plt.close(fig)


def plot_stimulus_info(nwbfile, output_dir):
    """
    Plot stimulus information from the NWB file
    
    Parameters
    ----------
    nwbfile : NWBFile
        The NWB file
    output_dir : str
        Path to the output directory for plots
    """
    # Get stimulus presentations
    try:
        stim_df = get_stimulus_table(nwbfile)
        if stim_df is None:
            print("Warning: No stimulus tables found in NWB file")
            return
        
        # Plot orientations (column is 'orientation' or 'Orientation' depending on the file)
        orientation_col = next((col for col in stim_df.columns if col.lower() == 'orientation'), None)
        if orientation_col is not None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(stim_df['start_time'], stim_df[orientation_col], 'bo-', markersize=5)
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Orientation (degrees)')
            ax.set_title('Stimulus Orientations')
            ax.grid(True)
            plt.savefig(os.path.join(output_dir, 'stimulus_orientations.png'), dpi=150, bbox_inches='tight')
            plt.close(fig)
        
        # Plot other (numeric) parameters if available
        param_columns = [col for col in stim_df.columns if col.lower() not in
                        ['start_time', 'stop_time', 'trial', 'id', 'tags']
                        and pd.api.types.is_numeric_dtype(stim_df[col])]
        
        if param_columns:
            fig, axs = plt.subplots(len(param_columns), 1, figsize=(10, 3*len(param_columns)), sharex=True)
            if len(param_columns) == 1:
                axs = [axs]  # Ensure axs is a list-like for consistency
                
            for i, param in enumerate(param_columns):
                if param in stim_df.columns and not stim_df[param].isna().all():
                    axs[i].plot(stim_df['start_time'], stim_df[param], 'o-', markersize=5)
                    axs[i].set_ylabel(param)
                    axs[i].grid(True)
            
            axs[-1].set_xlabel('Time (s)')
            plt.suptitle('Stimulus Parameters')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'stimulus_parameters.png'), dpi=150, bbox_inches='tight')
            plt.close(fig)
        
        # Plot stimulus timing
        # (collections rather than one artist per stimulus: later sessions have >50,000)
        fig, ax = plt.subplots(figsize=(10, 6))
        starts = stim_df['start_time'].to_numpy()
        stops = stim_df['stop_time'].to_numpy()
        ax.broken_barh(list(zip(starts, stops - starts)), (0, 1), alpha=0.3, color='gray')
        ax.vlines(starts, 0, 1, color='r', linestyle='-', linewidth=1, alpha=0.7)
        ax.vlines(stops, 0, 1, color='b', linestyle='-', linewidth=1, alpha=0.7)
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Stimulus')
        ax.set_title('Stimulus Timing')
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.grid(True, axis='x')
        plt.savefig(os.path.join(output_dir, 'stimulus_timing.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)
        
    except (KeyError, AttributeError) as e:
        print(f"Warning: Could not plot stimulus information: {e}")


def plot_summary_images(nwbfile, output_dir):
    """
    Plot summary images from the NWB file
    
    Parameters
    ----------
    nwbfile : NWBFile
        The NWB file
    output_dir : str
        Path to the output directory for plots
    """
    # Find all summary ImageSeries (acquisition or processing/ophys)
    summary_images = get_summary_images(nwbfile)
    
    if summary_images:
        # Create figure for summary images
        num_images = len(summary_images)
        fig_cols = min(3, num_images)
        fig_rows = (num_images + fig_cols - 1) // fig_cols  # Ceiling division
        
        fig, axs = plt.subplots(fig_rows, fig_cols, figsize=(5*fig_cols, 4*fig_rows))
        if num_images == 1:
            axs = np.array([axs])  # Make axs indexable for single subplot
        axs = axs.flatten()
        
        for i, (name, img_series) in enumerate(summary_images.items()):
            if i < len(axs):
                # Get the image data (expecting a 3D array with time as first dimension)
                img_data = get_image_frame(img_series)  # Take first time point
                
                # Display the image
                axs[i].imshow(img_data, cmap='viridis')
                axs[i].set_title(name)
                axs[i].axis('off')
        
        # Hide unused subplots
        for j in range(i + 1, len(axs)):
            axs[j].axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'summary_images.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        print("Warning: No summary images found in NWB file")


def plot_traces_with_stimuli(nwbfile, output_dir, window_start=None, window_length=30.0):
    """
    Plot traces with stimulus overlays from the NWB file
    
    Parameters
    ----------
    nwbfile : NWBFile
        The NWB file
    output_dir : str
        Path to the output directory for plots
    window_start : float, optional
        Start time (s) of the zoomed plot for continuous recordings
    window_length : float, optional
        Length (s) of the zoomed plot for continuous recordings
    """
    # Get stimulus presentations
    try:
        stim_df = get_stimulus_table(nwbfile)
        if stim_df is None:
            stim_df = pd.DataFrame(columns=['start_time', 'stop_time'])
        
        # Get ophys module
        ophys = nwbfile.processing.get('ophys')
        if ophys is None:
            print("Warning: No ophys module found in NWB file")
            return
        
        # Create colormap for stimulus parameters
        base_colors = list(mcolors.TABLEAU_COLORS.values())
        
        # Try to get DfOverF data first (preferred), fallback to Fluorescence
        trace_type, trace_series = get_trace_series(ophys)
        if not trace_series:
            print("Warning: No DfOverF or Fluorescence data found in NWB file")
            return
        
        # Get ROI response series names (per trial for recordings made in trial mode)
        roi_series_names = list(trace_series.keys())
        
        # Group series by trial and DMD (assuming naming convention like 'Trial{trial}_DMD{dmd}')
        trials_dmd = {}
        for name in roi_series_names:
            parts = name.split('_')
            trial_part = [p for p in parts if p.startswith('Trial')]
            dmd_part = [p for p in parts if p.startswith('DMD')]
            
            if trial_part and dmd_part:
                trial_num = int(trial_part[0].replace('Trial', ''))
                dmd_num = int(dmd_part[0].replace('DMD', ''))
                
                if trial_num not in trials_dmd:
                    trials_dmd[trial_num] = {}
                
                trials_dmd[trial_num][dmd_num] = name
        
        # Continuous recordings: one series per DMD (and channel) for the whole session
        if not trials_dmd:
            plot_continuous_traces(trace_series, trace_type, stim_df, output_dir,
                                   window_start, window_length)
            return
        
        # Keep track of previous parameter values for visual cues
        previous_values = {}
        param_colors = {}
        
        # Plot traces for each trial
        for trial_num, dmds in sorted(trials_dmd.items()):
            # Create figure for this trial
            fig = plt.figure(figsize=(10, 8))
            
            # For each DMD
            for i, (dmd_num, series_name) in enumerate(sorted(dmds.items())):
                # Get the ROI response series
                roi_series = trace_series[series_name]
                
                # Create subplot for this DMD
                ax = plt.subplot(len(dmds), 1, i+1)
                
                # Get trace data and timestamps
                trace_data = roi_series.data[:]  # Shape should be (time, ROI)
                timestamps = roi_series.timestamps[:]
                
                # Get trial start and end times
                trial_start = timestamps[0]
                trial_end = timestamps[-1]
                
                # Get stimuli during this trial
                trial_stims = stim_df[(stim_df['start_time'] >= trial_start) & 
                                     (stim_df['start_time'] <= trial_end)]
                
                # Plot heatmap of traces
                sns.heatmap(trace_data.T, ax=ax, cmap='Greens', 
                           vmin=0, vmax=2)  # Same scale as in load_slap2.py
                
                # Get time tick positions and labels
                num_timepoints = trace_data.shape[0]
                num_ticks = 5
                tick_indices = np.linspace(0, num_timepoints - 1, num_ticks, dtype=int)
                tick_labels = [f"{timestamps[i]:.1f}" for i in tick_indices]
                
                # Set axis labels
                if i == len(dmds) - 1:  # Bottom subplot
                    ax.set_xlabel(f"Time (s) - trial_{trial_num}")
                    ax.set_xticks(tick_indices)
                    ax.set_xticklabels(tick_labels)
                else:
                    ax.set_xticklabels([])
                    ax.set_xticks([])
                
                ax.set_ylabel(f"Synapse # - DMD {dmd_num}")
                
                # Draw vertical bars at stimulus times
                for _, stim_row in trial_stims.iterrows():
                    # Calculate position in the plot
                    stim_time = stim_row['start_time']
                    rel_time = stim_time - trial_start
                    
                    # Convert to x-index in the plot
                    x_index = int(rel_time / (trial_end - trial_start) * (num_timepoints - 1))
                    x_index = max(0, min(x_index, num_timepoints - 1))  # Ensure within bounds
                    
                    # Draw vertical line
                    ax.axvline(x=x_index, color='red', linestyle='-', linewidth=0.5)
                    
                    # Only annotate in the top subplot for clarity
                    if i == 0:
                        # Format stimulus parameters
                        y_offset = -1.5
                        x_offset = 0
                        prev_y_position = 1
                        
                        # Get parameters for this stimulus
                        for param in stim_row.index:
                            if param not in ['start_time', 'stop_time', 'id', 'tags', 'trial']:
                                val = stim_row[param]
                                if pd.notnull(val):  # Skip NaN values
                                    # Format value
                                    try:
                                        formatted_val = f"{float(val):.1g}"
                                    except:
                                        formatted_val = str(val)
                                    
                                    # Get color for this parameter
                                    if param not in param_colors:
                                        param_colors[param] = base_colors[len(param_colors) % len(base_colors)]
                                    
                                    # Check if value has changed
                                    has_changed = previous_values.get(param) != val
                                    previous_values[param] = val
                                    
                                    # Set text properties
                                    color = param_colors[param] if not has_changed else 'black'
                                    weight = 'normal' if not has_changed else 'bold'
                                    
                                    # Adjust y position
                                    adjusted_y_position = prev_y_position + y_offset
                                    prev_y_position = adjusted_y_position
                                    
                                    # Add text
                                    ax.text(x_index + x_offset, adjusted_y_position, 
                                           f"{param}={formatted_val}",
                                           rotation=45,
                                           color=color,
                                           fontsize=8,
                                           fontweight=weight,
                                           ha='left',
                                           va='bottom',
                                           clip_on=False)
            
            # Set overall title and layout
            plt.suptitle(f"Trial {trial_num} - {trace_type}")
            plt.tight_layout()
            
            # Save figure
            plt.savefig(os.path.join(output_dir, f'trial_{trial_num}_traces.png'), dpi=150, bbox_inches='tight')
            plt.close(fig)
            
    except (KeyError, AttributeError) as e:
        print(f"Warning: Could not plot traces: {e}")


def bin_traces(data, n_bins, chunk_bins=200):
    """
    Average a (time, ROI) dataset into at most n_bins consecutive time bins

    The dataset is read in chunks, so a whole session never has to be in memory.
    Returns the binned array (bins, ROI) and the number of samples per bin.
    """
    n_samples = data.shape[0]
    n_rois = data.shape[1] if len(data.shape) > 1 else 1
    per_bin = max(1, -(-n_samples // n_bins))  # ceil, so there are at most n_bins bins
    n_bins = n_samples // per_bin
    binned = np.empty((n_bins, n_rois))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)  # all-NaN bins
        for b0 in range(0, n_bins, chunk_bins):
            b1 = min(b0 + chunk_bins, n_bins)
            block = np.asarray(data[b0 * per_bin:b1 * per_bin], dtype=float)
            binned[b0:b1] = np.nanmean(block.reshape(b1 - b0, per_bin, n_rois), axis=1)
    return binned, per_bin


def robust_limits(values):
    """Return (vmin, vmax) from the 1st and 99th percentiles, or (None, None)"""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        vmin, vmax = np.nanpercentile(values, [1, 99])
    if not (np.isfinite(vmin) and np.isfinite(vmax)) or vmin == vmax:
        return None, None
    return vmin, vmax


def plot_continuous_traces(trace_series, trace_type, stim_df, output_dir,
                           window_start=None, window_length=30.0, max_bins=2000):
    """
    Plot traces of a continuously recorded session (no per-trial series)

    For each channel (e.g. 'dFF', or 'dFF_green' / 'dFF_red') two figures are saved,
    with one heatmap per DMD: the whole session averaged into at most max_bins time
    bins, with stimulus block changes marked, and a window_length-second window at
    full resolution (from window_start, default the first stimulus onset) with
    stimulus onsets coloured by orientation.
    
    Parameters
    ----------
    trace_series : dict
        {series_name: RoiResponseSeries}, series names containing 'DMD<n>'
    trace_type : str
        Label for the colour bar
    stim_df : pandas.DataFrame
        Stimulus presentations (see get_stimulus_table)
    output_dir : str
        Path to the output directory for plots
    """
    # Group series by channel, then DMD: 'DMD1_dFF_green' -> channel 'dFF_green', DMD 1
    channels = {}
    for name, series in trace_series.items():
        match = re.search(r'DMD(\d+)', name)
        dmd_num = int(match.group(1)) if match else 0
        channel = re.sub(r'_?DMD\d+_?', '', name) or name
        channels.setdefault(channel, {})[dmd_num] = series
    
    # Stimulus block changes ('stimulus_block' only exists for files with per-block tables)
    block_starts = []
    if 'stimulus_block' in stim_df.columns and len(stim_df) > 0:
        changed = stim_df['stimulus_block'] != stim_df['stimulus_block'].shift()
        block_starts = list(zip(stim_df.loc[changed, 'start_time'], stim_df.loc[changed, 'stimulus_block']))
    
    # Window for the full-resolution plot
    if window_start is None and len(stim_df) > 0:
        window_start = stim_df['start_time'].min()
    orientation_col = next((col for col in stim_df.columns if col.lower() == 'orientation'), None)
    
    for channel, dmds in sorted(channels.items()):
        dmd_items = sorted(dmds.items())
        timestamps = {dmd_num: get_timestamps(series) for dmd_num, series in dmd_items}
        
        # 1. Whole session, binned (shared time axis, so DMDs recorded over different spans show it)
        fig, axs = plt.subplots(len(dmd_items), 1, figsize=(14, 3 * len(dmd_items)), squeeze=False, sharex=True)
        for i, (dmd_num, series) in enumerate(dmd_items):
            ax = axs[i, 0]
            binned, per_bin = bin_traces(series.data, max_bins)
            bin_times = timestamps[dmd_num][:binned.shape[0] * per_bin].reshape(-1, per_bin).mean(axis=1)
            vmin, vmax = robust_limits(binned)
            im = ax.imshow(binned.T, aspect='auto', cmap='Greens', vmin=vmin, vmax=vmax,
                           interpolation='nearest',
                           extent=[bin_times[0], bin_times[-1], binned.shape[1] - 0.5, -0.5])
            fig.colorbar(im, ax=ax, label=trace_type)
            ax.set_ylabel(f"Synapse # - DMD {dmd_num}\n({per_bin} samples per bin)")
            
            for start, block in block_starts:
                ax.axvline(start, color='k', linestyle='--', linewidth=0.8)
                if i == 0 and len(block_starts) <= 30:
                    ax.text(start, -0.5, f" {block}", rotation=30, fontsize=8,
                            ha='left', va='bottom', clip_on=False)
        axs[-1, 0].set_xlim(min(ts[0] for ts in timestamps.values()), max(ts[-1] for ts in timestamps.values()))
        axs[-1, 0].set_xlabel("Time (s)")
        plt.suptitle(f"{channel} - whole session")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'traces_{channel}_session.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # 2. Full-resolution window with stimulus onsets
        if window_start is None:
            continue
        t0, t1 = window_start, window_start + window_length
        window_stims = stim_df[(stim_df['start_time'] >= t0) & (stim_df['start_time'] <= t1)]
        
        # One colour per orientation in the window (grey when the orientation is missing)
        onset_colors = ['red'] * len(window_stims)
        legend_handles = []
        if orientation_col is not None and len(window_stims) > 0:
            values = sorted(window_stims[orientation_col].dropna().unique())
            base_colors = plt.cm.tab20.colors
            value_colors = {v: base_colors[k % len(base_colors)] for k, v in enumerate(values)}
            onset_colors = [value_colors.get(v, 'grey') if pd.notnull(v) else 'grey'
                            for v in window_stims[orientation_col]]
            legend_handles = [plt.Line2D([0], [0], color=c, label=f"{orientation_col}={v:.4g}")
                              for v, c in value_colors.items()]
        
        fig, axs = plt.subplots(len(dmd_items), 1, figsize=(14, 3 * len(dmd_items)), squeeze=False)
        for i, (dmd_num, series) in enumerate(dmd_items):
            ax = axs[i, 0]
            ts = timestamps[dmd_num]
            i0, i1 = np.searchsorted(ts, [t0, t1])
            if i1 - i0 < 2:
                ax.set_title(f"DMD {dmd_num}: no samples between {t0:.1f} and {t1:.1f} s", fontsize=9)
                continue
            window = np.asarray(series.data[i0:i1], dtype=float)
            window = window.reshape(window.shape[0], -1)
            vmin, vmax = robust_limits(window)
            im = ax.imshow(window.T, aspect='auto', cmap='Greens', vmin=vmin, vmax=vmax,
                           interpolation='nearest',
                           extent=[ts[i0], ts[i1 - 1], window.shape[1] - 0.5, -0.5])
            fig.colorbar(im, ax=ax, label=trace_type)
            ax.set_xlim(t0, t1)
            ax.set_ylabel(f"Synapse # - DMD {dmd_num}")
            for start, color in zip(window_stims['start_time'], onset_colors):
                ax.axvline(start, color=color, linestyle='-', linewidth=0.8)
        if legend_handles:
            axs[0, 0].legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.12, 1),
                             fontsize=8, title='Stimulus onsets')
        axs[-1, 0].set_xlabel("Time (s)")
        plt.suptitle(f"{channel} - {t0:.1f} to {t1:.1f} s")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'traces_{channel}_window.png'), dpi=150, bbox_inches='tight')
        plt.close(fig)


def get_reference_shape(nwbfile, plane_name, plane_seg):
    """
    Return the (height, width) of a summary image of the same DMD as a plane
    segmentation (matched on the 'DMD<n>' token of the names), or None
    """
    names = [plane_name]
    if getattr(plane_seg, 'imaging_plane', None) is not None:
        names.append(plane_seg.imaging_plane.name)
    tokens = {token for name in names for token in re.findall(r'DMD\d+', name)}
    for img_name, img_series in get_summary_images(nwbfile).items():
        if tokens & set(re.findall(r'DMD\d+', img_name)):
            return get_image_frame(img_series).shape[:2]
    return None


def plot_segmentation_masks(nwbfile, output_dir):
    """
    Plot segmentation masks from the NWB file
    
    Parameters
    ----------
    nwbfile : NWBFile
        The NWB file
    output_dir : str
        Path to the output directory for plots
    """
    # Get ophys module
    ophys = nwbfile.processing.get('ophys')
    if ophys is None:
        print("Warning: No ophys module found in NWB file")
        return
    
    # Check if ImageSegmentation exists
    if 'ImageSegmentation' not in ophys.data_interfaces:
        print("Warning: No ImageSegmentation found in NWB file")
        return
    
    # Get ImageSegmentation interface
    img_seg = ophys.data_interfaces['ImageSegmentation']
    
    # Create a folder for segmentation masks
    masks_dir = os.path.join(output_dir, 'segmentation_masks')
    os.makedirs(masks_dir, exist_ok=True)
    
    # Process each plane's segmentation
    for plane_name, plane_seg in img_seg.plane_segmentations.items():
        print(f"Processing segmentation for plane: {plane_name}")
        
        # Get ROI IDs and image mask
        roi_ids = plane_seg.id.data[:]
        roi_mask_list = []
        
        # Check which fields are available for the ROIs
        available_fields = []
        if hasattr(plane_seg, 'image_mask') and plane_seg.image_mask is not None:
            available_fields.append('image_mask')
        if hasattr(plane_seg, 'pixel_mask') and plane_seg.pixel_mask is not None:
            available_fields.append('pixel_mask')
        if hasattr(plane_seg, 'voxel_mask') and plane_seg.voxel_mask is not None:
            available_fields.append('voxel_mask')
        
        if not available_fields:
            print(f"Warning: No mask data found for plane {plane_name}")
            continue
        
        # Create a combined mask for all ROIs in this plane
        if 'image_mask' in available_fields:
            # If image_mask is available, we can directly get the mask dimensions
            first_mask = plane_seg.image_mask[0]
            height, width = first_mask.shape
            combined_mask = np.zeros((height, width), dtype=np.int32)
            
            # Collect all masks for individual visualizations
            for i, roi_id in enumerate(roi_ids):
                mask = plane_seg.image_mask[i]
                roi_mask_list.append(mask)
                # Add to combined mask with ROI index as the value
                combined_mask[mask > 0] = i + 1  # +1 to avoid 0 (background)
        
        elif 'pixel_mask' in available_fields:
            # Pixel masks are lists of (x, y, weight). Which of x / y is the image row
            # differs between files, so use the ordering that fits the summary image of
            # the same DMD (x as the row index when both fit, or when there is no image).
            # (plane_seg.pixel_mask is the flat list of all pixels; plane_seg['pixel_mask'][i]
            # gives the pixels of ROI i)
            pixel_masks = [np.asarray([tuple(pixel) for pixel in plane_seg['pixel_mask'][i]],
                                      dtype=float).reshape(-1, 3)
                           for i in range(len(roi_ids))]
            all_pixels = np.concatenate(pixel_masks)
            max_x, max_y = int(all_pixels[:, 0].max()), int(all_pixels[:, 1].max())
            
            row_col = (0, 1)  # x is the row index
            height, width = max_x + 1, max_y + 1
            ref_shape = get_reference_shape(nwbfile, plane_name, plane_seg)
            if ref_shape is not None:
                if max_x < ref_shape[0] and max_y < ref_shape[1]:
                    height, width = ref_shape
                elif max_y < ref_shape[0] and max_x < ref_shape[1]:
                    row_col = (1, 0)  # y is the row index
                    height, width = ref_shape
                    print(f"Note: pixel_mask of {plane_name} only fits its summary image with y as the row index")
            
            # Create empty combined mask
            combined_mask = np.zeros((height, width), dtype=np.int32)
            
            # Fill in the masks
            for i, roi_id in enumerate(roi_ids):
                pixels = pixel_masks[i]
                rows = pixels[:, row_col[0]].astype(int)
                cols = pixels[:, row_col[1]].astype(int)
                individual_mask = np.zeros((height, width), dtype=np.float32)
                individual_mask[rows, cols] = pixels[:, 2]
                combined_mask[rows, cols] = i + 1  # +1 to avoid 0 (background)
                roi_mask_list.append(individual_mask)
        
        # Create a colormap for visualization
        colors = plt.cm.viridis(np.linspace(0, 1, len(roi_ids) + 1))
        custom_cmap = LinearSegmentedColormap.from_list('custom_cmap', colors)
        
        # Plot combined masks
        plt.figure(figsize=(10, 10))
        plt.imshow(combined_mask, cmap=custom_cmap)
        plt.colorbar(label='ROI Index')
        plt.title(f'All ROIs - {plane_name} ({len(roi_ids)} ROIs)')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(masks_dir, f'{plane_name}_all_masks.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        # Plot individual masks - arrange in a grid
        rows_per_figure = 5
        cols_per_figure = 6
        masks_per_figure = rows_per_figure * cols_per_figure
        
        # Calculate number of figures needed
        num_figures = (len(roi_mask_list) + masks_per_figure - 1) // masks_per_figure
        
        for fig_idx in range(num_figures):
            start_idx = fig_idx * masks_per_figure
            end_idx = min(start_idx + masks_per_figure, len(roi_mask_list))
            
            fig, axs = plt.subplots(rows_per_figure, cols_per_figure, 
                                   figsize=(15, 12), 
                                   gridspec_kw={'wspace': 0.1, 'hspace': 0.1})
            axs = axs.flatten()
            
            for i, mask_idx in enumerate(range(start_idx, end_idx)):
                axs[i].imshow(roi_mask_list[mask_idx], cmap='viridis')
                axs[i].set_title(f'ROI {roi_ids[mask_idx]}', fontsize=8)
                axs[i].axis('off')
            
            # Hide unused subplots
            for j in range(end_idx - start_idx, masks_per_figure):
                axs[j].axis('off')
                axs[j].set_visible(False)
            
            plt.suptitle(f'{plane_name} - ROI Masks (Page {fig_idx+1}/{num_figures})', fontsize=14)
            plt.tight_layout()
            plt.savefig(os.path.join(masks_dir, f'{plane_name}_masks_page{fig_idx+1}.png'), dpi=150, bbox_inches='tight')
            plt.close()
        
        # Create a visualization with ROI outlines overlaid on each other
        plt.figure(figsize=(10, 10))
        
        # Create a colored visualization where ROIs are semi-transparent
        overlay = np.zeros((height, width, 4))  # RGBA array
        
        for i, mask in enumerate(roi_mask_list):
            # Get a distinct color for this ROI
            color_idx = i % len(colors)
            r, g, b, a = colors[color_idx]
            
            # Create a mask for this ROI with its color
            roi_rgba = np.zeros((height, width, 4))
            roi_rgba[mask > 0, 0] = r
            roi_rgba[mask > 0, 1] = g
            roi_rgba[mask > 0, 2] = b
            roi_rgba[mask > 0, 3] = 0.3  # Semi-transparent
            
            # Add to overlay
            overlay[roi_rgba[:, :, 3] > 0] = roi_rgba[roi_rgba[:, :, 3] > 0]
            
            # Draw outline (on the binary mask: weights are not always within [0, 1])
            from scipy import ndimage
            edges = (mask > 0) & ~ndimage.binary_erosion(mask > 0)
            y_indices, x_indices = np.where(edges)
            plt.scatter(x_indices, y_indices, s=0.5, color=(r, g, b), alpha=0.8)
        
        plt.imshow(overlay)
        plt.title(f'ROI Outlines - {plane_name} ({len(roi_ids)} ROIs)')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(masks_dir, f'{plane_name}_roi_outlines.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
        # If summary images are available, plot ROI outlines on top of summary images
        # (only images of the same DMD when the names say which DMD they belong to)
        summary_images = get_summary_images(nwbfile)
        plane_dmds = set(re.findall(r'DMD\d+', plane_name))
        if plane_dmds:
            summary_images = {name: img for name, img in summary_images.items()
                              if plane_dmds & set(re.findall(r'DMD\d+', name))}
        
        for img_name, img_series in summary_images.items():
            try:
                # Get the image data (expecting a 3D array with time as first dimension)
                img_data = get_image_frame(img_series)  # Take first time point
                
                if img_data.shape[:2] == (height, width):  # Check if dimensions match
                    plt.figure(figsize=(10, 10))
                    plt.imshow(img_data, cmap='gray')
                    
                    # Overlay ROI outlines
                    for i, mask in enumerate(roi_mask_list):
                        # Get a distinct color for this ROI
                        color_idx = i % len(colors)
                        r, g, b, a = colors[color_idx]
                        
                        # Draw outline
                        from scipy import ndimage
                        edges = (mask > 0) & ~ndimage.binary_erosion(mask > 0)
                        y_indices, x_indices = np.where(edges)
                        plt.scatter(x_indices, y_indices, s=0.5, color=(r, g, b), alpha=0.8)
                    
                    plt.title(f'ROI Outlines on {img_name} - {plane_name}')
                    plt.axis('off')
                    plt.tight_layout()
                    plt.savefig(os.path.join(masks_dir, f'{plane_name}_roi_on_{img_name}.png'), dpi=150, bbox_inches='tight')
                    plt.close()
            except Exception as e:
                print(f"Warning: Could not overlay ROIs on {img_name}: {e}")
    
    print(f"Segmentation mask plots saved to {masks_dir}")


def main():
    parser = argparse.ArgumentParser(description='Validate NWB file by creating plots')
    parser.add_argument('--nwb', type=str, required=True, 
                        help='Path to NWB file')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory for plots (default: "validation" folder next to NWB file)')
    parser.add_argument('--window-start', type=float, default=None,
                        help='Start time (s) of the zoomed trace plot for continuous recordings '
                             '(default: first stimulus onset)')
    parser.add_argument('--window-length', type=float, default=30.0,
                        help='Length (s) of the zoomed trace plot for continuous recordings (default: 30)')
    
    args = parser.parse_args()
    
    validate_nwb(args.nwb, args.output, args.window_start, args.window_length)


if __name__ == "__main__":
    main()