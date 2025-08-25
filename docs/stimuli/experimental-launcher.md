# Experimental Launcher

The Experimental Launcher is an automated system that manages the complete lifecycle of running Bonsai experiments, from repository setup to experiment execution. It ensures reproducible, reliable experiment execution with automatic package management and error handling.

## Overview

The launcher provides a unified interface for running Bonsai experiments with the following key capabilities:

- **Automated Repository Management**: Downloads and syncs experiment code from GitHub
- **Bonsai Installation & Package Management**: Automatically installs and verifies Bonsai packages
- **Experiment Execution**: Launches Bonsai workflows with proper parameter handling
- **Error Recovery**: Automatically fixes common package and dependency issues
- **Data Management**: Handles experiment data storage and session tracking

## Architecture

### Core Components

**BonsaiExperiment Class** (`bonsai_experiment_launcher.py`)

- Main orchestrator for experiment execution
- Handles all phases of experiment lifecycle
- Provides error handling and recovery mechanisms

**Parameter Management**

- JSON-based configuration system
- Environment-specific settings (camstim config integration)
- Session metadata and UUID generation

**Process Management**

- Windows job object integration for proper cleanup
- Process monitoring and timeout handling
- Signal handling for graceful shutdown

## Experiment Lifecycle

### Phase 1: Repository Setup

1. Clone/update repository from GitHub
2. Checkout specific commit or branch
3. Verify repository integrity
4. Set up local working directory

### Phase 2: Bonsai Installation

1. Locate Bonsai executable in repository
2. Verify Bonsai installation
3. Run setup scripts if needed
4. Validate Bonsai version compatibility

### Phase 3: Package Verification

1. Parse Bonsai.config for required packages
2. Scan installed packages directory
3. Compare versions and dependencies
4. Auto-reinstall if mismatches detected

### Phase 4: Stimulus Table Generation

1. Generate session UUID and metadata
2. Create session-specific stimulus CSV using on-the-fly generation
3. Use session-specific random seed for unique stimulus sequences
4. Place stimulus table in session output folder

### Phase 5: Experiment Execution

1. Prepare experiment parameters with generated stimulus table path
2. Launch Bonsai workflow with --start --no-editor
3. Monitor process and capture output
4. Capture and log experiment output

### Phase 6: Cleanup & Data Management

1. Ensure proper process termination
2. Save experiment data and metadata
3. Generate session reports
4. Clean up temporary resources

## Configuration

### Parameter File Structure

The launcher uses JSON parameter files with the following structure:

```json
{
    "repository_url": "https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing.git",
    "commit_hash": "main", 
    "local_repository_path": "C:/BonsaiDataPredictiveProcessingTest",
    "bonsai_path": "code/stimulus-control/src/Mindscope/generic_oddball.bonsai",
    "session_type": "sensorimotor_mismatch",
    "mouse_id": "test_mouse",
    "user_id": "test_user"
}
```

### Key Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `repository_url` | GitHub repository URL | Yes | - |
| `commit_hash` | Specific commit or branch name | Yes | - |
| `local_repository_path` | Local directory for repository | Yes | - |
| `bonsai_path` | Relative path to workflow file | Yes | - |
| `session_type` | Experimental session type for stimulus generation | Yes | - |
| `mouse_id` | Subject identifier | Yes | - |
| `user_id` | Experimenter identifier | Yes | - |
| `bonsai_exe_path` | Relative path to Bonsai executable | No | `tools/Bonsai.startstop/Bonsai.exe` |
| `bonsai_setup_script` | Path to package installation script | No | `code/stimulus-control/bonsai/setup.cmd` |

### Session Types

The launcher supports the following session types for automatic stimulus table generation:

| Session Type | Description | Typical Duration |
|-------------|-------------|------------------|
| `visual_mismatch` | Standard oddball with orientation deviants | ~66 minutes |
| `sensorimotor_mismatch` | Motor coupling with mismatch blocks | ~66 minutes |
| `sequence_mismatch` | Sequential learning with pattern violations | ~66 minutes |
| `duration_mismatch` | Temporal oddball with duration deviants | ~66 minutes |
| `sequence_no_oddball` | Long blocks without oddball trials | ~66 minutes |
| `sensorimotor_no_oddball` | Long motor coupling without mismatches | ~66 minutes |

Each session type generates a unique stimulus table with appropriate control blocks and RF mapping.

## Stimulus Table Generation

### On-the-Fly Generation

The launcher automatically generates stimulus tables for each experimental session using the integrated CSV generator. This approach provides several advantages:

- **Unique Stimulus Sequences**: Each session uses a session-specific random seed, ensuring no two sessions have identical stimulus presentations
- **Reproducible Results**: The random seed is logged with session metadata, allowing exact replication when needed
- **Simplified Workflow**: No need to pre-generate or manage static CSV files
- **Reduced Storage**: Only the active session's stimulus table is stored, eliminating large collections of unused CSV files

### Generation Process

1. **Session Initialization**: When a session starts, the launcher extracts the `session_type` parameter
2. **Seed Generation**: A unique random seed is created based on the session UUID, session type, and current time
3. **CSV Creation**: The generator script is called with the session type, output path (in session folder), and unique seed
4. **Parameter Update**: The `stimulus_table_path` parameter is updated to point to the generated CSV file
5. **Bonsai Launch**: The workflow is launched with the path to the newly generated stimulus table

### Logging and Traceability

All stimulus generation is fully logged:
- Generator script execution and output
- Random seed used for generation
- Number of trials generated
- Output file location and verification
- Any errors or warnings during generation

This ensures complete traceability and reproducibility of experimental conditions.

## Package Management

### Automatic Package Verification

The launcher automatically verifies that installed Bonsai packages match the requirements specified in `Bonsai.config`. This includes:

- **Version Matching**: Ensures exact version compatibility
- **Dependency Resolution**: Verifies all package dependencies
- **Missing Package Detection**: Identifies packages that need installation

### Auto-Reinstall System

The launcher automatically fixes package issues when detected:

1. **Detection**: Identifies version mismatches or missing packages
2. **Cleanup**: Removes the entire Packages directory for a clean slate
3. **Reinstallation**: Runs the setup script to install all packages fresh
4. **Verification**: Re-checks packages to confirm the fix worked

This ensures experiments always run with the correct package versions.

## Usage Examples

### Basic Usage

```python
from bonsai_experiment_launcher import BonsaiExperiment

# Create experiment instance
experiment = BonsaiExperiment()

# Run experiment with parameter file
success = experiment.run('experiment_params.json')

if success:
    print("Experiment completed successfully!")
else:
    print("Experiment failed - check logs for details")
```

### Testing and Development

```bash
# Test the launcher with sample parameters
python test_bonsai_launcher.py

# Use custom parameter file
python test_bonsai_launcher.py --param-file my_params.json
```

### Integration with Camstim Agent

The launcher is designed to be executed by the **camstim agent** - one of the Allen Institute's internal session management system. The integration works as follows:

#### Agent-Based Execution
- **Agent receives**: A script path and YAML parameter file from the experiment scheduling system
- **Agent calls**: The experimental launcher with the provided parameters
- **Agent monitors**: Experiment execution and handles results

#### Parameter Flow
```
1. Experiment scheduling system → YAML parameters → camstim agent
2. camstim agent → experimental launcher
3. experimental launcher → experiment execution → results back to agent
```

#### Camstim Infrastructure Integration
- **Configuration**: Reads from `C:/ProgramData/AIBS_MPE/camstim/config/stim.cfg`
- **Data Storage**: Saves experiment data to camstim-compatible pickle files
- **Session Management**: Uses camstim session UUID format and metadata structure
- **Logging**: Compatible with camstim logging standards and tracking formats
- **Process Management**: Integrates with camstim's process monitoring and cleanup

#### Expected Usage Pattern
```python
# This is typically called by the camstim agent, not directly by users
from bonsai_experiment_launcher import BonsaiExperiment

# Agent provides the YAML file path
experiment = BonsaiExperiment()
success = experiment.run('agent_provided_params.json')  # Agent converts YAML→JSON

# Results are automatically saved in camstim-compatible format
# Agent handles success/failure reporting back to scheduling system
```

#### Camstim-Compatible Output Format
The launcher generates pickle files with the same structure as standard camstim experiments:
- Platform and session metadata
- Experiment parameters and checksums
- Behavioral data integration points
- LIMS-compatible data structure

## See Also

- [Bonsai Instructions](bonsai_instructions.md) - Basic Bonsai usage
- [Bonsai for Python Programmers](bonsai_for_python_programmers.md) - Integration concepts
- [Standard Oddball](standard-oddball.md) - Example experiment workflow

<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/allenneuraldynamics/openscope-community-predictive-processing/discussions/new?category=q-a&title=Discussion%3A%20stimuli/experimental-launcher" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->
