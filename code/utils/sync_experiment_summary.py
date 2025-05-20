#!/usr/bin/env python3
"""
Script to synchronize the experiment summary page with individual experiment markdown files.
This script scans all experiment markdown files, extracts key information, and updates
the experiment summary tables accordingly.
"""

import os
import re
import glob
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
EXPERIMENTS_DIR = DOCS_DIR / "experiments"
SUMMARY_FILE = DOCS_DIR / "experiment-summary.md"

# Regular expressions to extract information from experiment files
MOUSE_ID_REGEX = r"\*\*Mouse ID:\*\* (\w+)"
DATE_REGEX = r"\*\*Date:\*\* (\d{4}-\d{2}-\d{2})"
EXPERIMENTER_REGEX = r"\*\*Experimenter:\*\* (.+)"
RIG_REGEX = r"\*\*Rig / Setup ID:\*\* (.+)"
PROTOCOL_REGEX = r"\*\*Protocol followed:\*\* (.+)"


def extract_info_from_file(file_path):
    """Extract experiment information from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract basic information using regex
    mouse_id_match = re.search(MOUSE_ID_REGEX, content)
    date_match = re.search(DATE_REGEX, content)
    experimenter_match = re.search(EXPERIMENTER_REGEX, content)
    rig_match = re.search(RIG_REGEX, content)
    protocol_match = re.search(PROTOCOL_REGEX, content)
    
    # Create a relative path for the link - this should work with nested paths
    rel_path = os.path.relpath(file_path, DOCS_DIR)
    
    # Replace backslashes with forward slashes for web links
    rel_path = rel_path.replace('\\', '/')
    
    return {
        'mouse_id': mouse_id_match.group(1) if mouse_id_match else "N/A",
        'date': date_match.group(1) if date_match else "Unknown",
        'experimenter': experimenter_match.group(1) if experimenter_match else "Unknown",
        'rig': rig_match.group(1) if rig_match else "Unknown",
        'protocol': protocol_match.group(1) if protocol_match else "Unknown",
        'file_path': rel_path,
    }


def generate_table_for_platform(experiments, platform_name):
    """Generate a markdown table for a specific recording platform."""
    if not experiments:
        return f"### {platform_name} Experiments\n\n*No {platform_name} experiments have been conducted yet.*\n"
    
    # Sort experiments by date
    sorted_exps = sorted(experiments, key=lambda x: x['date'], reverse=True)
    
    table = f"### {platform_name} Experiments\n\n"
    table += "| Date | Mouse ID | Protocol | Session Notes |\n"
    table += "|------|----------|----------|---------------|\n"
    
    for exp in sorted_exps:
        link_text = f"[Session Details]({exp['file_path']})"
        table += f"| {exp['date']} | {exp['mouse_id']} | {exp['protocol']} | {link_text} |\n"
    
    return table


def update_summary_file(platform_tables):
    """Update the experiment summary file with new tables."""
    # Read the header part of the file (up to the first platform section)
    with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the header content (everything before the first platform section)
    header_match = re.search(r'^(.*?)(?=### SLAP2 Experiments|### Neuropixels Experiments|### Mesoscope Experiments)', 
                            content, re.DOTALL)
    
    if header_match:
        header = header_match.group(1)
    else:
        # If no match found, use a default header
        header = """# Experiment Summary

This page provides a comprehensive overview of all experiments conducted as part of the OpenScope Community Predictive Processing project. It includes links to detailed session notes for each completed experiment and indicates planned experiments for platforms where data collection has not yet begun.

## Overview by Platform

The project utilizes three complementary neural recording platforms, each offering unique capabilities for studying predictive processing. Below is a summary of experiments conducted on each platform.

"""
    
    # Extract the footer (Related Documents section)
    footer_match = re.search(r'(## Related Documents.*?)$', content, re.DOTALL)
    footer = footer_match.group(1) if footer_match else """
## Related Documents

- **[Experimental Plan](experimental-plan.md)**: Overview of experimental paradigms and approaches
- **[Detailed Experimental Plan](detailed-experimental-plan.md)**: Comprehensive methodology and experimental design
- **[Analysis Plan](analysis-plan.md)**: Methods for analyzing the collected data
- **[Hardware Overview](hardware-overview.md)**: Information about the recording platforms used
- **[Project Tracking](project-tracking.md)**: Current progress and status of all project components
"""

    # Create the new content by combining header, platform tables, and footer
    new_content = header.rstrip() + "\n\n"
    
    # Add platform tables in order
    for platform in ['SLAP2', 'Neuropixels', 'Mesoscope']:
        new_content += platform_tables[platform] + "\n\n"
    
    # Add footer
    new_content += footer
    
    # Write the updated content to the file
    with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)


def main():
    """Main function to sync experiment summary with individual files."""
    # Find all experiment markdown files
    experiment_files = []
    
    # Check both direct files in experiments/ and nested directories
    experiment_files.extend(glob.glob(str(EXPERIMENTS_DIR / "*.md")))
    experiment_files.extend(glob.glob(str(EXPERIMENTS_DIR / "**" / "*.md")))
    
    # Extract information from each file and categorize by platform
    platform_experiments = defaultdict(list)
    
    for file_path in experiment_files:
        info = extract_info_from_file(file_path)
        # Categorize by platform based on the rig information
        if "SLAP2" in info['rig']:
            platform_experiments['SLAP2'].append(info)
        elif "Neuropixels" in info['rig']:
            platform_experiments['Neuropixels'].append(info)
        elif "Mesoscope" in info['rig']:
            platform_experiments['Mesoscope'].append(info)
        else:
            # If rig is not specified, try to infer from the file path
            file_lower = file_path.lower()
            if "slap2" in file_lower:
                platform_experiments['SLAP2'].append(info)
            elif "neuropixels" in file_lower:
                platform_experiments['Neuropixels'].append(info)
            elif "mesoscope" in file_lower:
                platform_experiments['Mesoscope'].append(info)
            else:
                print(f"Warning: Could not determine platform for {file_path}")
    
    # Generate tables for each platform
    platform_tables = {}
    for platform in ['SLAP2', 'Neuropixels', 'Mesoscope']:
        platform_tables[platform] = generate_table_for_platform(
            platform_experiments[platform], platform
        )
    
    # Update the summary file
    update_summary_file(platform_tables)
    print(f"Successfully updated {SUMMARY_FILE}")


if __name__ == "__main__":
    main()