# -*- coding: utf-8 -*-
"""
Created on Wed May 21 20:21:34 2025

@author: Sarah Ruediger
"""
from pathlib import Path
from pynwb import NWBHDF5IO
import numpy as np
import matplotlib.pyplot as plt
from dandi import dandiapi
import requests
from tqdm import tqdm
import warnings
from collections import Counter
from PIL import Image as PILImage
from IPython.display import Image as IPImage
from scipy.spatial.distance import pdist, squareform
import seaborn as sns
import pandas as pd
from scipy.stats import spearmanr

# =============================================================================
# =========================================================================
# Download and Visualize NWB Data from the DANDI Archive
# =========================================================================
# 
# This script performs the following steps:
# 1. Defines the DANDI dataset and file path for a given NWB file.
# 2. Checks if the file is already downloaded; if not, downloads it using the DANDI API.
# 3. Loads the NWB file using PyNWB while suppressing timezone warnings.
# 4. Extracts the stimulus presentation table from the NWB file.
# 5. Plots the orientation of the presented stimuli over time.
# 
# =============================================================================

# Set output directory
output_dir = Path('/content')
output_dir.mkdir(exist_ok=True)

# Define DANDI details
dandiset_id = "001424"
dandi_filepath = "sub-794237/sub-794237_ses-20250508T145040_image+ophys.nwb"
filename = dandi_filepath.split("/")[-1]
filepath = output_dir / filename

# Download file if not already present
if not filepath.exists():
    with dandiapi.DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id)
        asset = dandiset.get_asset_by_path(dandi_filepath)
        file_url = asset.download_url

        response = requests.get(file_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024

        with open(filepath, 'wb') as f, tqdm(
            desc=f"Downloading {filename}",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(block_size):
                f.write(data)
                bar.update(len(data))

    print(f"Downloaded file to {filepath}")
else:
    print(f"{filename} already exists.")

# Load NWB file
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, message=".*Date is missing timezone information.*")
    with NWBHDF5IO(filepath, mode="r", load_namespaces=True) as io:
        nwb = io.read()

# Extract and display the first few rows of the stimulus table
stim_table = nwb.intervals["stimulus_presentations"].to_dataframe()
print(stim_table.head(10))

# Plot orientation over time
plt.figure(figsize=(14, 4))
plt.plot(stim_table['start_time'], stim_table['orientation'], marker='o', linestyle='-')
plt.title("Orientation over Time")
plt.xlabel("Start Time (s)")
plt.ylabel("Orientation (radians)")
plt.grid(True)
plt.tight_layout()
plt.show()


# =============================================================================
# 
# ===============================================================
# Identify and Classify an 'Oddball Block' in Orientation Stimuli
# ===============================================================
# 
# Steps:
# 1. Convert stimulus orientations from radians to degrees.
# 2. Use a sliding window to detect the longest block with:
#    - ≤ 3 unique orientations
#    - One orientation dominating ≥ 80% of the time
#    - Minimum block length of 30 trials
# 3. Determine the dominant orientation in this block.
# 4. Classify each trial in the block as 'standard', 'static', 'blank', or other.
# 5. Plot and summarize the detected oddball block.
# """
# =============================================================================


# Step 1: Convert orientation from radians to degrees, wrap to [0, 180), round to int
stim_table['orientation_deg'] = (np.degrees(stim_table['orientation']) % 180).round().astype(int)
ori = stim_table['orientation_deg'].values

# Step 2: Sliding window to find longest valid oddball block
max_unique = 3              # Maximum number of unique orientations allowed
min_dom_frac = 0.8          # Minimum fraction of trials with the dominant orientation
min_block_len = 30          # Minimum block length in trials

best_start = None
best_end = None

i = 0
while i < len(ori):
    unique_ors = set()
    counts = Counter()
    j = i

    while j < len(ori):
        val = ori[j]
        counts[val] += 1
        unique_ors = set(counts.keys())

        if len(unique_ors) > max_unique:
            break  # Too many orientations — stop this window

        # Check if dominant orientation meets criteria
        dom_val, dom_count = counts.most_common(1)[0]
        total = j - i + 1
        if total >= min_block_len and (dom_count / total) >= min_dom_frac:
            if best_end is None or (j - i) > (best_end - best_start):
                best_start, best_end = i, j
        j += 1
    i += 1

# Step 3: Extract and verify the final oddball block
if best_start is None:
    raise RuntimeError("No valid low-entropy block found")

final_indices = np.arange(best_start, best_end + 1)
oddball_block = stim_table.iloc[final_indices].copy()

# Step 4: Recompute dominant orientation in the final block
dominant_ori = oddball_block['orientation_deg'].mode().iloc[0]

# Step 5: Classify stimulus type based on contrast, temporal frequency, and orientation
def classify_stim(row):
    if row['contrast'] == 0.0 and row['temporal_frequency'] == 0.0:
        return 'blank'
    elif row['temporal_frequency'] == 0.0:
        return 'static'
    elif row['orientation_deg'] == dominant_ori:
        return 'standard'
    else:
        return str(row['orientation_deg'])  # Could represent the 'oddball'

oddball_block['stim_type'] = oddball_block.apply(classify_stim, axis=1)

# Step 6: Print summary
print(f"Oddball block trials: {len(oddball_block)}")
print(f"Dominant orientation: {dominant_ori}°")
print(oddball_block['stim_type'].value_counts())

# Step 7: Plot full trial sequence and highlight oddball block
plt.figure(figsize=(14, 4))
plt.plot(stim_table['start_time'], stim_table['orientation_deg'], label='All Trials', alpha=0.5)

# Overlay the detected oddball block in red
plt.plot(oddball_block['start_time'], oddball_block['orientation_deg'], color='red', label='Oddball Block')

# Highlight transition points with vertical lines
plt.axvline(oddball_block['start_time'].iloc[0], color='green', linestyle='--', label='Oddball Start')
plt.axvline(oddball_block['start_time'].iloc[-1], color='purple', linestyle='--', label='Oddball End')

plt.xlabel("Time (s)")
plt.ylabel("Orientation (deg)")
plt.title("Transition from Tuning to Oddball Block")
plt.legend()
plt.tight_layout()
plt.grid(True)
plt.show()

# =============================================================================
# ===============================================================
# Visualize Stimulus Classes in Oddball Block
# ===============================================================
# 
# This script:
# 1. Refines stimulus classification based on orientation and temporal frequency.
# 2. Assigns color codes to different oddball types.
# 3. Plots a timeline of stimulus presentations:
#    - Standards at y=0
#    - Oddballs at y=1
#    - Vertical lines connect standard to oddball presentations.
# """
# =============================================================================

# Step 1: Refine stimulus classification
def refined_stim_class(row):
    if row['temporal_frequency'] == 0.0:
        return 'static'
    elif row['orientation_deg'] == 45:
        return '45'
    elif row['orientation_deg'] == 90:
        return '90'
    elif row['orientation_deg'] == 0:
        return 'standard'
    else:
        return 'other'

oddball_block['stim_class'] = oddball_block.apply(refined_stim_class, axis=1)

# Step 2: Define color map for key oddball types
color_map = {
    '45': 'red',
    '90': 'green',
    'static': 'blue'
}

# Step 3: Create timeline plot
plt.figure(figsize=(16, 4))

# Draw reference lines at y=0 and y=1
plt.axhline(0, color='gray', linewidth=0.5, linestyle='--')
plt.axhline(1, color='gray', linewidth=0.5, linestyle='--')

# Plot standard stimuli at y=0
standard_mask = oddball_block['stim_class'] == 'standard'
standard_idx = oddball_block[standard_mask].index
plt.scatter(standard_idx, [0]*len(standard_idx), color='gray', label='Standard (0°)', s=12)

# Plot oddballs at y=1 and connect them with lines
for stim_class, color in color_map.items():
    mask = oddball_block['stim_class'] == stim_class
    idx = oddball_block[mask].index

    # Draw connecting lines from y=0 (standard) to y=1 (oddball)
    for i in idx:
        plt.plot([i, i], [0, 1], color=color, alpha=0.4, linewidth=1)

    # Plot oddball points at y=1
    plt.scatter(idx, [1]*len(idx), color=color, label=stim_class.capitalize(), s=30)

# Final plot formatting
plt.yticks([0, 1], ['Standard', 'Oddball'])
plt.xlabel("Trial Index")
plt.title("Stimulus Timeline: Standards and Oddballs (Linked)")
plt.legend(loc='upper right')
plt.tight_layout()
plt.show()


# =============================================================================
# ===============================================================
# Visualize Image Masks and ΔF/F Heatmaps for DMD1 and DMD2
# ===============================================================
# 
# This script:
# 1. Sums and displays the ROI image masks for DMD1 and DMD2.
# 2. Visualizes the ΔF/F time series for each ROI as a heatmap.
# 3. Combines plots for DMD1 and DMD2 into subplots for direct comparison.
# """
# =============================================================================

# --- Plot summed image masks for DMD1 and DMD2 ---
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for i, dmd in enumerate([1, 2]):
    image_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']
    image_mask_sum = np.sum(image_masks, axis=0)

    im = axes[i].imshow(image_mask_sum)
    axes[i].set_title(f"DMD{dmd} Image Mask Sum")
    axes[i].axis('off')
    plt.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04, label='Mask Sum')

plt.suptitle("Summed ROI Image Masks for DMD1 and DMD2")
plt.tight_layout()
plt.show()

# --- Plot ΔF/F heatmaps for DMD1 and DMD2 ---
fig, axes = plt.subplots(2, 1, figsize=(12, 8))
for i, dmd in enumerate([1, 2]):
    dff = nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"]
    dff_data = np.array(dff.data)  # [time, ROIs]
    dff_timestamps = np.array(dff.timestamps)

    n_timestamps, n_rois = dff_data.shape
    ts_start, ts_end = dff_timestamps[0], dff_timestamps[-1]
    std = np.nanstd(dff_data)
    mean = np.nanmean(dff_data)

    im = axes[i].imshow(
        dff_data.T,
        aspect='auto',
        extent=[ts_start, ts_end, n_rois, 0],
        vmin=mean - 2 * std,
        vmax=mean + 2 * std
    )
    axes[i].set_title(f"DMD{dmd} ΔF/F Heatmap")
    axes[i].set_xlabel("Time (s)")
    axes[i].set_ylabel("ROIs")
    plt.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04, label='ΔF/F')

plt.suptitle("ΔF/F Heatmaps for DMD1 and DMD2")
plt.tight_layout()
plt.show()

def extract_oddball_responses(dff, timestamps, stim_table,
                               onset_delay=0,
                               window_duration=0.6,
                               baseline_duration=0.5):
    # """
    # Extracts z-scored ΔF/F responses aligned to stimulus onsets.

    # Parameters:
    #     dff (ndarray): NOTED 22/5/2025: ΔF data (Not ΔF/F for firs test data) array of shape [time, n_rois].
    #     timestamps (ndarray): Timepoints corresponding to the ΔF/F data.
    #     stim_table (DataFrame): Table containing stimulus metadata with 'stim_type' and 'start_time'.
    #     onset_delay (float): Time after stimulus onset to begin response window (seconds).
    #     window_duration (float): Duration of response window after onset delay (seconds).
    #     baseline_duration (float): Duration of baseline window before stimulus onset (seconds).

    # Returns:
    #     responses (dict): Nested dictionary {stim_type: {'traces': [array of z-scored responses per ROI]}}.
    #     trace_window (ndarray): Time vector relative to stimulus onset for each trace sample.
    # """

    # Determine number of time points per trace based on sampling interval
    sampling_interval = np.median(np.diff(timestamps))
    trace_len = int(np.round((baseline_duration + window_duration) / sampling_interval))
    trace_window = np.linspace(-baseline_duration, window_duration, trace_len)

    n_rois = dff.shape[1]
    responses = defaultdict(lambda: defaultdict(list))

    for _, row in stim_table.iterrows():
        stim_type = str(row['stim_type']).strip()
        if stim_type.endswith(".0"):
            stim_type = stim_type[:-2]  # Convert '45.0' -> '45'

        # Define timing for baseline and stimulus windows
        start_time = row['start_time']
        base_start = start_time - baseline_duration
        base_end = start_time
        stim_start = start_time + onset_delay
        stim_end = stim_start + window_duration

        # Convert time windows to indices
        base_idx_start, base_idx_end = np.searchsorted(timestamps, (base_start, base_end))
        stim_idx_start, stim_idx_end = np.searchsorted(timestamps, (stim_start, stim_end))

        # Ensure valid index ranges
        if stim_idx_end > stim_idx_start and base_idx_end > base_idx_start:
            baseline = dff[base_idx_start:base_idx_end]
            trace = dff[stim_idx_start:stim_idx_end]

            # Z-score both baseline and trace using baseline mean and std
            mean_base = np.nanmean(baseline, axis=0)
            std_base = np.nanstd(baseline, axis=0)
            z_baseline = (baseline - mean_base) / (std_base + 1e-10)
            z_trace = (trace - mean_base) / (std_base + 1e-10)

            # Only accept full-length traces
            if z_baseline.shape[0] + z_trace.shape[0] == trace_len:
                z_full = np.concatenate((z_baseline, z_trace), axis=0)
                responses[stim_type]['traces'].append(z_full)

    return responses, trace_window




# =============================================================================
# ===============================================================
# Main Analysis Loop: Extract and Plot Oddball Responses by ROI
# ===============================================================
# 
# This loop:
# 1. Iterates over DMD1 and DMD2 imaging planes.
# 2. Extracts z-scored ΔF/F responses aligned to stimulus onsets.
# 3. Computes and plots average response traces for each ROI and stimulus type.
# 4. Saves plots to a structured output directory.
# """
# =============================================================================

# Set analysis parameters
onset_delay = 0
window_duration = 0.6
baseline_duration = 0.5

# Create output directory for storing plots
output_dir = Path("/content/oddball_traces")
output_dir.mkdir(parents=True, exist_ok=True)

for dmd in [1, 2]:
    print(f"Processing DMD{dmd}")

    # --- Load ΔF/F data and timestamps ---
    dff_key = f"DMD{dmd}_DfOverF"
    dff = np.array(nwb.processing['ophys']['DfOverF'][dff_key].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][dff_key].timestamps)

    # --- Extract z-scored response traces aligned to oddball stimuli ---
    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=onset_delay,
        window_duration=window_duration,
        baseline_duration=baseline_duration
    )

    # --- Define stimulus conditions and colors ---
    conditions = ['standard', 'static', '45', '90']
    colors = {'standard': 'gray', 'static': 'black', '45': 'red', '90': 'green'}

    # Create subdirectory for this DMD
    dmd_dir = output_dir / f"DMD{dmd}"
    dmd_dir.mkdir(exist_ok=True)

    n_rois = dff.shape[1]

    # --- Loop over each ROI and plot mean response per condition ---
    for roi in range(n_rois):
        plt.figure(figsize=(12, 4))
        for cond in conditions:
            if cond in responses and len(responses[cond]['traces']) > 0:
                # Stack traces: [n_trials, timepoints, rois]
                traces = np.stack(responses[cond]['traces'])
                if traces.shape[0] > 0 and roi < traces.shape[2]:
                    roi_traces = traces[:, :, roi]
                    mean_trace = np.nanmean(roi_traces, axis=0)
                    plt.plot(trace_window, mean_trace, label=cond, color=colors.get(cond, 'black'))

        # Annotate and save plot
        plt.title(f"DMD{dmd} ROI {roi} – Oddball Responses")
        plt.xlabel("Time (s)")
        plt.ylabel("Z-scored ΔF")
        plt.axvline(0, color='black', linestyle='--', linewidth=1, label='Stimulus Onset')
        plt.axvline(window_duration, color='black', linestyle='--', linewidth=1, label='Stimulus Offset')
        plt.legend()
        plt.tight_layout()
        plt.savefig(dmd_dir / f"roi_{roi}_oddball_traces.png", dpi=150)
        # plt.show()
        plt.close()


# --- Image Mask Sums ---
fig = plt.figure(figsize=(10, 5))
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 0.05], wspace=0.1)
axs = [fig.add_subplot(gs[0]), fig.add_subplot(gs[1])]
cax = fig.add_subplot(gs[2])

for i, dmd in enumerate([1, 2]):
    image_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']
    image_mask_sum = np.sum(image_masks, axis=0)

    im = axs[i].imshow(image_mask_sum)
    axs[i].set_title(f"DMD{dmd} Image Mask Sum")
    axs[i].axis('off')

fig.colorbar(im, cax=cax, label='Mask Sum')
plt.tight_layout()
plt.show()


# --- ΔF Heatmaps ---
fig = plt.figure(figsize=(14, 5))
gs = gridspec.GridSpec(1, 3, width_ratios=[1, 1, 0.05], wspace=0.1)
axs = [fig.add_subplot(gs[0]), fig.add_subplot(gs[1])]
cax = fig.add_subplot(gs[2])

for i, dmd in enumerate([1, 2]):
    dff = nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"]
    dff_data = np.array(dff.data)
    dff_timestamps = np.array(dff.timestamps)

    n_timestamps, n_rois = dff_data.shape
    ts_start, ts_end = dff_timestamps[0], dff_timestamps[-1]
    std = np.nanstd(dff_data)
    mean = np.nanmean(dff_data)

    im = axs[i].imshow(dff_data.T, aspect='auto', extent=[ts_start, ts_end, n_rois, 0],
                       vmin=mean - 2 * std, vmax=mean + 2 * std)
    axs[i].set_title(f"DMD{dmd} ΔF Heatmap")
    axs[i].set_xlabel('Time (s)')
    axs[i].set_ylabel('ROIs')

fig.colorbar(im, cax=cax, label='ΔF')
plt.tight_layout()
plt.show()


        
        
def show_all_roi_thumbnails(dmd, max_cols=8, scale=0.25):
    """
    Display a grid of ROI response thumbnails for a given DMD.

    Parameters:
        dmd (int): DMD number (1 or 2).
        max_cols (int): Maximum number of columns in the grid.
        scale (float): Scaling factor for the figure size.
    """
    base_path = Path(f"/content/oddball_traces/DMD{dmd}")
    roi_files = sorted(base_path.glob("roi_*_oddball_traces.png"))

    if not roi_files:
        print(f"No ROI plots found in {base_path}")
        return

    n_rois = len(roi_files)
    n_cols = min(max_cols, n_rois)
    n_rows = int(np.ceil(n_rois / n_cols))

    fig, axs = plt.subplots(n_rows, n_cols, figsize=(n_cols * 3 * scale, n_rows * 2.5 * scale))
    axs = axs.flatten() if n_rois > 1 else [axs]  # handle 1x1 subplot edge case

    for i, roi_file in enumerate(roi_files):
        img = PILImage.open(roi_file)
        axs[i].imshow(img)
        axs[i].axis('off')
        axs[i].set_title(roi_file.stem.replace("_oddball_traces", ""), fontsize=8)

    # Hide unused subplots if number of ROIs < total axes
    for ax in axs[n_rois:]:
        ax.axis('off')

    plt.tight_layout()
    plt.show()

# === Example: show all DMD1 traces
show_all_roi_thumbnails(dmd=1)

# To see DMD2:
show_all_roi_thumbnails(dmd=2)


def get_significant_rois(responses, trace_window, z_thresh=1.0):
    """
    Identify ROIs that show a mean z-scored ΔF/F > z_thresh during the stimulus window
    in any condition.

    Parameters:
        responses (dict): Output of extract_oddball_responses.
        trace_window (ndarray): Time vector aligned to stimulus onset.
        z_thresh (float): Z-score threshold (default = 1.0).

    Returns:
        List of unique ROI indices that exceed the threshold in any condition.
    """
    stim_period = trace_window >= 0  # Boolean mask for stimulus time
    roi_set = set()

    for cond, cond_data in responses.items():
        if len(cond_data['traces']) == 0:
            continue

        traces = np.stack(cond_data['traces'])  # Shape: [n_trials, n_timepoints, n_rois]
        stim_traces = traces[:, stim_period, :]  # Select only stimulus period

        # Mean response across trials and time for each ROI
        mean_response = np.nanmean(stim_traces, axis=(0, 1))

        # Find ROIs exceeding the threshold
        sig_rois = np.where(mean_response > z_thresh)[0]
        roi_set.update(sig_rois)

    return sorted(list(roi_set))

# === Loop over DMD1 and DMD2 ===
sig_rois_by_dmd = {}

for dmd in [1, 2]:
    print(f"\nProcessing DMD{dmd}")

    # Load ΔF/F and timestamps
    dff = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)

    # Z-score and align responses to stimulus
    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=0, window_duration=0.6, baseline_duration=0.5
    )

# --- Set z-score threshold ---
z_thresh = 1.0

# --- Helper: Get significant ROIs (z > threshold during stimulus) ---
def get_significant_rois(responses, trace_window, z_thresh=1.0):
    stim_period = trace_window >= 0
    roi_set = set()
    for cond_data in responses.values():
        if not cond_data['traces']:
            continue
        traces = np.stack(cond_data['traces'])  # [trials, time, rois]
        stim_traces = traces[:, stim_period, :]
        mean_response = np.nanmean(stim_traces, axis=(0, 1))
        sig_rois = np.where(mean_response > z_thresh)[0]
        roi_set.update(sig_rois)
    return sorted(list(roi_set))

# --- Helper: Summarize traces for selected ROIs ---
def summarize_by_condition(responses, significant_rois):
    summaries = {}
    for cond, data in responses.items():
        if not data['traces'] or not significant_rois:
            continue
        traces = np.stack(data['traces'], axis=0)  # [trials, time, rois]
        traces = traces[:, :, significant_rois]
        mean_trace = np.nanmean(traces, axis=(0, 2))
        sem_trace = np.nanstd(traces, axis=(0, 2)) / np.sqrt(traces.shape[0])
        median_trace = np.nanmedian(traces, axis=(0, 2))
        summaries[cond] = {
            'mean': mean_trace,
            'sem': sem_trace,
            'median': median_trace
        }
    return summaries

# --- Helper: Plot average traces with SEM shading ---
def plot_condition_summary(summaries, trace_window, dmd_label, n_rois=None, title_suffix="(Significant ROIs only)"):
    plt.figure(figsize=(10, 4))
    colors = {'standard': 'gray', 'static': 'black', '45': 'red', '90': 'green'}

    for cond, summary in summaries.items():
        if cond not in colors:
            continue
        color = colors[cond]
        plt.plot(trace_window, summary['mean'], label=f"{cond}", color=color, linewidth=2)
        plt.fill_between(trace_window,
                         summary['mean'] - summary['sem'],
                         summary['mean'] + summary['sem'],
                         color=color, alpha=0.2)

    # Stimulus markers
    plt.axvline(0, color='black', linestyle='--', linewidth=1, label="Stimulus onset")
    plt.axvline(trace_window[trace_window >= 0][0] + 0.343, color='black', linestyle='--', linewidth=1, label="Stimulus offset")

    # Title with ROI count
    title = f"Average Oddball Responses – {dmd_label} {title_suffix}"
    if n_rois is not None:
        title += f"\n(n = {n_rois} ROIs)"
    plt.title(title)
    
    # Add annotation with z-threshold
    if z_thresh is not None and n_rois is not None:
        text_str = f"{n_rois} significant ROIs (z > {z_thresh:.2f})"
        plt.text(0.99, 0.95, text_str,
                 ha='right', va='top', transform=plt.gca().transAxes,
                 fontsize=9, bbox=dict(facecolor='white', edgecolor='black', alpha=0.6))

    plt.xlabel("Time (s)")
    plt.ylabel("Z-scored ΔF")
    plt.legend()
    plt.tight_layout()
    plt.show()

# --- Main loop for DMD1 and DMD2 ---
for dmd in [1, 2]:
    print(f"\n=== Processing DMD{dmd} ===")

    # Load ΔF/F and timestamps
    dff = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)

    # Extract z-scored trial-aligned responses
    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=0, window_duration=0.6, baseline_duration=0.5
    )

    # Identify significant ROIs
    sig_rois = get_significant_rois(responses, trace_window, z_thresh=z_thresh)
    print(f"  Found {len(sig_rois)} modulated ROIs (z > {z_thresh:.2f}): {sig_rois}")

    # Summarize and plot
    summaries = summarize_by_condition(responses, sig_rois)
    plot_condition_summary(summaries, trace_window, dmd_label=f"DMD{dmd}", n_rois=len(sig_rois))


"""
====================================================================================
Spatial Similarity Analysis of ROI Responses for DMD1 and DMD2 Imaging Planes
====================================================================================

This script performs a spatial organization analysis of neuronal activity patterns
extracted from ΔF/F traces in two imaging planes (DMD1 and DMD2). The goal is to 
investigate whether nearby ROIs exhibit more similar stimulus-evoked responses.

For each imaging plane (DMD1 and DMD2), the following steps are carried out:

1. Extract binary image masks for each ROI and compute their spatial centroids.
2. Compute the pairwise Euclidean distance matrix between ROI centroids.
3. Extract z-scored ΔF responses aligned to oddball stimulus events.
4. For each stimulus condition (e.g., 'standard', '45', '90', 'static'):
    - Compute average response traces per ROI across trials.
    - Calculate pairwise correlation between ROI response profiles.
    - Compare functional similarity with anatomical distance:
        • Spearman correlation between distance and dissimilarity
        • Binned similarity vs. distance plot with error bars
        • Similarity heatmap sorted by spatial proximity
        • Boxplot comparing similarity in nearby vs. distant ROI pairs

Outputs:
- Summary statistics for spatial correlation (Spearman r, p-values)
- Visualizations of response similarity as a function of spatial distance
- Heatmaps and boxplots for each condition and imaging plane

This analysis helps determine whether functional clustering exists at the scale
of recorded ROIs in each imaging field.
""" 

conditions = ['standard', '45', '90', 'static']

for dmd in [1, 2]:
    print(f"\n=== Processing DMD{dmd} ===")

    # === Step 1: Get ROI masks and centroids ===
    roi_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']
    n_rois = roi_masks.shape[0]

    # Compute (row, col) centroid for each ROI
    roi_centroids = np.array([
        np.argwhere(mask).mean(axis=0) for mask in roi_masks
    ])

    # === Step 2: Compute pairwise distances between ROIs ===
    distance_matrix = squareform(pdist(roi_centroids))  # shape: [n_rois, n_rois]
    flat_distances = squareform(distance_matrix, checks=False)

    reference_roi = 0
    sorted_idx = np.argsort(distance_matrix[reference_roi])  # sort by proximity to ROI 0

    # === Step 3: Extract z-scored ΔF traces aligned to oddball stimuli ===
    dff = np.array(nwb.processing['ophys']['DfOverF'][f'DMD{dmd}_DfOverF'].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f'DMD{dmd}_DfOverF'].timestamps)

    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=0,
        window_duration=0.6,
        baseline_duration=0.5
    )

    # === Step 4: Loop through stimulus conditions ===
    for cond in conditions:
        if cond not in responses:
            print(f"Skipping condition {cond} (not found in data).")
            continue

        print(f"\nProcessing condition: {cond}")

        # Stack all trials: [n_trials, n_timepoints, n_rois]
        traces_all = np.stack(responses[cond]['traces'])

        # Compute mean trace per ROI across trials: [n_rois, n_timepoints]
        mean_traces = np.nanmean(traces_all, axis=0).T  # shape: [n_rois, time]

        # === Step 5: Similarity matrix and correlation ===
        similarity_matrix = np.corrcoef(mean_traces)                         # ROI–ROI similarity
        dissimilarity_matrix = 1 - similarity_matrix                         # dissimilarity
        flat_dissimilarities = squareform(dissimilarity_matrix, checks=False)

        # === Step 6: Correlate similarity with spatial distance ===
        rho, pval = spearmanr(flat_distances, flat_dissimilarities)
        print(f"Spearman r = {rho:.2f}, p = {pval:.4f}")

        # === Step 7: Binned distance-similarity plot ===
        df = pd.DataFrame({
            'distance': flat_distances,
            'similarity': 1 - flat_dissimilarities
        })
        df['distance_bin'] = pd.qcut(df['distance'], q=10)

        bin_summary = df.groupby('distance_bin')['similarity'].agg(['mean', 'sem']).reset_index()
        bin_centers = df.groupby('distance_bin')['distance'].mean().values

        plt.figure(figsize=(7, 5))
        plt.errorbar(bin_centers, bin_summary['mean'], yerr=bin_summary['sem'], fmt='o-', capsize=4)
        plt.xlabel("Inter-ROI Distance (pixels)")
        plt.ylabel("Mean Response Correlation")
        plt.title(f"ROI Response Similarity vs Distance\nCondition: {cond} – DMD{dmd}")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

        # === Step 8: Heatmap of similarity matrix (sorted by proximity) ===
        sorted_sim = similarity_matrix[sorted_idx][:, sorted_idx]
        plt.figure(figsize=(6, 5))
        sns.heatmap(sorted_sim, cmap='viridis', square=True, cbar_kws={'label': 'Correlation'})
        plt.title(f"All ROIs Similarity Sorted by Distance\nCondition: {cond} – DMD{dmd}")
        plt.xlabel("ROIs (sorted)")
        plt.ylabel("ROIs (sorted)")
        plt.tight_layout()
        plt.show()

        # === Step 9: Boxplot – Nearby vs Distant ROIs ===
        threshold = np.median(flat_distances)
        df['proximity'] = np.where(df['distance'] < threshold, 'Nearby', 'Distant')

        plt.figure(figsize=(6, 5))
        sns.boxplot(data=df, x='proximity', y='similarity', palette='Set2')
        plt.ylabel("Response Correlation")
        plt.title(f"Nearby vs Distant ROI Pairs\nCondition: {cond} – DMD{dmd}")
        plt.tight_layout()
        plt.show()
    


for dmd in [1, 2]:
    print(f"Processing DMD{dmd} with custom ΔF")

    # Use raw fluorescence, not pre-computed DfOverF
    raw_fluo = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)

    # Compute custom ΔF/F using 10th percentile baseline
    dff = compute_dff_low10(raw_fluo)

    # Extract trial-aligned responses
    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=onset_delay,
        window_duration=window_duration,
        baseline_duration=baseline_duration
    )

    # Plot per ROI traces
    n_rois = dff.shape[1]
    conditions = ['standard', 'static', '45', '90']
    colors = {'standard': 'gray', 'static': 'black', '45': 'red', '90': 'green'}
    dmd_dir = output_dir / f"DMD{dmd}"
    dmd_dir.mkdir(exist_ok=True)

    for roi in range(n_rois):
        plt.figure(figsize=(12, 4))
        for cond in conditions:
            if cond in responses and len(responses[cond]['traces']) > 0:
                traces = np.stack(responses[cond]['traces'])  # [trials, time, rois]
                if traces.shape[0] > 0 and roi < traces.shape[2]:
                    roi_traces = traces[:, :, roi]
                    mean_trace = np.nanmean(roi_traces, axis=0)
                    plt.plot(trace_window, mean_trace, label=cond, color=colors.get(cond, 'black'))
        plt.title(f"DMD{dmd} ROI {roi} – Oddball Responses (custom ΔF/F)")
        plt.xlabel("Time (s)")
        plt.ylabel("Z-scored ΔF")
        plt.axvline(0, color='black', linestyle='--', linewidth=1)
        plt.axvline(window_duration, color='black', linestyle='--', linewidth=1)
        plt.legend()
        plt.tight_layout()
        plt.savefig(dmd_dir / f"roi_{roi}_oddball_traces.png", dpi=150)
        plt.close()
        
        
def compute_rf_similarity(dmd_id, dff, timestamps, stim_table, roi_masks, onset_delay=0.1, window_duration=0.6):
    # 1. Identify RF trials (non-zero screen position)
    rf_block = stim_table[(stim_table['x_position'] != 0) & (stim_table['y_position'] != 0)].copy()
    rf_block.sort_values('start_time', inplace=True)

    # 2. Compute preferred screen location for each ROI
    roi_rf_centers = {}
    for roi in range(dff.shape[1]):
        response_by_pos = {}
        for _, row in rf_block.iterrows():
            x, y = row['x_position'], row['y_position']
            stim_start = row['start_time']
            idx_start = np.searchsorted(timestamps, stim_start + onset_delay)
            idx_end = np.searchsorted(timestamps, stim_start + onset_delay + window_duration)
            if idx_end > idx_start:
                mean_resp = np.nanmean(dff[idx_start:idx_end, roi])
                response_by_pos.setdefault((x, y), []).append(mean_resp)
        if response_by_pos:
            avg_by_pos = {pos: np.nanmean(vals) for pos, vals in response_by_pos.items()}
            best_pos = max(avg_by_pos, key=avg_by_pos.get)
            roi_rf_centers[roi] = best_pos

    # 3. Get valid ROI centroids and RF coords
    roi_centroids = np.array([np.argwhere(mask).mean(axis=0) for mask in roi_masks])
    rf_coords = np.array([roi_rf_centers.get(i, (np.nan, np.nan)) for i in range(len(roi_centroids))])
    valid_mask = ~np.isnan(rf_coords[:, 0])
    roi_centroids = roi_centroids[valid_mask]
    rf_coords = rf_coords[valid_mask]

    # 4. Distance and correlation
    spatial_dist = squareform(pdist(roi_centroids))
    rf_dist = squareform(pdist(rf_coords))
    rho, pval = spearmanr(squareform(spatial_dist), squareform(rf_dist))

    return rf_coords, roi_centroids, rho, pval

results = {}

for dmd in [1, 2]:
    print(f"Running RF similarity analysis for DMD{dmd}")
    dff = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)
    roi_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']

    rf_coords, roi_centroids, rho, pval = compute_rf_similarity(dmd, dff, timestamps, stim_table, roi_masks)
    results[dmd] = {'rf_coords': rf_coords, 'roi_centroids': roi_centroids, 'rho': rho, 'pval': pval}
    print(f"DMD{dmd} – Spearman r = {rho:.2f}, p = {pval:.4f}")
    

def compute_rf_dissimilarity_vs_distance(dmd_id, dff, timestamps, stim_table, roi_masks, onset_delay=0.1, window_duration=0.6):
    # Step 1: Extract RF trials (x_position ≠ 0 and y_position ≠ 0)
    rf_block = stim_table[(stim_table['x_position'] != 0) & (stim_table['y_position'] != 0)].copy()
    rf_block.sort_values('start_time', inplace=True)

    # Step 2: Determine max-response RF location for each ROI
    roi_rf_centers = {}
    for roi in range(dff.shape[1]):
        response_by_pos = {}
        for _, row in rf_block.iterrows():
            x, y = row['x_position'], row['y_position']
            stim_start = row['start_time']
            idx_start = np.searchsorted(timestamps, stim_start + onset_delay)
            idx_end = np.searchsorted(timestamps, stim_start + onset_delay + window_duration)
            if idx_end > idx_start:
                mean_resp = np.nanmean(dff[idx_start:idx_end, roi])
                response_by_pos.setdefault((x, y), []).append(mean_resp)
        if response_by_pos:
            avg_by_pos = {pos: np.nanmean(vals) for pos, vals in response_by_pos.items()}
            best_pos = max(avg_by_pos, key=avg_by_pos.get)
            roi_rf_centers[roi] = best_pos

    # Step 3: Get valid ROI coordinates
    roi_centroids = np.array([np.argwhere(mask).mean(axis=0) for mask in roi_masks])
    rf_coords = np.array([roi_rf_centers.get(i, (np.nan, np.nan)) for i in range(len(roi_centroids))])
    valid_mask = ~np.isnan(rf_coords[:, 0])
    roi_centroids = roi_centroids[valid_mask]
    rf_coords = rf_coords[valid_mask]

    # Step 4: Compute distances
    spatial_dist = squareform(pdist(roi_centroids))
    rf_dist = squareform(pdist(rf_coords))
    flat_spatial = squareform(spatial_dist)
    flat_rf = squareform(rf_dist)

    df = pd.DataFrame({
        'anatomical_distance': flat_spatial,
        'rf_distance': flat_rf,
        'dmd': f"DMD{dmd_id}"
    })

    return df

def compute_rf_dissimilarity_vs_distance(dmd_id, dff, timestamps, stim_table, roi_masks, onset_delay=0, window_duration=0.6):
    rf_block = stim_table[(stim_table['x_position'] != 0) & (stim_table['y_position'] != 0)].copy()
    rf_block.sort_values('start_time', inplace=True)

    roi_rf_centers = {}
    for roi in range(dff.shape[1]):
        response_by_pos = {}
        for _, row in rf_block.iterrows():
            x, y = row['x_position'], row['y_position']
            stim_start = row['start_time']
            idx_start = np.searchsorted(timestamps, stim_start + onset_delay)
            idx_end = np.searchsorted(timestamps, stim_start + onset_delay + window_duration)
            if idx_end > idx_start:
                mean_resp = np.nanmean(dff[idx_start:idx_end, roi])
                response_by_pos.setdefault((x, y), []).append(mean_resp)
        if response_by_pos:
            avg_by_pos = {pos: np.nanmean(vals) for pos, vals in response_by_pos.items()}
            best_pos = max(avg_by_pos, key=avg_by_pos.get)
            roi_rf_centers[roi] = best_pos

    roi_centroids = np.array([np.argwhere(mask).mean(axis=0) for mask in roi_masks])
    rf_coords = np.array([roi_rf_centers.get(i, (np.nan, np.nan)) for i in range(len(roi_centroids))])
    valid_mask = ~np.isnan(rf_coords[:, 0])
    roi_centroids = roi_centroids[valid_mask]
    rf_coords = rf_coords[valid_mask]

    spatial_dist = squareform(pdist(roi_centroids))
    rf_dist = squareform(pdist(rf_coords))

    flat_spatial = squareform(spatial_dist)
    flat_rf = squareform(rf_dist)

    df = pd.DataFrame({
        'anatomical_distance': flat_spatial,
        'rf_distance': flat_rf,
        'dmd': f"DMD{dmd_id}"
    })

    return df

# === Run for both DMDs ===
dfs = []
for dmd in [1, 2]:
    dff = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)
    roi_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']
    df = compute_rf_dissimilarity_vs_distance(dmd, dff, timestamps, stim_table, roi_masks)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# === Plot with subplots and lowess smoothing ===
df1 = combined_df[combined_df['dmd'] == 'DMD1']
df2 = combined_df[combined_df['dmd'] == 'DMD2']

fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

# DMD1
sns.regplot(
    data=df1,
    x='anatomical_distance',
    y='rf_distance',
    ax=axs[0],
    scatter_kws={'alpha': 0.3, 's': 15,'color': 'blue' },
    line_kws={'color': 'black'},
    lowess=True
)
axs[0].set_title("DMD1")
axs[0].set_xlabel("Anatomical Distance (pixels)")
axs[0].set_ylabel("RF Distance (deg)")
axs[0].grid(True)

# DMD2
sns.regplot(
    data=df2,
    x='anatomical_distance',
    y='rf_distance',
    ax=axs[1],
    scatter_kws={'alpha': 0.3, 's': 15,'color': 'blue' },
    line_kws={'color': 'black'},
    lowess=True
)
axs[1].set_title("DMD2")
axs[1].set_xlabel("Anatomical Distance (pixels)")
axs[1].set_ylabel("RF Distance (deg)")
axs[1].grid(True)

plt.suptitle("RF Dissimilarity vs Anatomical Distance (Per DMD)", fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()


print("Example ROI centroids:", roi_centroids[:5])
print("Min/max:", np.min(roi_centroids), np.max(roi_centroids))

print("X range:", np.min(roi_centroids[:, 1]), "to", np.max(roi_centroids[:, 1]))
print("Y range:", np.min(roi_centroids[:, 0]), "to", np.max(roi_centroids[:, 0]))


# === Assumes you already have these from earlier analysis ===
# roi_centroids: array of shape [n_rois, 2] – anatomical positions (e.g. from ROI masks)
# rf_coords: array of shape [n_rois, 2] – preferred screen positions

# Example: simulate if not available (replace with real data)
# np.random.seed(3)
# n_rois = 80
# roi_centroids = np.random.rand(n_rois, 2) * 100
# rf_coords = roi_centroids + np.random.randn(n_rois, 2) * 10

# === Step 1: Group ROIs by rounded RF position ===
rf_pos_rounded = [tuple(np.round(pos, decimals=1)) for pos in rf_coords]
position_to_indices = defaultdict(list)

for idx, pos in enumerate(rf_pos_rounded):
    position_to_indices[pos].append(idx)

# === Step 2: Compute pairwise distances between ROIs for each shared RF position ===
position_distance_stats = {}

for pos, indices in position_to_indices.items():
    if len(indices) < 2:
        continue  # skip if only one ROI has this RF
    subset_centroids = roi_centroids[indices]
    dists = pdist(subset_centroids)
    position_distance_stats[pos] = dists

# === Step 3: Plot distributions for a few screen positions ===
fig, axs = plt.subplots(1, 3, figsize=(15, 4))

for ax, (pos, dists) in zip(axs, list(position_distance_stats.items())[:3]):
    ax.hist(dists, bins=15, color='skyblue', edgecolor='black', density=True)
    ax.set_title(f"RF @ {pos}\n(n={len(dists)} pairs)")
    ax.set_xlabel("Anatomical Distance (pixels)")
    ax.set_ylabel("Probability Density")
    ax.grid(True)

plt.suptitle("Normalized Pairwise Distance Distributions for Shared RF Preference", fontsize=14)
plt.tight_layout(rect=[0, 0, 1, 0.92])
plt.show()



# Prepare containers
tuning_vs_distance_all = []
rf_vs_distance_all = []
shared_rf_distance_stats = {}

for dmd in [1, 2]:
    print(f"\n=== Processing DMD{dmd} ===")
    dff = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].data)
    timestamps = np.array(nwb.processing['ophys']['DfOverF'][f"DMD{dmd}_DfOverF"].timestamps)
    roi_masks = nwb.processing['ophys']['ImageSegmentation'][f'DMD{dmd}_plane_segmentation']['image_mask']
    roi_centroids = np.array([np.argwhere(mask).mean(axis=0) for mask in roi_masks])

    # Extract responses
    responses, trace_window = extract_oddball_responses(
        dff, timestamps, oddball_block,
        onset_delay=0, window_duration=0.6, baseline_duration=0.5
    )

    # --- 1. Orientation tuning preference ---
    roi_orientations = {}
    for roi in range(dff.shape[1]):
        max_response = -np.inf
        preferred_ori = None
        for cond in ['0', '45', '90']:
            if cond in responses:
                traces = np.stack(responses[cond]['traces'])[:, :, roi]
                mean_resp = np.nanmean(traces[:, trace_window >= 0])
                if mean_resp > max_response:
                    max_response = mean_resp
                    preferred_ori = int(cond)
        if preferred_ori is not None:
            roi_orientations[roi] = preferred_ori

    roi_ids = list(roi_orientations.keys())
    ori_vals = np.array([roi_orientations[r] for r in roi_ids])
    centroids_tuning = roi_centroids[roi_ids]

    ori_diff_matrix = squareform(pdist(ori_vals[:, None], lambda u, v: abs((u - v) % 180)))
    anatomical_dist_matrix = squareform(pdist(centroids_tuning))
    tuning_vs_distance_all.append((anatomical_dist_matrix.flatten(), ori_diff_matrix.flatten()))

    # --- 2. RF preference ---
    rf_block = stim_table[(stim_table['x_position'] != 0) & (stim_table['y_position'] != 0)].copy()
    rf_block.sort_values('start_time', inplace=True)

    roi_rf_centers = {}
    for roi in range(dff.shape[1]):
        response_by_pos = {}
        for _, row in rf_block.iterrows():
            x, y = row['x_position'], row['y_position']
            stim_start = row['start_time']
            idx_start = np.searchsorted(timestamps, stim_start + 0.1)
            idx_end = np.searchsorted(timestamps, stim_start + 0.1 + 0.6)
            if idx_end > idx_start:
                mean_resp = np.nanmean(dff[idx_start:idx_end, roi])
                response_by_pos.setdefault((x, y), []).append(mean_resp)
        if response_by_pos:
            avg_by_pos = {pos: np.nanmean(vals) for pos, vals in response_by_pos.items()}
            best_pos = max(avg_by_pos, key=avg_by_pos.get)
            roi_rf_centers[roi] = best_pos

    rf_coords = np.array([roi_rf_centers.get(i, (np.nan, np.nan)) for i in range(len(roi_centroids))])
    valid_mask = ~np.isnan(rf_coords[:, 0])
    rf_coords_valid = rf_coords[valid_mask]
    centroids_valid = roi_centroids[valid_mask]

    rf_dist = squareform(pdist(rf_coords_valid))
    spatial_dist = squareform(pdist(centroids_valid))
    rf_vs_distance_all.append((spatial_dist.flatten(), rf_dist.flatten()))

    # --- 3. Shared RF distance distributions ---
    rf_to_roi = {}
    for roi, rf in roi_rf_centers.items():
        rf_to_roi.setdefault(rf, []).append(roi)

    rf_pos_distances = {}
    for rf, rois in rf_to_roi.items():
        if len(rois) > 1:
            pairs = [(i, j) for idx, i in enumerate(rois) for j in rois[idx + 1:]]
            distances = [np.linalg.norm(roi_centroids[i] - roi_centroids[j]) for i, j in pairs]
            rf_pos_distances[rf] = distances

    shared_rf_distance_stats[dmd] = rf_pos_distances

# === Plot 1: Orientation tuning difference vs anatomical distance
fig, axs = plt.subplots(1, 2, figsize=(12, 5))
for i, (distances, ori_diffs) in enumerate(tuning_vs_distance_all):
    axs[i].scatter(distances, ori_diffs, alpha=0.3, s=10)
    axs[i].set_title(f"DMD{i+1} – Orientation Tuning vs Distance")
    axs[i].set_xlabel("Anatomical Distance (px)")
    axs[i].set_ylabel("Orientation Difference (deg)")
    axs[i].grid(True)
plt.tight_layout()
plt.show()

# === Plot 2: RF distance vs anatomical distance
fig, axs = plt.subplots(1, 2, figsize=(12, 5))
for i, (distances, rf_diffs) in enumerate(rf_vs_distance_all):
    axs[i].scatter(distances, rf_diffs, alpha=0.3, s=10)
    axs[i].set_title(f"DMD{i+1} – RF Distance vs Anatomical Distance")
    axs[i].set_xlabel("Anatomical Distance (px)")
    axs[i].set_ylabel("RF Distance (screen units)")
    axs[i].grid(True)
plt.tight_layout()
plt.show()



