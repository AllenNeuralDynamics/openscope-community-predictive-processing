#!/usr/bin/env python
"""
Test script for the Bonsai Experiment Launcher

This script directly tests the BonsaiExperiment class with a specific Bonsai executable
and workflow path without going through the agent.

Usage:
    python test_bonsai_launcher.py [--param-file sample_params.json]
"""

import os
import sys
import json
import logging
import datetime
import time
import platform
import argparse

# Simple console-only logging setup
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors
    format='%(levelname)s: %(message)s'
)

# Now import the BonsaiExperiment class
import bonsai_experiment_launcher
from bonsai_experiment_launcher import BonsaiExperiment

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Test Bonsai Experiment Launcher')
    parser.add_argument('--param-file', default='sample_params.json', 
                        help='JSON parameter file to use')
    return parser.parse_args()

def main():
    """
    Test the BonsaiExperiment class using parameters from JSON file.
    """
    start_time = time.time()
    print("=" * 60)
    print("Bonsai Experiment Launcher Test")
    print("Started at: {0}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("=" * 60)
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Get the path to the parameter JSON file
    param_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.param_file)
    
    # Check if the parameter file exists
    if not os.path.exists(param_file_path):
        print("ERROR: Parameter file does not exist: {0}".format(param_file_path))
        return False
    
    print("Using parameter file: {0}".format(args.param_file))
    
    # Load the parameters from JSON file
    with open(param_file_path, 'r') as f:
        params = json.load(f)
    
    print("Repository: {0}".format(params.get('repository_url', 'N/A')))
    print("Workflow: {0}".format(params.get('bonsai_path', 'N/A')))
    print("-" * 60)

    # Create an instance of BonsaiExperiment and run the experiment
    try:
        experiment = BonsaiExperiment()
        success = experiment.run(param_file_path)
        
        print("-" * 60)
        if success:
            print("EXPERIMENT COMPLETED SUCCESSFULLY!")
        else:
            print("EXPERIMENT FAILED!")
            
    except Exception as e:
        print("EXCEPTION: {0}".format(e))
        return False
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print("Total time: {0:.1f} seconds".format(elapsed_time))
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)