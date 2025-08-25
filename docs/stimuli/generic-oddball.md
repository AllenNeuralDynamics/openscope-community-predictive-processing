# Generic Oddball Protocol

## Overview

The Generic Oddball Protocol represents a unified framework for running multiple experimental sensory contexts using a single Bonsai script. The system uses dynamically generated CSV files to define stimulus parameters, providing precise control over trial sequences, timing, and stimulus properties with unique stimulus presentations for each experimental session.

## Architecture

The Generic Oddball system consists of two main components:

1. **`generate_experiment_csv.py`**: Python script that generates CSV files containing stimulus parameters for different experimental sensory contexts
2. **`generic_oddball.bonsai`**: Bonsai workflow that reads CSV files and presents stimuli according to the specified parameters

This separation allows for:
- **Reproducible experiments**: Exact stimulus sequences can be reproduced using logged random seeds
- **Unique sessions**: Each session generates a unique stimulus sequence to avoid habituation effects
- **Flexible parameter control**: All stimulus properties can be precisely specified
- **Complex experimental designs**: Multiple sensory contexts can be run with the same underlying infrastructure
- **Integrated workflow**: The experimental launcher automatically generates stimulus tables on-the-fly

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

The system supports six main experimental session types, each designed to probe different aspects of predictive processing:

### 1. Visual Mismatch (`visual_mismatch`)
**Purpose**: Classic oddball paradigm with orientation deviants to probe sensory prediction error responses
**Blocks**: Control blocks interspersed with oddball blocks containing orientation deviants (45°, 90°), halts, and omissions

### 2. Sensorimotor Mismatch (`sensorimotor_mismatch`) 
**Purpose**: Closed-loop paradigm where visual stimulus phase is coupled to wheel movement, with occasional mismatches
**Blocks**: Control blocks plus sensorimotor mismatch blocks with motor coupling violations

### 3. Sequence Mismatch (`sequence_mismatch`)
**Purpose**: Tests sequence learning and prediction with ordered stimulus presentations and violations
**Blocks**: Control blocks plus sequential blocks with predictable patterns and violations

### 4. Duration Mismatch (`duration_mismatch`)
**Purpose**: Temporal prediction paradigm with duration-based deviants
**Blocks**: Control blocks plus duration oddball blocks with shorter/longer duration deviants

### 5. Sequence No-Oddball (`sequence_no_oddball`)
**Purpose**: Long blocks of sequential stimuli without oddball trials for baseline sequence processing
**Blocks**: Extended control and sequential blocks without mismatch trials

### 6. Sensorimotor No-Oddball (`sensorimotor_no_oddball`)
**Purpose**: Long blocks of sensorimotor coupling without mismatch for baseline motor-visual coupling
**Blocks**: Extended control and motor coupling blocks without mismatch trials

Each session type includes:
- **RF Mapping**: 9x9 grid of positions for receptive field characterization
- **Control Blocks**: Standard stimulus presentations for baseline comparisons  
- **Session-Specific Randomization**: Unique random seed ensures different stimulus sequences per session

## Usage Instructions

### Integrated Workflow (Recommended)

The recommended approach is to use the experimental launcher, which automatically handles stimulus table generation:

1. **Create Parameter File**: Specify the desired session type in the launcher parameter JSON:
```json
{
    "repository_url": "https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing.git",
    "commit_hash": "main",
    "local_repository_path": "C:/BonsaiDataPredictiveProcessingTest", 
    "bonsai_path": "code/stimulus-control/src/Mindscope/generic_oddball.bonsai",
    "session_type": "sensorimotor_mismatch",
    "mouse_id": "subject_123",
    "user_id": "experimenter"
}
```

2. **Run Launcher**: Execute the launcher with your parameter file:
```bash
python bonsai_experiment_launcher.py your_params.json
```

3. **Automatic Processing**: The launcher will:
   - Generate a unique stimulus table for the specified session type
   - Place the CSV file in the session output folder
   - Launch Bonsai with the correct stimulus table path
   - Log all generation details for traceability

### Manual Generation (Advanced Users)

For direct control over stimulus generation, you can use the generator script directly:

**Generate a Single Session CSV:**
```bash
cd code/stimulus-control/src/Mindscope/
python generate_experiment_csv.py --session-type sensorimotor_mismatch --output-path my_session.csv --seed 12345
```

**Available Session Types:**
- `visual_mismatch`
- `sensorimotor_mismatch` 
- `sequence_mismatch`
- `duration_mismatch`
- `sequence_no_oddball`
- `sensorimotor_no_oddball`

### Session Folder Structure

When using the integrated workflow, each session creates an organized folder structure:
```
session_timestamp_mouseID_bonsai/
├── session_timestamp.pkl              # Session data
├── stimulus_table_sensorimotor_mismatch.csv  # Generated stimulus table
├── orientations_logger.csv            # Bonsai timing logs
├── orientations_orientations.csv      # Bonsai parameter logs
└── [other session files...]
```

### Bonsai Workflow Configuration

The Bonsai workflow (`generic_oddball.bonsai`) automatically reads the stimulus table from the path provided by the launcher. Key features:

- **Single CSV Input**: The workflow reads one stimulus table per session
- **Dynamic Parameter Loading**: All stimulus parameters are loaded from the CSV file
- **Hardware Integration**: Supports encoder/wheel input for motor coupling experiments
- **Synchronization**: Provides digital outputs for recording equipment sync
- **Real-time Logging**: Generates detailed logs during stimulus presentation

The launcher automatically passes the correct CSV file path to Bonsai via the `stimulus_table_path` parameter.

## Reproducibility and Session Uniqueness

### Unique Sessions
- Each experimental session generates a unique stimulus sequence using a session-specific random seed
- The seed is derived from session UUID, session type, and timestamp, ensuring no two sessions are identical
- This prevents habituation effects while maintaining experimental rigor

### Reproducibility
- All random seeds are logged with session metadata
- Sessions can be exactly reproduced by using the same seed value
- Complete audit trail from stimulus generation through data collection

### Session Metadata
Each session maintains complete metadata including:
- Session UUID and timestamp
- Random seed used for stimulus generation
- Session type and parameter configuration
- Experiment launcher version and checksums
- Hardware configuration details

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
