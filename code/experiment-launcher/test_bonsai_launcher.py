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

# Set up advanced logging configuration
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):  # Python 2.7 compatible way to check directory
    os.makedirs(log_dir)  # Using os.makedirs instead of Path.mkdir

# Create file handler
log_file = os.path.join(log_dir, "bonsai_launcher_{0}.log".format(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
file_handler = logging.FileHandler(log_file)  # No need to convert Path to string
file_handler.setFormatter(log_formatter)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

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
    logging.info("="*80)
    logging.info("Starting Bonsai Experiment Test at {0}".format(datetime.datetime.now().isoformat()))
    logging.info("Platform: {0}".format(platform.platform()))
    logging.info("Python version: {0}".format(platform.python_version()))
    logging.info("="*80)
    
    # Parse command-line arguments
    args = parse_arguments()
    
    # Get the path to the parameter JSON file
    param_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.param_file)
    
    # Check if the parameter file exists
    if not os.path.exists(param_file_path):
        logging.error("Parameter file does not exist: {0}".format(param_file_path))
        return False
    
    logging.info("Using parameter file: {0}".format(param_file_path))
    
    # Load the parameters from JSON file
    with open(param_file_path, 'r') as f:
        params = json.load(f)
    
    logging.info("Loaded parameters from JSON file")
    
    # Override Bonsai executable path from JSON if provided
    if 'bonsai_exe_path' in params:
        bonsai_experiment_launcher.BONSAI_EXE_PATH = params['bonsai_exe_path']
        logging.info("Using Bonsai executable from JSON: {0}".format(params['bonsai_exe_path']))
    
    # Build the full workflow path if needed
    if 'bonsai_path' in params and 'workflow_dir' in params:
        # If bonsai_path is not absolute, prepend the workflow_dir
        if not os.path.isabs(params['bonsai_path']):
            full_workflow_path = os.path.join(params['workflow_dir'], params['bonsai_path'])
            params['bonsai_path'] = full_workflow_path
            logging.info("Using workflow: {0}".format(params['bonsai_path']))
    
    # Verify workflow exists
    if 'bonsai_path' in params and not os.path.exists(params['bonsai_path']):
        logging.error("Workflow file does not exist: {0}".format(params['bonsai_path']))
        return False
    
    # Create an instance of BonsaiExperiment and run the experiment
    try:
        experiment = BonsaiExperiment()
        success = experiment.run(param_file_path)
        
        if success:
            logging.info("Experiment completed successfully!")
        else:
            logging.error("Experiment failed!")
            
    except Exception as e:
        logging.exception("Exception running experiment: {0}".format(e))
        return False
    finally:
        logging.info("Cleaning up resources...")
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    logging.info("Test completed in %.2f seconds" % elapsed_time)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)