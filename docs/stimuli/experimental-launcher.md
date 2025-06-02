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

1. **BonsaiExperiment Class** (`bonsai_experiment_launcher.py`)
   - Main orchestrator for experiment execution
   - Handles all phases of experiment lifecycle
   - Provides error handling and recovery mechanisms

2. **Parameter Management**
   - JSON-based configuration system
   - Environment-specific settings (camstim config integration)
   - Session metadata and UUID generation

3. **Process Management**
   - Windows job object integration for proper cleanup
   - Process monitoring and timeout handling
   - Signal handling for graceful shutdown

## Experiment Lifecycle

### Phase 1: Repository Setup
```
1. Clone/update repository from GitHub
2. Checkout specific commit or branch
3. Verify repository integrity
4. Set up local working directory
```

### Phase 2: Bonsai Installation
```
1. Locate Bonsai executable in repository
2. Verify Bonsai installation
3. Run setup scripts if needed
4. Validate Bonsai version compatibility
```

### Phase 3: Package Verification
```
1. Parse Bonsai.config for required packages
2. Scan installed packages directory
3. Compare versions and dependencies
4. Auto-reinstall if mismatches detected
```

### Phase 4: Experiment Execution
```
1. Generate session UUID and metadata
2. Prepare experiment parameters
3. Launch Bonsai workflow with --start --no-editor
4. Monitor process and handle timeouts
5. Capture and log experiment output
```

### Phase 5: Cleanup & Data Management
```
1. Ensure proper process termination
2. Save experiment data and metadata
3. Generate session reports
4. Clean up temporary resources
```

## Configuration

### Parameter File Structure

The launcher uses JSON parameter files with the following structure:

```json
{
    "repository_url": "https://github.com/AllenNeuralDynamics/openscope-community-predictive-processing.git",
    "commit_hash": "main",
    "local_repository_path": "C:/BonsaiDataPredictiveProcessingTest",
    "bonsai_path": "code/stimulus-control/src/Standard_oddball_slap2.bonsai",
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
| `mouse_id` | Subject identifier | Yes | - |
| `user_id` | Experimenter identifier | Yes | - |
| `bonsai_exe_path` | Relative path to Bonsai executable | No | `code/stimulus-control/bonsai/Bonsai.exe` |
| `bonsai_setup_script` | Path to package installation script | No | `code/stimulus-control/bonsai/setup.cmd` |

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