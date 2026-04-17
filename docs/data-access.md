# Data Access Guide

This page explains how to find, browse, and open the Predictive Processing data that is publicly available on Amazon S3. **No AWS account is required.**

For a walkthrough of everything on this page, see the [presentation slides](https://docs.google.com/presentation/d/16pukgoNJ8y2fFwfE9ErGTLTxn81HCSLickkPncqPWb0/edit?slide=id.g3de82949ca6_2_176#slide=id.g3de82949ca6_2_176) from our April 14, 2026 community meeting.

## What's Available Now

As of April 2026, our data release is ongoing. Processed assets and partial NWB files are available on S3 for most sessions. Complete NWB files combining all modalities per session will be uploaded to [DANDI](https://dandiarchive.org/) as they are finalized.

| Modality | Raw Assets | Processed Assets | Partial NWBs | Complete NWBs on DANDI |
|----------|-----------|-----------------|-------------|----------------------|
| **Neuropixels** | ✅ Available | ✅ Spike-sorted available | ✅ In sorted assets | ⬚ In progress (pending CCF) |
| **Mesoscope** | ✅ Available | ✅ Planar ophys, behavior, behavior videos | ✅ In processed assets (Zarr) | ⬚ In progress |
| **SLAP2** | ✅ Available | ⬚ Pipeline in development | ⬚ Not yet | ⬚ Not yet |

**What "partial NWB" means:** Each processed asset contains an NWB file with just that modality's data (e.g., the spike-sorted NWB has spike times + LFP but not behavior). The goal is to produce **complete NWBs** that combine behavior + recording into a single file, which will be released on DANDI with a permanent DOI.

**QC is ongoing.** Some assets may be reprocessed as quality control continues. You can check the QC status of individual sessions in the tracking spreadsheet. If you spot issues, please let us know via [GitHub Discussions](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/discussions).

## Getting Started

The fastest path from zero to data:

1. **Find your session** in the [data tracking spreadsheet](https://docs.google.com/spreadsheets/d/1wAeloFJgvRjrseoVeNm4YQd8BezGWRon-Z-b1iJAz9c/edit?gid=970358340#gid=970358340). Column H ("New Session id (Code Ocean)") contains the session identifier — this is also the **folder name on S3**.

2. **Search for it on S3.** Go to the [Quilt S3 viewer](https://open.quiltdata.com/b/aind-open-data/tree/), make sure you are inside the `aind-open-data` bucket, and paste the session identifier into the search bar.

3. **Open the NWB.** Use our [Stream NWB from S3](notebooks/stream_nwb_from_s3.ipynb) notebook to open any NWB file directly from S3 — no download required.

The sections below explain each step in more detail.

## Browsing Data on S3

All data lives in the public S3 bucket **`s3://aind-open-data`**, hosted by AWS Open Data and funded by Amazon to support open science. You can browse it with any S3-compatible tool — no sign-in required.

### Using the Quilt viewer (no code required)

1. Go to [open.quiltdata.com/b/aind-open-data](https://open.quiltdata.com/b/aind-open-data/tree/)
2. Make sure you are **inside the bucket** (the breadcrumb should show `s3 / aind-open-data`)
3. Use the search bar within the bucket to paste a session identifier from the spreadsheet
4. Click into folders to browse files, view images, and inspect metadata

### Using boto3, the AWS CLI, or other tools

Since the bucket is public, you can use any S3-compatible tool with anonymous access — including `boto3`, the AWS CLI (`--no-sign-request`), or libraries like `s3fs`. No credentials are needed. Our [Stream NWB from S3](notebooks/stream_nwb_from_s3.ipynb) notebook demonstrates this with `boto3`. You can also download files directly with `aws s3 cp --no-sign-request`.

!!! note
    Raw Neuropixels sessions can be very large. If you only need spike times, we recommend streaming the NWB rather than downloading the full raw data.

## Understanding Folder Structure

### Session Identifiers

Session identifiers (from the [Getting Started](#getting-started) section above) follow the pattern `<modality>_<mouse_id>_<session_datetime>`, for example:

- `ecephys_012345_2025-01-01_01-01-01`
- `multiplane-ophys_1111111_2025-04-04_04-04-04`

!!! note
    Some newer sessions (particularly SLAP2) omit the modality prefix — this is due to a schema change and does not affect access. For example, a SLAP2 session might simply be `567890_2025-09-09_09-09-09`.

### Assets per Session

Each experimental session produces multiple **assets** (folders) on S3. The number depends on the modality. Searching for a session identifier on S3 will show all associated assets:

**Neuropixels** — currently 2 assets on S3 (1 raw + 1 spike-sorted). Additional CCF and complete NWB assets will appear here as they are produced:

```
ecephys_012345_2025-01-01_01-01-01                              # raw session
ecephys_012345_2025-01-01_01-01-01_sorted_2025-02-02_02-02-02   # spike-sorted
ecephys_012345_ccf                                              # (coming soon) brain region coordinates
ecephys_012345_2025-01-01_01-01-01_nwb_2025-03-03_03-03-03      # (coming soon) complete NWB
```

**Mesoscope** — 4 assets (1 raw + 3 processed). A complete NWB asset will appear as it is produced:

```
multiplane-ophys_1111111_2025-04-04_04-04-04                                         # raw session
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-05-05_05-05-05            # behavior videos (Eye, Face, etc.)
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-06-06_06-06-06            # behavior/timing (stimulus sync, timing QC plots, NWB)
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-07-07_07-07-07            # planar ophys (ΔF/F, segmentation, NWB Zarr)
multiplane-ophys_1111111_2025-04-04_04-04-04_nwb_2025-08-08_08-08-08                  # (coming soon) complete NWB
```

**SLAP2** — currently 1 asset (raw only, processing pipeline in development). Processed and NWB assets will appear as they are produced:

```
567890_2025-09-09_09-09-09                                      # raw session
```

!!! warning
    The three Mesoscope processed assets all contain `_processed_` in the name and **cannot be distinguished by name alone** — they differ only by the processing timestamp. You need to look inside the folder to determine which is which (see below).

### Raw Session Assets

Across modalities, raw sessions share a common structure, though the exact files vary by schema version:

```
ecephys_012345_2025-01-01_01-01-01/
├── behavior-videos/          # MP4s of eye, face, body cameras (+ JSON sidecar per video)
├── behavior/                 # Stimulus tables, sync data, running speed
├── ecephys/                  # Modality-specific data (see note below)
│   ├── ecephys_clipped/
│   └── ecephys_compressed/
├── original_metadata/        # Original metadata from acquisition
├── data_description.json     # Project, funding, institution
├── metadata.nd.json          # Consolidated metadata document
├── session.json              # Session metadata, start/end time, rig ID, stimulus info
├── subject.json              # Mouse ID, genotype, age
├── procedures.json           # Surgical procedures
├── rig.json                  # Rig configuration
└── processing.json           # Processing pipeline metadata
```

The **modality-specific directory** differs by session type:

- **Neuropixels**: `ecephys/` — contains `ecephys_clipped/` and `ecephys_compressed/`
- **Mesoscope**: `pophys/` — contains raw imaging data
- **SLAP2**: `slap2/` — contains `dynamic_data/` and `notes/`

!!! note
    Sessions collected on the **Neuropixels** and **Mesoscope** rigs use `rig.json`, `session.json`, `original_metadata/`, and `metadata.nd.json`. Sessions collected on the **SLAP2** rig use `instrument.json` and `acquisition.json` instead. The information is equivalent — the naming difference reflects updated metadata schemas.

### Neuropixels Sorted Assets

The spike-sorted asset contains the full spike sorting pipeline output and a partial NWB:

```
ecephys_012345_2025-01-01_01-01-01_sorted_2025-02-02_02-02-02/
├── spikesorted/              # Raw spike sorting output (one folder per probe)
│   ├── experiment1_Record Node 101#...ProbeA-AP_recording1/
│   │   ├── properties/       # Unit properties (Amplitude.npy, KSLabel.npy, etc.)
│   │   ├── spikes.npy        # Spike times
│   │   └── *.json            # SpikeInterface metadata
│   ├── ...ProbeB-AP_recording1/
│   └── ...                   # One folder per probe (A–F)
├── curated/                  # Post-curation spike sorting (same per-probe structure)
├── postprocessed/            # Post-processing results (per-probe .zarr folders)
├── preprocessed/             # Pre-processing intermediates (motion/)
├── nwb/                      # Partial NWB file (Zarr format, ~250 MB)
├── quality_control/          # Drift maps, firing rate plots, unit yield (per-probe)
├── visualization/            # Per-probe traces, drift maps
├── original_metadata/        # Original metadata from acquisition
├── visualization_output.json # Links to interactive sorting summary portals
├── quality_control.json      # QC metrics summary
├── data_description.json
├── metadata.nd.json
├── subject.json
├── procedures.json
└── processing.json
```

### Mesoscope Processed Assets

The three processed assets for each Mesoscope session are:

**1. Planar Ophys Asset** — identifiable by having plane-named subfolders (e.g., `VISp_0/`, `VISl_4/`):

```
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-07-07_07-07-07/
├── VISp_0/                   # Visual cortex primary, plane 0
│   ├── dff/                  # ΔF/F traces
│   ├── events/               # Event detection results
│   ├── classification/       # Cell classification results
│   ├── extraction/           # ROI extraction output
│   ├── motion_correction/    # Motion correction outputs
│   ├── decrosstalk/          # Crosstalk correction
│   ├── movie_qc/             # QC images (z-drift, segmentation, etc.)
│   ├── VISp_0.h5             # Raw plane data
│   └── VISp_0_*.tif          # Depth/surface reference images
├── VISp_1/, VISp_2/, VISp_3/ # Additional primary visual cortex planes
├── VISl_4/, VISl_5/, ...     # Lateral visual cortex planes
├── vasculature/              # Vasculature reference images
├── pophys.nwb.zarr/          # Partial NWB file (Zarr format)
├── pair0.txt … pair3.txt     # Plane pairing information
├── stitched_full_field_img.h5  # Full-field stitched image
├── data_description.json
├── quality_control.json
├── subject.json
├── procedures.json
└── processing.json
```

**2. Behavior Videos Asset** — identifiable by `Behavior/`, `Eye/`, `Face/`, `Nose/` folders. Contains processed average images and tracking outputs from each camera:

```
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-05-05_05-05-05/
├── Behavior/                 # Body camera tracking output
├── Eye/                      # Eye camera tracking output (avg images)
├── Face/                     # Face camera tracking output
├── Nose/                     # Nose camera tracking output
├── data_description.json
├── quality_control.json
└── ...                       # Standard metadata JSONs
```

**3. Behavior/Timing Asset** — identifiable by timing plot PNGs and a `.nwb/` Zarr directory. Contains processed behavioral signals (stimulus sync, running wheel, photodiode timing) and a partial NWB:

```
multiplane-ophys_1111111_2025-04-04_04-04-04_processed_2025-06-06_06-06-06/
├── multiplane-ophys_1111111_2025-04-04_04-04-04.nwb/   # Partial NWB (Zarr format)
├── *_timing_plot.png         # Timing QC plots (photodiode, physio, eye, face, etc.)
├── wheel_*.png               # Running wheel QC plots
├── metrics.json              # Timing and sync metrics
├── data_description.json
├── quality_control.json
└── ...                       # Standard metadata JSONs
```

!!! tip
    To tell the processed assets apart: if you see plane folders like `VISp_0/`, `VISl_4/`, it's the **planar ophys** asset. If you see `Eye/`, `Face/`, `Behavior/`, `Nose/` folders, it's the **behavior videos** asset. If you see timing plot PNGs and a `.nwb/` directory, it's the **behavior/timing** asset.

### SLAP2 Raw Assets

SLAP2 sessions currently only have raw data:

```
567890_2025-09-09_09-09-09/
├── behavior-videos/          # Eye and face camera videos
├── behavior/                 # HARP-based behavior data, stimulus logs
├── slap2/
│   ├── dynamic_data/         # Imaging data
│   │   ├── reference_stack/  # Reference stack images per DMD
│   │   ├── *_REGISTERED_DOWNSAMPLED-80Hz.tif  # Registered imaging TIFFs
│   │   └── *_ALIGNMENTDATA.mat                # Alignment metadata per trial
│   ├── static_data/          # Structure images and annotations (some sessions)
│   │   ├── structure_*_DMD*.tif               # Structural reference images
│   │   ├── structure_*_DMD*.annotation.json   # ROI annotations
│   │   └── structure_*_DMD*.dat / .meta       # Raw data and metadata
│   └── notes/                # Session notes
├── acquisition.json          # Acquisition metadata
├── instrument.json           # Instrument configuration
├── data_description.json
├── subject.json
├── procedures.json
└── processing.json
```

## Working with NWB Files

Most users will want to work with the NWB files rather than browsing raw S3 folders. We provide notebooks to help with this.

### Streaming NWBs from S3 (recommended)

Our [Stream NWB from S3](notebooks/stream_nwb_from_s3.ipynb) notebook opens any NWB file directly from S3 — no download needed. It auto-detects whether the file is HDF5 or Zarr format. Just pass a session folder name and it finds and opens the NWB for you.

!!! note
    This only works with **processed** assets that contain NWB files. Raw assets do not have NWBs in them.

### What's in each NWB

**Neuropixels NWBs** contain spike times, unit quality metrics, and a downsampled version of the LFP — but **not** raw traces, so file sizes are manageable (~250 MB). Units are automatically classified as **noise**, **MUA** (multi-unit activity), or **SUA** (single-unit activity) by a pre-trained classifier from the [AIBSPhase pipeline](https://github.com/AllenNeuralDynamics/aind-ephys-pipeline-kilosort25). Brain region coordinates (CCF registration) are **not yet available** — histology/brain imaging is still in progress.

**Mesoscope NWBs** (Zarr format) contain ΔF/F traces, event detection, neuropil correction, ROI segmentation masks, and projection images for each imaging plane. For a guided tour, see: [Examine Ophys NWB](notebooks/examine_ophys_nwb.ipynb)

### Spike sorting output portal

To interactively explore the spike sorting results for a Neuropixels session, open the `visualization_output.json` file in the sorted asset and click the `sorting_summary` link for each probe. This launches a browser-based viewer where you can inspect individual units and their quality metrics.

### Example notebooks

| Notebook | Description |
|----------|-------------|
| [Stream NWB from S3](notebooks/stream_nwb_from_s3.ipynb) | Open any NWB from S3 in one line of Python |
| [Examine Ophys NWB](notebooks/examine_ophys_nwb.ipynb) | Walkthrough of ophys NWB contents — ROIs, ΔF/F, events, multi-plane comparison |
| [Intro to Ephys NWBs](notebooks/intro_to_ephys_nwbs.ipynb) | Explore spike-sorted Neuropixels NWBs |

The [OpenScope Databook](https://alleninstitute.github.io/openscope_databook/intro.html) also has extensive notebooks for working with NWB files from Allen Institute projects. Note that our latest NWBs may have some differences in key names or data organization compared to what the Databook shows, but the general patterns are the same.

## Additional Resources

- **Code Ocean** — To see the actual processing pipeline code and run it in the cloud, contact [Jerome Lecoq](mailto:jeromel@alleninstitute.org) or [Carter Peene](mailto:carter.peene@alleninstitute.org) to request access. Code Ocean hosts all of our internal processing code, environments, and compute infrastructure.
- **[DANDI Archive](https://dandiarchive.org/)** — Where complete NWBs will be published with permanent DOIs for citation in publications.

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20data-access" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
