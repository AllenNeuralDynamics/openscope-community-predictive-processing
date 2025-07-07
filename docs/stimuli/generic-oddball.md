# Generic Oddball Protocol

## Overview

The Generic Oddball Protocol represents a unified framework for running multiple experimental sensory contexts using a single Bonsai script. Unlike previous context-specific scripts, this system uses CSV files to define stimulus parameters, making it highly flexible and allowing for complex experimental designs with precise control over trial sequences, timing, and stimulus properties.

## Architecture

The Generic Oddball system consists of two main components:

1. **`generate_experiment_csv.py`**: Python script that generates CSV files containing stimulus parameters for different experimental sensory contexts
2. **`generic_oddball.bonsai`**: Bonsai workflow that reads CSV files and presents stimuli according to the specified parameters

This separation allows for:
- **Reproducible experiments**: Exact stimulus sequences can be saved and repeated
- **Flexible parameter control**: All stimulus properties can be precisely specified
- **Complex experimental designs**: Multiple sensory contexts can be run with the same underlying infrastructure
- **Easy variant generation**: Multiple shuffled versions of experiments can be created
- **Custom experiment loading**: Previously saved CSV files can be loaded and reused for exact replication of experimental conditions

## Script Locations

- **Python Generator**: [`/code/stimulus-control/src/Mindscope/generate_experiment_csv.py`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/blob/main/code/stimulus-control/src/Mindscope/generate_experiment_csv.py)
- **Bonsai Workflow**: [`/code/stimulus-control/src/Mindscope/generic_oddball.bonsai`](https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing/blob/main/code/stimulus-control/src/Mindscope/generic_oddball.bonsai)

## Hardware Requirements

- Behavior device with encoder/wheel for tracking animal movement (when used)
- Digital outputs for synchronization with recording equipment

## CSV Parameter Structure

### Standard CSV Columns

Each CSV file contains the following standardized columns:

| Column | Description | Units | Typical Values |
|--------|-------------|-------|----------------|
| `Contrast` | Stimulus contrast | 0-1 | 1 (full contrast), 0 (omission) |
| `Delay` | Inter-stimulus interval | seconds | 0.343, 1.0, 1.5, 2.0 |
| `Diameter` | Stimulus diameter (also serves as sensory context marker) | degrees | 340-390 (see Diameter Markers) |
| `Duration` | Stimulus presentation duration | seconds | 0.343, 0.250, 0.050-0.200 |
| `Orientation` | Grating orientation | degrees | 0, 45, 90, 135, etc. |
| `Spatial_Frequency` | Spatial frequency of grating | cycles/degree | 0.04 |
| `Temporal_Frequency` | Temporal frequency of grating | Hz | 2, 0 (for halt) |
| `X` | Horizontal position offset | degrees | 0 |
| `Y` | Vertical position offset | degrees | 0 |
| `Phase` | Initial phase of grating | radians | 0 |
| `Trial_Type` | Type of trial | string | 'standard', 'orientation_45', 'orientation_90', 'halt', 'omission', 'jitter', 'single' |
| `Block_Type` | Experimental sensory context | string | 'standard_oddball', 'jitter_oddball', 'sequential_oddball', etc. |

## Sensory Contexts

### 1. Standard Oddball Variants

**Purpose**: Classic mismatch sensory context with occasional stimulus deviants

**Generated Files**: `blocks/standard/standard_oddball_variant_01.csv` through `blocks/standard/standard_oddball_variant_10.csv`

### 2. Jitter Variants

**Purpose**: Temporal prediction sensory context with duration-based deviants

**Generated Files**: `blocks/jitter/jitter_variant_01.csv` through `blocks/jitter/jitter_variant_10.csv`

### 3. Sequential Variants

**Purpose**: Sequence learning with pattern violations

**Generated Files**: `blocks/sequentials/sequential_variant_01.csv` through `blocks/sequentials/sequential_variant_10.csv`

### 4. Motor Sensory Contexts

**Purpose**: Sensorimotor closed-loop with wheel-controlled phase

**Generated Files**: 
- `blocks/motor/motor_oddball_variant_01.csv` through `blocks/motor/motor_oddball_variant_10.csv`
- `blocks/motor/motor_control_variant_01.csv` through `blocks/motor/motor_control_variant_10.csv`

## Usage Instructions

### Step 1: CSV Files

**Option A: Generate New CSV Files**

Run the Python script to generate all experimental sensory contexts:

```bash
cd code/stimulus-control/src/Mindscope/
python generate_experiment_csv.py
```

This creates a complete directory structure:
```
blocks/
├── standard/
│   ├── standard_oddball_variant_01.csv ... 10.csv
│   └── standard_control_variant_01.csv ... 10.csv
├── jitter/
│   ├── jitter_variant_01.csv ... 10.csv
│   └── jitter_control_variant_01.csv ... 10.csv
├── sequentials/
│   ├── sequential_variant_01.csv ... 10.csv
│   └── sequential_control_variant_01.csv ... 10.csv
├── motor/
│   ├── motor_oddball_variant_01.csv ... 10.csv
│   └── motor_control_variant_01.csv ... 10.csv
└── test/
    └── [1-minute test versions of all sensory contexts]
```

### Randomization and Variants

The system supports multiple randomized variants of each sensory context:

- Each variant uses a different random seed for shuffling
- 10 variants are generated by default for each sensory context type
- This enables counterbalancing across subjects and sessions

### Test Variants

Short 1-minute test versions are automatically generated for rapid validation:

- Located in `blocks/test/` directory
- Same structure as full experiments but with reduced trial counts
- Ideal for system testing and workflow validation

**Option B: Use Previously Saved CSV Files**

The system can load any previously generated CSV files, enabling exact replication of experimental conditions:

- **Reuse existing variants**: Load any of the pre-generated variants from the `blocks/` directory
- **Exact replication**: Ensure identical stimulus sequences across subjects or sessions by using the same CSV file


### Step 2: Configure Bonsai Workflow

1. Open `generic_oddball.bonsai` in Bonsai
2. **Configure CSV file sources**: Locate the "Enumerate Files" nodes in the workflow - these determine which experimental blocks will be loaded:
   - Each "Enumerate Files" node points to a specific folder (e.g., `blocks\standard\`, `blocks\jitter\`, etc.)
   - Update the folder paths to point to your desired experimental sensory contexts
   - You can enable/disable different sensory contexts by including/excluding their corresponding "Enumerate Files" nodes
3. **Set block execution order**: The "Concat" main loop determines the sequence in which different experimental blocks are presented:
   - The order of inputs to the Concat node controls the presentation sequence
   - Modify this order to change how sensory contexts are sequenced during the experiment
4. Configure any hardware-specific settings (encoder ports, digital outputs, etc.)

### Step 3: Run Experiment

1. Start the Bonsai workflow
2. The workflow will automatically:

   - Read stimulus parameters from the CSV file
   - Present stimuli according to the specified timing
   - Log experimental data and timestamps
   - Handle synchronization with recording equipment

## Data Collection

The system generates several output files during each session:

### Stimulus Logs
- `orientations_logger.csv`: Timing information for each stimulus presentation

    - Stimulus onset and offset times
    - Unique trial identifiers

- `orientations_orientations.csv`: Complete stimulus parameter log with trial details

    - All stimulus parameters (orientation, contrast, duration, etc.)
    - Trial type and block type information
    - Unique trial identifiers
    - Behavioral data (when encoder is connected)


## Related Documents

- **[Standard Oddball](standard-oddball.md)**: Original standard oddball implementation
- **[Sensory-Motor Closed-Loop](sensory-motor-closed-loop.md)**: Sensorimotor paradigm details
- **[Sequence Mismatch](sequence-mismatch.md)**: Sequence learning paradigm
- **[Experimental Plan](../experimental-plan.md)**: Overview of all experimental sensory contexts
- **[Bonsai Instructions](bonsai_instructions.md)**: General Bonsai setup and usage

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20stimuli/generic-oddball" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
