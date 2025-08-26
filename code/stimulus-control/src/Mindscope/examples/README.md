# Stimulus Table Examples and Analysis

This directory contains example stimulus tables and analysis tools for the OpenScope predictive processing protocols.

## Contents

### Example Stimulus Tables
- `visual_mismatch_example.csv` - Visual mismatch (standard oddball) protocol
- `sequence_mismatch_example.csv` - Sequence mismatch protocol  
- `sensorimotor_mismatch_example.csv` - Sensory-motor mismatch protocol
- `duration_mismatch_example.csv` - Duration mismatch protocol
- `*_no_oddball_example.csv` - Control protocols without oddball events

### Analysis Tools
- `analyze_stimulus_tables.py` - Comprehensive analysis and visualization script
- `analysis_plots/` - Generated analysis plots and summary statistics

## Usage

### Generate Example Tables
From the parent directory (`../`), run:
```bash
python generate_experiment_csv.py --examples
```

### Run Analysis
```bash
# Analyze all protocols
python analyze_stimulus_tables.py

# Analyze specific protocol
python analyze_stimulus_tables.py --session-type visual_mismatch

# Custom output directory
python analyze_stimulus_tables.py --output-dir my_plots
```

## Analysis Output

The analysis script generates for each protocol:

1. **Structure Analysis Plot** (`*_structure_analysis.png`):
   - Block timeline showing experimental phases
   - Grating orientation progression over time
   - Oddball event distribution

2. **Summary Statistics** (`*_summary_stats.txt`):
   - Total trials and session duration
   - Block-by-block breakdown
   - Trial type statistics
   - Oddball analysis metrics

## Features

### Comprehensive Visualization
- **Block Structure**: Shows timing and organization of experimental blocks
- **Stimulus Progression**: Displays how stimulus parameters evolve over time
- **Oddball Distribution**: Highlights mismatch events and their temporal distribution

### Full Trial Analysis
- No sampling - uses complete trial datasets
- Preserves all oddball and RF mapping trials
- Accurate temporal relationships

### Multiple Session Types
Supports analysis of all experimental protocols:
- Visual mismatch (orientation oddballs)
- Sequence mismatch (pattern violations)
- Sensory-motor mismatch (motor-visual coupling)
- Duration mismatch (temporal violations)
- Control protocols

## Integration

The generated plots are automatically integrated into the project documentation:
- Copied to `docs/img/stimuli/` for documentation use
- Referenced in protocol documentation files
- Used in main project overview

This provides researchers with clear, data-driven visualizations of experimental structure and expected timing patterns.
