#!/usr/bin/env python
"""
Bonsai Experiment Launcher

This script launches a Bonsai workflow with parameters from a JSON file,
similar to how openscope_mousemotion/ExperimentCode.py works.

Usage:
    python bonsai_experiment_launcher.py [path_to_parameters.json]

The JSON file should contain experiment parameters that will be passed to Bonsai.
"""

import os
import sys
import time
import signal
import logging
import datetime
import platform
import subprocess
import yaml  
import socket
import uuid
import cPickle as pickle
import ConfigParser
import io
import hashlib
import atexit
import psutil
import threading
import shutil  # Added for directory operations

# Import Windows-specific modules for process management
try:
    import win32job
    import win32api
    import win32con
    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    WINDOWS_MODULES_AVAILABLE = False
    logging.warning("Windows modules (win32job, win32api, win32con) not available. Process management will be limited.")

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Constants
BONSAI_EXE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "stimulus-control", "bonsai", "Bonsai.exe"
))

# Default configuration for CamStim-like behavior
if "Windows" in platform.system():
    CAMSTIM_DIR = "C:/ProgramData/AIBS_MPE/camstim/"
else:
    CAMSTIM_DIR = os.path.expanduser('~/.camstim/')

OUTPUT_DIR = os.path.join(CAMSTIM_DIR, "data")
KILL_THRESHOLD = float(os.getenv('CAMSTIM_VMEM_THRESHOLD', 90))

DEFAULTCONFIG = """
[Behavior]
nidevice = Dev1
volume_limit = 1.5
sync_sqr = True
sync_sqr_loc = (-300,-300)
sync_pulse = True
pulseOnRisingEdge = True
pulsedigitalport = 1
pulsedigitalline = 0
sync_nidevice = Dev1
display_time = True
mouse_id = test_mouse
user_id = test_user

[Encoder]
nidevice = Dev1
encodervinchannel = 0
encodervsigchannel = 1

[Reward]
reward_volume = 0.007
nidevice = Dev1
reward_lines = [(0,0)]
invert_logic = False

[Licksensing]
nidevice = Dev1
lick_lines = [(0,1)]

[Sync]
sync_sqr = True
sync_sqr_loc = (-300,-300)

[Stim]
showmouse = False
miniwindow = False
fps = 60.000
monitor_brightness = 30
monitor_contrast = 50

[LIMS]
lims_upload = False
lims_dummy = True

[SweepStim]
backupdir = None
mouseid = 'test'
userid = 'user'
bgcolor = (0,0,0)
controlstream = True
trigger = None
triggerdiport = 0
triggerdiline = 0
trigger_delay_sec = 0.0
savesweeptable = True
eyetracker = False

[Display]
monitor = 'testMonitor'
screen = 1
projectorType = 'Projector.Normal'
warp = 'Warp.Disabled'
warpfile = None
flipHorizontal = False
flipVertical = False
eyepoint = (0.5,0.5)

[Datastream]
data_export = False
data_export_port = 5000
data_export_rep_port = 5001
"""


class BonsaiExperiment(object):
    """
    Main experiment class that handles launching Bonsai and 
    saving experiment data
    """
    
    def __init__(self):
        """Initialize the experiment with configuration data"""
        self.platform_info = self.get_platform_info()
        self.output_path = None
        self.params = {}
        self.bonsai_process = None
        self.start_time = None
        self.stop_time = None
        self.config = {}
        self.config_path = os.path.join(CAMSTIM_DIR, "config/stim.cfg")
        
        # Initialize session tracking variables similar to camstim's agent
        self.mouse_id = ""
        self.user_id = ""
        self.session_uuid = str(uuid.uuid4())
        self.session_output_path = ""
        self.script_checksum = None
        self.params_checksum = None
        self._percent_used = None
        self._restarted = False
        
        # Add variables to capture stdout and stderr
        self.stdout_data = []
        self.stderr_data = []
        self._output_threads = []
        
        # Create Windows job object for process management
        if WINDOWS_MODULES_AVAILABLE:
            try:
                self.hJob = win32job.CreateJobObject(None, "BonsaiJobObject")
                extended_info = win32job.QueryInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation)
                extended_info['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                win32job.SetInformationJobObject(self.hJob, win32job.JobObjectExtendedLimitInformation, extended_info)
                logging.info("Windows job object created for process management")
            except Exception as e:
                logging.warning("Failed to create Windows job object: %s" % e)
                self.hJob = None
        else:
            self.hJob = None
        
        # Register exit handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def get_platform_info(self):
        """Gets system and version information."""
        info = {
            "python": sys.version.split()[0],
            "os": (platform.system(), platform.release(), platform.version()),
            "hardware": (platform.processor(), platform.machine()),
            "computer_name": platform.node(),
            "rig_id": os.environ.get('RIG_ID', socket.gethostname()),
        }
        return info
    
    def load_parameters(self, param_file):
        """
        Load parameters from a JSON file
        
        Args:
            param_file (str): Path to the JSON parameter file
        """
        try:
            if param_file:
                with open(param_file, 'r') as f:
                    import json
                    self.params = json.load(f)
                    logging.info("Loaded parameters from %s" % param_file)
                    
                    # Generate parameter checksum for provenance tracking, like in camstim agent
                    with open(param_file, 'rb') as f:
                        self.params_checksum = hashlib.md5(f.read()).hexdigest()
                    logging.info("Parameter file checksum: %s" % self.params_checksum)
            else:
                logging.warning("No parameter file provided, using default parameters. THIS IS NOT THE EXPECTED BEHAVIOR FOR PRODUCTION RUNS")
                self.params = {}
            
            # Set default values for optional parameters
            if 'bonsai_exe_path' not in self.params:
                self.params['bonsai_exe_path'] = 'code/stimulus-control/bonsai/Bonsai.exe'
            
            if 'bonsai_setup_script' not in self.params:
                self.params['bonsai_setup_script'] = 'code/stimulus-control/bonsai/setup.cmd'
                
            # Extract mouse_id and user_id specifically, matching camstim's agent behavior
            self.mouse_id = self.params.get("mouse_id", "")
            self.user_id = self.params.get("user_id", "")
                
            # After loading JSON parameters, load and merge CamStim config
            self.load_config()
            
            # If mouse_id and user_id were not in JSON params, try to get them from config
            if not self.mouse_id:
                self.mouse_id = self.config.get("Behavior", {}).get("mouse_id", "test_mouse")
                self.params["mouse_id"] = self.mouse_id
                
            if not self.user_id:
                self.user_id = self.config.get("Behavior", {}).get("user_id", "test_user")
                self.params["user_id"] = self.user_id
                
            # Log mouse and user ID
            logging.info("Using mouse_id: %s, user_id: %s" % (self.mouse_id, self.user_id))
            
            # Save the merged configuration to a file for Bonsai to access
            if param_file:
                self.save_config_file(param_file)
                
        except Exception as e:
            logging.error("Failed to load parameters: %s" % e)
            raise
    
    def load_config(self):
        """
        Load configuration from CamStim config files, similar to what's done in BehaviorBase
        """
        # Check if config directory exists, create if not
        config_dir = os.path.dirname(self.config_path)
        if not os.path.isdir(config_dir):
            os.makedirs(config_dir)
            
        # Check if config file exists, create if not
        if not os.path.isfile(self.config_path):
            logging.info("Config file not found, creating default at %s" % self.config_path)
            with open(self.config_path, 'w') as f:
                f.write(DEFAULTCONFIG)
                
        # Load configuration from file
        logging.info("Loading configuration from %s" % self.config_path)
        
        try:
            config = ConfigParser.RawConfigParser()
            config.readfp(io.BytesIO(DEFAULTCONFIG))
            config.read(self.config_path)
            
            # Load all standard sections that are used in camstim
            self.load_config_section("Behavior", config)
            self.load_config_section("Encoder", config)
            self.load_config_section("Reward", config)
            self.load_config_section("Licksensing", config)
            self.load_config_section("Sync", config)
            
            # Load additional sections discovered in camstim code
            self.load_config_section("Stim", config)
            self.load_config_section("LIMS", config)
            self.load_config_section("SweepStim", config)
            self.load_config_section("Display", config)
            self.load_config_section("Datastream", config)
            
        except Exception as e:
            logging.warning("Error reading config file: %s" % e)
    
    def load_config_section(self, section, config):
        """
        Load a section from the config file
        
        Args:
            section (str): Section name
            config (ConfigParser): ConfigParser object
        """
        try:
            if section not in self.config:
                self.config[section] = {}
                
            if config.has_section(section):
                for key, value in config.items(section):
                    try:
                        # Convert string to Python object
                        self.config[section][key] = eval(value)
                    except (SyntaxError, NameError):
                        # If eval fails, keep as string
                        self.config[section][key] = value
                        
            logging.debug("Loaded config section: %s" % section)
            
        except Exception as e:
            logging.warning("Failed to load config section %s: %s" % (section, e))
    
    def save_config_file(self, param_file_path):
        """
        Save the configuration data to a JSON file in the same directory
        as the input parameter file, with '_config' appended to the filename.
        
        The saved file contains three distinct sections:
        - params: stimulus parameters (can change between experiments)
        - config: hardware configurations associated with the rig (don't change)
        - metadata: session-specific parameters (change all the time)
        
        Args:
            param_file_path (str): Path to the original parameter file
        """
        if not param_file_path:
            logging.warning("No parameter file path provided, cannot save config file")
            return None
            
        try:
            # Parse the original filename and create the new config filename
            param_dir = os.path.dirname(param_file_path)
            param_basename = os.path.basename(param_file_path)
            param_name, param_ext = os.path.splitext(param_basename)
            
            # Create the config filename with '_config' suffix
            config_filename = param_name + "_config" + param_ext
            config_file_path = os.path.join(param_dir, config_filename)
            
            # Prepare the data to save with clear separation:
            # - session_params: stimulus parameters (can change between experiments)
            # - hardware_config: hardware configurations associated with the rig (don't change)
            # - session_metadata: session-specific parameters (change all the time)
            config_data = {
                'session_params': self.params,
                'hardware_config': self.config,
                'session_metadata': {
                    'generated_from': param_file_path,
                    'generation_time': datetime.datetime.now().isoformat(),
                    'session_uuid': self.session_uuid,
                    'mouse_id': self.mouse_id,
                    'user_id': self.user_id,
                    'platform_info': self.platform_info
                }
            }
            
            # Save to JSON file
            import json
            with open(config_file_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logging.info("Saved configuration with separate params, config, and metadata to: %s" % config_file_path)
            
            # Also store the config file path in params so Bonsai can access it
            self.params['config_file_path'] = config_file_path
            
            return config_file_path
            
        except Exception as e:
            logging.error("Failed to save config file: %s" % e)
            return None
    
    def setup_output_path(self, output_path=None):
        """
        Set up the output path for the experiment data, using the same pattern
        as camstim's agent.
        
        Args:
            output_path (str, optional): Specific output path to use
        
        Returns:
            str: The output file path
        """
        if output_path:
            # Use provided output path
            output_folder = os.path.dirname(output_path)
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder)
            self.session_output_path = output_path
        else:
            # Generate output path based on datetime, mouse ID, and session UUID
            dt_str = datetime.datetime.now().strftime('%y%m%d%H%M%S')
            mouse_id = self.mouse_id if self.mouse_id else "unknown_mouse"
            filename = "%s_%s_%s.pkl" % (dt_str, mouse_id, self.session_uuid)
            
            # Create output directory if it doesn't exist
            if not os.path.isdir(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)
                
            self.session_output_path = os.path.join(OUTPUT_DIR, filename)
            
        logging.info("Session output path: %s" % self.session_output_path)
        self.params["output_path"] = self.session_output_path
        
        return self.session_output_path
            
    def get_bonsai_args(self):
        """
        Construct command-line arguments for Bonsai
        
        Returns:
            list: Command-line arguments for Bonsai
        """
        bonsai_path = self.params.get('bonsai_path', None)
        if not bonsai_path:
            raise ValueError("No Bonsai workflow path specified in parameters")
            
        # Convert relative path to absolute path using repository
        workflow_path = self.get_absolute_path_from_repo(bonsai_path)
        if not workflow_path:
            # Fall back to original relative path logic for backward compatibility
            workflow_path = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                "..", "stimulus-control", "src", bonsai_path
            ))
        
        if not os.path.exists(workflow_path):
            raise ValueError("Bonsai workflow not found at: %s" % workflow_path)
        
        # Generate workflow checksum for provenance tracking, like in camstim agent
        with open(workflow_path, 'rb') as f:
            self.script_checksum = hashlib.md5(f.read()).hexdigest()
        logging.info("Workflow file checksum: %s" % self.script_checksum)
            
        # Base arguments - use correct Bonsai CLI syntax:
        # 1. Bonsai executable
        # 2. Workflow file as positional argument
        args = [BONSAI_EXE_PATH, workflow_path]
        
        # Run in non-interactive application mode with both flags
        args.append("--start")
        args.append("--no-editor")
        
        # Pass the config file path to Bonsai if available
        config_file_path = self.params.get('config_file_path')
        if config_file_path and os.path.exists(config_file_path):
            args.extend(["--property", "ConfigFilePath=%s" % config_file_path])
            logging.info("Passing config file to Bonsai: %s" % config_file_path)
        
        # Log the complete command
        logging.info("Command: %s" % " ".join(args))
        return args
        
    def start_bonsai(self):
        """Start the Bonsai workflow as a subprocess"""
        logging.info("Mouse ID: %s, User ID: %s, Session UUID: %s" % (self.mouse_id, self.user_id, self.session_uuid))
        
        # Store current memory usage for runaway detection, like in camstim agent
        vmem = psutil.virtual_memory()
        self._percent_used = vmem.percent
        
        # Ensure output path is set up
        self.setup_output_path(self.params.get("output_path", None))
        
        # Get command-line arguments
        args = self.get_bonsai_args()
        
        logging.info("Starting Bonsai with arguments: %s" % ' '.join(args))
        
        try:
            # Start Bonsai as a subprocess with pipe for stdout and stderr
            self.bonsai_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,  # Use text mode for output handling
                bufsize=1  # Line buffered
            )
            
            # Create threads to read output streams in real-time
            self._start_output_readers()
            
            # If Windows modules are available, assign process to job object
            if WINDOWS_MODULES_AVAILABLE and self.hJob:
                try:
                    perms = win32con.PROCESS_TERMINATE | win32con.PROCESS_SET_QUOTA
                    hProcess = win32api.OpenProcess(perms, False, self.bonsai_process.pid)
                    win32job.AssignProcessToJobObject(self.hJob, hProcess)
                    logging.info("Bonsai process %s assigned to job object for proper cleanup" % self.bonsai_process.pid)
                except Exception as e:
                    logging.warning("Failed to assign process to job object: %s" % e)
            
            self.start_time = datetime.datetime.now()
            logging.info("Bonsai started at %s" % self.start_time)
            
            # Log the experiment start with mouse ID and user ID for tracking
            logging.info("MID, %s, UID, %s, Action, Executing, Checksum, %s, Json_checksum, %s" % (self.mouse_id, self.user_id, self.script_checksum, self.params_checksum))
            
            # Monitor Bonsai process
            self._monitor_bonsai()
            
        except Exception as e:
            logging.error("Failed to start Bonsai: %s" % e)
            raise

    def _start_output_readers(self):
        """Start threads to read stdout and stderr in real-time"""
        # Clear previous data
        self.stdout_data = []
        self.stderr_data = []
        
        # Define reader functions that append to the data lists
        def stdout_reader():
            for line in iter(self.bonsai_process.stdout.readline, ''):
                if line:
                    self.stdout_data.append(line.rstrip())
                    logging.info("Bonsai output: %s" % line.rstrip())
            self.bonsai_process.stdout.close()
            
        def stderr_reader():
            for line in iter(self.bonsai_process.stderr.readline, ''):
                if line:
                    self.stderr_data.append(line.rstrip())
                    logging.error("Bonsai error: %s" % line.rstrip())
            self.bonsai_process.stderr.close()
        
        # Start reader threads
        self._output_threads = [
            threading.Thread(target=stdout_reader),
            threading.Thread(target=stderr_reader)
        ]
        
        # Set as daemon threads so they don't block program exit
        for thread in self._output_threads:
            thread.daemon = True
            thread.start()

    def _monitor_bonsai(self):
        """Monitor the Bonsai process until it completes"""
        logging.info("Monitoring Bonsai process...")
        
        try:
            # Check for process memory usage and kill if it exceeds threshold
            try:
                process = psutil.Process(self.bonsai_process.pid)
            except psutil.NoSuchProcess:
                logging.warning("Process ended unexpectedly")
                return
                
            # Wait for Bonsai process to complete or check for runaway memory usage
            while self.bonsai_process.poll() is None:
                try:
                    # Check for memory usage every second
                    vmem = psutil.virtual_memory()
                    if vmem.percent > float(self._percent_used) + KILL_THRESHOLD:
                        logging.warning("Detected runaway process, memory usage: %s%% (threshold: %s%%)" % (vmem.percent, float(self._percent_used) + KILL_THRESHOLD))
                        self.kill_process()
                        break
                except Exception as e:
                    logging.warning("Error checking process status: %s" % e)
                    
                # Sleep a bit before checking again
                time.sleep(0.5)
                
            # Wait for output reader threads to finish
            for thread in self._output_threads:
                thread.join(timeout=2.0)  # Wait up to 2 seconds
                
            # Check return code
            return_code = self.bonsai_process.returncode
            if return_code != 0:
                logging.error("Bonsai exited with code: %s" % return_code)
                
                # Display all the captured error output
                if self.stderr_data:
                    error_msg = "\n".join(self.stderr_data)
                    logging.error("Complete Bonsai error output:\n%s" % error_msg)
                    
                # Log error with mouse and user IDs for tracking
                logging.error("MID, %s, UID, %s, Action, Errored, Return_code, %s" % (self.mouse_id, self.user_id, return_code))
            else:
                logging.info("Bonsai completed successfully")
                
                # Display any errors even if the return code was successful 
                # (some errors might not affect the return code)
                if self.stderr_data:
                    warning_msg = "\n".join(self.stderr_data)
                    logging.warning("Bonsai reported warnings or non-fatal errors:\n%s" % warning_msg)
                
                # Log completion with mouse and user IDs for tracking
                self.stop_time = datetime.datetime.now()
                duration_min = (self.stop_time - self.start_time).total_seconds() / 60.0
                logging.info("MID, %s, UID, %s, Action, Completed, Duration_min, %s" % (self.mouse_id, self.user_id, round(duration_min, 2)))
                
        except Exception as e:
            logging.error("Error monitoring Bonsai process: %s" % e)
            self.stop()
            
    def get_bonsai_errors(self):
        """Return any errors reported by Bonsai"""
        if not self.stderr_data:
            return "No errors reported by Bonsai."
        return "\n".join(self.stderr_data)
    
    def kill_process(self):
        """Kill the Bonsai process immediately"""
        if self.bonsai_process and self.bonsai_process.poll() is None:
            logging.warning("Killing Bonsai process due to excessive memory usage")
            try:
                # Try to kill Bonsai process
                self.bonsai_process.kill()
                
                # Also kill child processes
                if WINDOWS_MODULES_AVAILABLE:
                    try:
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.bonsai_process.pid)])
                    except Exception as e:
                        logging.warning("Could not kill child processes: %s" % e)
            except Exception as e:
                logging.error("Error killing Bonsai process: %s" % e)
    
    def stop(self):
        """Stop the Bonsai process if it's running"""
        if self.bonsai_process and self.bonsai_process.poll() is None:
            logging.info("Stopping Bonsai process...")
            
            try:
                # Try to terminate gracefully first
                self.bonsai_process.terminate()
                
                # Give it a moment to terminate
                start_time = time.time()
                while time.time() - start_time < 3:  # Wait up to 3 seconds
                    if self.bonsai_process.poll() is not None:
                        logging.info("Bonsai process terminated gracefully")
                        break
                    time.sleep(0.1)
                
                # If termination didn't work, kill the process
                if self.bonsai_process.poll() is None:
                    logging.warning("Bonsai process did not terminate gracefully, killing it")
                    self.bonsai_process.kill()
                    
                    # Wait for process to be killed
                    start_time = time.time()
                    while time.time() - start_time < 2:  # Wait up to 2 seconds
                        if self.bonsai_process.poll() is not None:
                            break
                        time.sleep(0.1)
                    
                    if self.bonsai_process.poll() is None:
                        logging.error("Failed to kill Bonsai process")
                    else:
                        logging.info("Bonsai process killed")
                
                # Try to kill any child processes that might have been spawned by Bonsai
                if WINDOWS_MODULES_AVAILABLE:
                    try:
                        subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.bonsai_process.pid)])
                    except Exception as e:
                        logging.warning("Could not kill child processes: %s" % e)
                    
            except Exception as e:
                logging.error("Error stopping Bonsai process: %s" % e)
    
    def cleanup(self):
        """Clean up resources when the script exits"""
        logging.info("Cleaning up resources...")
        self.stop()
    
    def save_output(self):
        """
        Save experiment data as a pickle file in CAMSTIM-compatible format.
        
        This method creates a dictionary structure that closely resembles
        the one produced by CAMSTIM's OutputFile and SweepStim._save_output
        methods, ensuring compatibility with downstream processes.
        """
        self.stop_time = datetime.datetime.now()
        dt_str = self.start_time.strftime('%y%m%d%H%M%S')
        
        # Create structure similar to CAMSTIM's output format
        output_data = {
            # Top level experiment data
            'platform_info': self.platform_info,
            'start_time': self.start_time,
            'stop_time': self.stop_time,
            'duration': (self.stop_time - self.start_time).total_seconds(),
            'session_uuid': self.session_uuid,
            
            # Standard CAMSTIM metadata fields
            'rig_id': os.environ.get('aibs_rig_id', self.platform_info.get('rig_id', 'undefined')),
            'comp_id': os.environ.get('aibs_comp_id', self.platform_info.get('computer_name', 'undefined')),
            'script': os.path.basename(self.params.get('bonsai_path', '')),
            'script_md5': self.script_checksum,
            'params_md5': self.params_checksum,
            
            # Store stdout and stderr data for debugging
            'bonsai_stdout': self.stdout_data,
            'bonsai_stderr': self.stderr_data,
            
            # Items field organizes components like behavior, stim, etc.
            'items': {
                'behavior': {
                    'config': self.config.get('Behavior', {}),
                    'mouse_id': self.mouse_id,
                    'user_id': self.user_id,
                    # Placeholder for behavior data coming from Bonsai
                    'bonsai_data': self.params.get('bonsai_output', {})
                },
                'stimulus': {
                    'config': {
                        'params': self.params,
                        'config': self.config
                    },
                    'name': self.params.get('workflow_name', os.path.basename(self.params.get('bonsai_path', ''))),
                    'workflow_path': self.params.get('bonsai_path', ''),
                    'return_code': self.bonsai_process.returncode if self.bonsai_process else None
                }
            },
            
            # Config sections - for downstream compatibility
            'config': self.config,
            'params': self.params
        }
        
        # Use the session output path that was set up earlier
        output_path = self.session_output_path
        
        # Save output data as pickle file
        try:
            # Process through wecanpicklethat to filter out unpickleable items
            pickled_data = self.wecanpicklethat(output_data)
            
            # Create output directory if needed
            output_dir = os.path.dirname(output_path)
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
                
            # Use same logic as CAMSTIM's OutputFile.save() method
            if os.path.isfile(output_path):
                filename = os.path.basename(output_path)
                dirname = os.path.dirname(output_path)
                output_path = os.path.join(dirname, dt_str + "-" + filename)
                logging.warning("File path already exists, saving to: %s" % output_path)
                
            with open(output_path, 'wb') as f:
                pickle.dump(pickled_data, f)
                
            logging.info("Experiment data saved to: %s" % output_path)
            self.output_path = output_path
            
            # After saving, check if we need to create a backup copy
            backupdir = self.config.get('SweepStim', {}).get('backupdir')
            mouseid = self.mouse_id if self.mouse_id else "test_mouse"
            
            if backupdir:
                try:
                    # Create backup directory if it doesn't exist
                    mouse_dir = os.path.join(backupdir, mouseid + "/output")
                    if not os.path.isdir(mouse_dir):
                        os.makedirs(mouse_dir)
                    
                    # Create backup file in the mouse's output directory
                    backup_path = os.path.join(mouse_dir, os.path.basename(output_path))
                    logging.info("Backing up pkl file at %s" % backup_path)
                    
                    # Copy the file
                    import shutil
                    shutil.copy2(output_path, backup_path)
                    logging.info("Backup complete!")
                except Exception as e:
                    logging.warning("Failed to create backup: %s" % e)
            
        except Exception as e:
            logging.error("Failed to save experiment data: %s" % e)
    
    def wecanpicklethat(self, datadict):
        """
        Input is a dictionary.
            Attempts to pickle every item. If it doesn't pickle it is discarded
            and its key is added to the output as "unpickleable"
            
        This is a direct reimplementation of CAMSTIM's wecanpicklethat function.
        """
        pickleable = {}
        unpickleable = []
        for k, v in datadict.iteritems():
            try:
                if k[0] != "_":  # we don't want private counters and such
                    test = v
                    _ = pickle.dumps(test)
                    pickleable[k] = v
            except:
                unpickleable.append(k)
        pickleable['unpickleable'] = unpickleable
        return pickleable
    
    def run(self, param_file=None):
        """
        Run the experiment with the given parameters
        
        Args:
            param_file (str, optional): Path to the JSON parameter file
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Load parameters
            self.load_parameters(param_file)
            
            # Step 1: Set up repository (clone or update if needed)
            logging.info("Step 1: Setting up repository...")
            if not self.setup_repository():
                logging.error("Repository setup failed")
                return False
            
            # Step 2: Set up Bonsai installation (install if needed)
            logging.info("Step 2: Setting up Bonsai installation...")
            if not self.setup_bonsai():
                logging.error("Bonsai setup failed")
                return False
            
            # Step 3: Update BONSAI_EXE_PATH to use the installed executable
            global BONSAI_EXE_PATH
            bonsai_exe_relative_path = self.params.get('bonsai_exe_path')
            if bonsai_exe_relative_path:
                bonsai_exe_path = self.get_absolute_path_from_repo(bonsai_exe_relative_path)
                if bonsai_exe_path and os.path.exists(bonsai_exe_path):
                    BONSAI_EXE_PATH = bonsai_exe_path
                    logging.info("Using Bonsai executable: %s" % BONSAI_EXE_PATH)
            
            # Step 4: Verify Bonsai packages match repository requirements
            logging.info("Step 3: Verifying Bonsai package installation...")
            if not self.verify_bonsai_packages():
                logging.error("Bonsai package verification failed")
                logging.error("Please run your setup.cmd script to install/update the required packages")
                return False
            
            # Step 5: Start Bonsai
            logging.info("Step 4: Starting Bonsai experiment...")
            self.start_bonsai()
            
            # Check for errors
            if self.bonsai_process.returncode != 0:
                print("\n===== BONSAI ERROR DETAILS =====")
                print(self.get_bonsai_errors() or "No specific error details available.")
                print("================================\n")
                
                # Save output even if there was an error
                self.save_output()
                return False
            
            # Save experiment data
            self.save_output()
            
            # Check if there were any warnings/errors even with successful return code
            if self.stderr_data:
                print("\n===== BONSAI WARNING DETAILS =====")
                print(self.get_bonsai_errors())
                print("==================================\n")
            
            return True
            
        except Exception as e:
            logging.exception("Experiment failed: %s" % e)
            return False
        finally:
            # Make sure Bonsai is stopped
            self.stop()
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C and other signals"""
        logging.info("Received signal to terminate")
        self.stop()
        sys.exit(0)

    def check_git_available(self):
        """Check if Git is available on the system"""
        try:
            subprocess.check_output(['git', '--version'], stderr=subprocess.STDOUT)
            return True
        except (subprocess.CalledProcessError, OSError):
            logging.error("Git is not available on this system. Please install Git to use repository management features.")
            return False
    
    def get_current_commit_hash(self, repo_path):
        """Get the current commit hash of a Git repository"""
        try:
            original_dir = os.getcwd()
            os.chdir(repo_path)
            commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], stderr=subprocess.STDOUT).strip()
            return commit_hash
        except (subprocess.CalledProcessError, OSError) as e:
            logging.warning("Failed to get current commit hash: %s" % e)
            return None
        finally:
            os.chdir(original_dir)
    
    def get_remote_commit_hash(self, repo_path, branch='main'):
        """Get the latest commit hash from the remote repository for a specific branch"""
        try:
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            # Fetch latest changes from remote
            subprocess.check_call(['git', 'fetch', 'origin'], stderr=subprocess.STDOUT)
            
            # Get the commit hash of the remote branch
            remote_commit = subprocess.check_output(['git', 'rev-parse', 'origin/%s' % branch], stderr=subprocess.STDOUT).strip()
            return remote_commit
        except (subprocess.CalledProcessError, OSError) as e:
            logging.warning("Failed to get remote commit hash for %s: %s" % (branch, e))
            return None
        finally:
            os.chdir(original_dir)
    
    def is_on_latest_commit(self, repo_path, target_commit):
        """Check if the repository is on the latest commit for the specified target"""
        if target_commit == 'main':
            # For main branch, check against remote origin/main
            current_hash = self.get_current_commit_hash(repo_path)
            remote_hash = self.get_remote_commit_hash(repo_path, 'main')
            
            if current_hash and remote_hash:
                if current_hash == remote_hash:
                    logging.info("Repository is on the latest commit of main branch")
                    return True
                else:
                    logging.info("Repository is not on the latest commit")
                    logging.info("Current: %s, Latest remote: %s" % (current_hash[:8], remote_hash[:8]))
                    return False
            else:
                logging.warning("Could not compare commit hashes")
                return False
        else:
            # For specific commit hash, check if current commit matches
            current_hash = self.get_current_commit_hash(repo_path)
            if current_hash and current_hash.startswith(target_commit):
                logging.info("Repository is at the specified commit: %s" % target_commit)
                return True
            else:
                logging.info("Repository is not at the specified commit")
                logging.info("Current: %s, Required: %s" % (current_hash[:8] if current_hash else "unknown", target_commit))
                return False
    
    def clone_repository(self, repo_url, local_path):
        """Clone a Git repository to the specified local path"""
        try:
            logging.info("Cloning repository %s to %s" % (repo_url, local_path))
            
            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(local_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            # Clone the repository
            subprocess.check_call(['git', 'clone', repo_url, local_path], 
                                stderr=subprocess.STDOUT)
            logging.info("Repository cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Failed to clone repository: %s" % e)
            return False
        except OSError as e:
            logging.error("Git command failed: %s" % e)
            return False
    
    def checkout_commit(self, repo_path, commit_hash):
        """Checkout a specific commit in the repository"""
        try:
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            logging.info("Checking out commit %s" % commit_hash)
            
            # Fetch latest changes first
            subprocess.check_call(['git', 'fetch'], stderr=subprocess.STDOUT)
            
            # Checkout the specific commit
            subprocess.check_call(['git', 'checkout', commit_hash], stderr=subprocess.STDOUT)
            
            logging.info("Successfully checked out commit %s" % commit_hash)
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error("Failed to checkout commit %s: %s" % (commit_hash, e))
            return False
        except OSError as e:
            logging.error("Git command failed: %s" % e)
            return False
        finally:
            os.chdir(original_dir)
    
    def setup_repository(self):
        """Set up the repository based on parameters in the JSON file"""
        repo_url = self.params.get('repository_url')
        commit_hash = self.params.get('repository_commit_hash', 'main')
        local_repo_path = self.params.get('local_repository_path')
        
        if not repo_url or not local_repo_path:
            logging.info("No repository configuration found, skipping repository setup")
            return True
        
        # Check if Git is available
        if not self.check_git_available():
            return False
        
        logging.info("Setting up repository: %s" % repo_url)
        logging.info("Target commit: %s" % commit_hash)
        logging.info("Local path: %s" % local_repo_path)
        
        repo_full_path = os.path.join(local_repo_path, "openscope-community-predictive-processing")
        
        # Check if repository already exists
        if os.path.exists(repo_full_path):
            if os.path.exists(os.path.join(repo_full_path, '.git')):
                logging.info("Repository already exists, checking commit hash")
                
                # Use the new commit checking logic
                if self.is_on_latest_commit(repo_full_path, commit_hash):
                    logging.info("Repository is already at the correct commit")
                    return True
                else:
                    logging.info("Repository needs to be updated")
                    
                    # Use Git operations to update instead of deleting
                    if self.update_repository(repo_full_path, commit_hash):
                        logging.info("Repository updated successfully")
                        return True
                    else:
                        logging.warning("Failed to update repository, will try fresh clone")
                        # Only try to remove if update failed
                        if not self.force_remove_directory(repo_full_path):
                            logging.error("Failed to remove existing repository for fresh clone")
                            return False
            else:
                logging.info("Directory exists but is not a Git repository, removing it")
                if not self.force_remove_directory(repo_full_path):
                    logging.error("Failed to remove existing directory")
                    return False
        
        # Clone the repository
        if not self.clone_repository(repo_url, repo_full_path):
            return False
        
        # Checkout specific commit if not 'main'
        if commit_hash != 'main':
            if not self.checkout_commit(repo_full_path, commit_hash):
                return False
        
        logging.info("Repository setup completed successfully")
        return True
    
    def update_repository(self, repo_path, commit_hash):
        """Update an existing repository to the specified commit using Git operations"""
        try:
            original_dir = os.getcwd()
            os.chdir(repo_path)
            
            logging.info("Updating existing repository to commit %s" % commit_hash)
            
            # Reset any local changes
            subprocess.check_call(['git', 'reset', '--hard'], stderr=subprocess.STDOUT)
            
            # Fetch latest changes
            subprocess.check_call(['git', 'fetch', 'origin'], stderr=subprocess.STDOUT)
            
            # Checkout the target commit/branch
            if commit_hash == 'main':
                subprocess.check_call(['git', 'checkout', 'main'], stderr=subprocess.STDOUT)
                subprocess.check_call(['git', 'pull', 'origin', 'main'], stderr=subprocess.STDOUT)
            else:
                subprocess.check_call(['git', 'checkout', commit_hash], stderr=subprocess.STDOUT)
            
            logging.info("Repository updated successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error("Failed to update repository: %s" % e)
            return False
        except OSError as e:
            logging.error("Git command failed: %s" % e)
            return False
        finally:
            os.chdir(original_dir)
    
    def force_remove_directory(self, path):
        """Force remove a directory, handling Windows file locks"""
        import stat
        
        def handle_remove_readonly(func, path, exc):
            """Error handler for Windows readonly files"""
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                func(path)
        
        try:
            logging.info("Removing directory: %s" % path)
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return True
        except Exception as e:
            logging.error("Failed to remove directory %s: %s" % (path, e))
            return False
    
    def check_bonsai_installation(self):
        """Check if Bonsai is installed at the expected location"""
        bonsai_exe_relative_path = self.params.get('bonsai_exe_path')
        
        if not bonsai_exe_relative_path:
            logging.error("No Bonsai executable path specified in parameters")
            return False
        
        # Convert relative path to absolute path
        bonsai_exe_path = self.get_absolute_path_from_repo(bonsai_exe_relative_path)
        if not bonsai_exe_path:
            logging.error("Failed to construct absolute path for Bonsai executable")
            return False
        
        if os.path.exists(bonsai_exe_path):
            logging.info("Bonsai executable found at: %s" % bonsai_exe_path)
            return True
        else:
            logging.info("Bonsai executable not found at: %s" % bonsai_exe_path)
            return False
    
    def install_bonsai(self):
        """Install Bonsai using the setup script from the repository"""
        setup_script_relative_path = self.params.get('bonsai_setup_script')
        
        if not setup_script_relative_path:
            logging.error("No Bonsai setup script path specified in parameters")
            return False
        
        # Convert relative path to absolute path
        setup_script_path = self.get_absolute_path_from_repo(setup_script_relative_path)
        if not setup_script_path:
            logging.error("Failed to construct absolute path for Bonsai setup script")
            return False
        
        if not os.path.exists(setup_script_path):
            logging.error("Bonsai setup script not found at: %s" % setup_script_path)
            return False
        
        logging.info("Installing Bonsai using setup script: %s" % setup_script_path)
        
        try:
            # Change to the directory containing the setup script
            script_dir = os.path.dirname(setup_script_path)
            original_dir = os.getcwd()
            os.chdir(script_dir)
            
            # Execute the setup script
            process = subprocess.Popen(
                [setup_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True
            )
            
            # Monitor the installation process
            logging.info("Bonsai installation started...")
            stdout_lines = []
            stderr_lines = []
            
            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    stdout_lines.append(output.strip())
                    logging.info("Setup: %s" % output.strip())
            
            # Get any remaining stderr
            stderr_output = process.stderr.read()
            if stderr_output:
                stderr_lines.extend(stderr_output.split('\n'))
                for line in stderr_lines:
                    if line.strip():
                        logging.warning("Setup stderr: %s" % line.strip())
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                logging.info("Bonsai installation completed successfully")
                
                # Verify installation
                if self.check_bonsai_installation():
                    logging.info("Bonsai installation verified")
                    return True
                else:
                    logging.error("Bonsai installation verification failed")
                    return False
            else:
                logging.error("Bonsai installation failed with return code: %s" % return_code)
                return False
                
        except Exception as e:
            logging.error("Failed to execute Bonsai setup script: %s" % e)
            return False
        finally:
            os.chdir(original_dir)
    
    def setup_bonsai(self):
        """Set up Bonsai installation if needed"""
        # Check if Bonsai is already installed
        if self.check_bonsai_installation():
            logging.info("Bonsai is already installed")
            return True
        
        # Install Bonsai
        if not self.install_bonsai():
            logging.error("Failed to install Bonsai")
            return False
        
        return True

    def get_repository_path(self):
        """Get the full path to the cloned repository"""
        local_repo_path = self.params.get('local_repository_path')
        if not local_repo_path:
            return None
        return os.path.join(local_repo_path, "openscope-community-predictive-processing")
    
    def get_absolute_path_from_repo(self, relative_path):
        """Convert a relative path within the repository to an absolute path"""
        repo_path = self.get_repository_path()
        if not repo_path or not relative_path:
            return None
        return os.path.join(repo_path, relative_path)

    def parse_bonsai_config(self, config_path):
        """Parse a Bonsai.config XML file to extract package requirements"""
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(config_path)
            root = tree.getroot()
            
            required_packages = {}
            packages_element = root.find('Packages')
            
            if packages_element is not None:
                for package in packages_element.findall('Package'):
                    package_id = package.get('id')
                    package_version = package.get('version')
                    if package_id and package_version:
                        required_packages[package_id] = package_version
            
            logging.info("Found %d required packages in Bonsai.config" % len(required_packages))
            return required_packages
            
        except Exception as e:
            logging.error("Failed to parse Bonsai.config file %s: %s" % (config_path, e))
            return {}
    
    def get_installed_bonsai_packages(self, bonsai_install_path):
        """Get list of currently installed Bonsai packages and their versions"""
        packages_dir = os.path.join(bonsai_install_path, "Packages")
        installed_packages = {}
        
        if not os.path.exists(packages_dir):
            logging.warning("Bonsai packages directory not found: %s" % packages_dir)
            return installed_packages
        
        try:
            # Look for package directories in the format: PackageName.Version
            for item in os.listdir(packages_dir):
                package_path = os.path.join(packages_dir, item)
                if os.path.isdir(package_path):
                    # Parse package name and version from directory name
                    # Format is typically: PackageName.Version
                    parts = item.split('.')
                    if len(parts) >= 2:
                        # Find where version starts (first part that looks like a version)
                        version_start_idx = -1
                        for i, part in enumerate(parts):
                            if part.isdigit() or (len(part) > 0 and part[0].isdigit()):
                                version_start_idx = i
                                break
                        
                        if version_start_idx > 0:
                            package_name = '.'.join(parts[:version_start_idx])
                            package_version = '.'.join(parts[version_start_idx:])
                            installed_packages[package_name] = package_version
                            
            logging.info("Found %d installed Bonsai packages" % len(installed_packages))
            return installed_packages
            
        except Exception as e:
            logging.error("Failed to scan installed Bonsai packages: %s" % e)
            return {}
    
    def normalize_version(self, version):
        """Normalize version strings for comparison (e.g., '2.0.7.0' -> '2.0.7')"""
        if not version:
            return version
        
        # Split version into parts
        parts = version.split('.')
        
        # Remove trailing zeros
        while len(parts) > 1 and parts[-1] == '0':
            parts.pop()
        
        return '.'.join(parts)
    
    def versions_match(self, required_version, installed_version):
        """Check if two version strings are compatible"""
        if not required_version or not installed_version:
            return False
        
        # Normalize both versions (remove trailing .0)
        norm_required = self.normalize_version(required_version)
        norm_installed = self.normalize_version(installed_version)
        
        return norm_required == norm_installed
    
    def verify_bonsai_packages(self, auto_reinstall=True):
        """Verify that installed Bonsai packages match the requirements in the repository"""
        # Get the Bonsai config file from the repository
        bonsai_config_path = self.get_absolute_path_from_repo("code/stimulus-control/bonsai/Bonsai.config")
        if not bonsai_config_path or not os.path.exists(bonsai_config_path):
            logging.warning("Bonsai.config file not found in repository, skipping package verification")
            return True
        
        # Parse required packages from config
        required_packages = self.parse_bonsai_config(bonsai_config_path)
        if not required_packages:
            logging.warning("No required packages found in Bonsai.config, skipping verification")
            return True
        
        # Get Bonsai installation path
        bonsai_exe_path = self.get_absolute_path_from_repo(self.params.get('bonsai_exe_path', ''))
        if not bonsai_exe_path:
            logging.error("Cannot determine Bonsai installation path")
            return False
        
        bonsai_install_dir = os.path.dirname(bonsai_exe_path)
        
        # Get currently installed packages
        installed_packages = self.get_installed_bonsai_packages(bonsai_install_dir)
        
        # Compare required vs installed packages
        missing_packages = []
        version_mismatches = []
        
        for package_name, required_version in required_packages.items():
            if package_name not in installed_packages:
                missing_packages.append((package_name, required_version))
            elif not self.versions_match(required_version, installed_packages[package_name]):
                version_mismatches.append((
                    package_name, 
                    required_version, 
                    installed_packages[package_name]
                ))
        
        # Report results
        if not missing_packages and not version_mismatches:
            logging.info("All Bonsai packages are correctly installed and up to date")
            return True
        else:
            logging.warning("Bonsai package verification failed:")
            
            if missing_packages:
                logging.warning("Missing packages (%d):" % len(missing_packages))
                for package_name, required_version in missing_packages[:10]:  # Show first 10
                    logging.warning("  - %s (version %s)" % (package_name, required_version))
                if len(missing_packages) > 10:
                    logging.warning("  ... and %d more" % (len(missing_packages) - 10))
            
            if version_mismatches:
                logging.warning("Version mismatches (%d):" % len(version_mismatches))
                for package_name, required, installed in version_mismatches[:10]:  # Show first 10
                    logging.warning("  - %s: required %s, installed %s" % (package_name, required, installed))
                if len(version_mismatches) > 10:
                    logging.warning("  ... and %d more" % (len(version_mismatches) - 10))
            
            # Auto-reinstall if enabled
            if auto_reinstall:
                logging.info("Auto-reinstall enabled, attempting to fix package mismatches...")
                if self.reinstall_bonsai_packages():
                    logging.info("Bonsai packages reinstalled successfully, re-verifying...")
                    return self.verify_bonsai_packages(auto_reinstall=False)  # Prevent infinite loop
                else:
                    logging.error("Failed to reinstall Bonsai packages")
                    return False
            else:
                logging.warning("Run your setup.cmd script to install/update the required packages")
                return False
    
    def reinstall_bonsai_packages(self):
        """Reinstall Bonsai packages using the setup.cmd script from the repository"""
        try:
            # Find the setup script in the repository
            setup_script_relative_path = self.params.get('bonsai_setup_script')
            if not setup_script_relative_path:
                # Try common setup script names if not specified
                possible_scripts = [
                    'code/stimulus-control/bonsai/setup.cmd',
                    'code/stimulus-control/setup.cmd',
                    'setup.cmd'
                ]
                
                for script_path in possible_scripts:
                    full_path = self.get_absolute_path_from_repo(script_path)
                    if full_path and os.path.exists(full_path):
                        setup_script_relative_path = script_path
                        logging.info("Found setup script at: %s" % script_path)
                        break
                
                if not setup_script_relative_path:
                    logging.error("No setup script found. Please specify 'bonsai_setup_script' in parameters or ensure setup.cmd exists in the repository")
                    return False
            
            # Convert relative path to absolute path
            setup_script_path = self.get_absolute_path_from_repo(setup_script_relative_path)
            if not setup_script_path or not os.path.exists(setup_script_path):
                logging.error("Setup script not found at: %s" % setup_script_path)
                return False
            
            logging.info("Reinstalling Bonsai packages using setup script: %s" % setup_script_path)
            
            # Get Bonsai installation path for cleanup
            bonsai_exe_path = self.get_absolute_path_from_repo(self.params.get('bonsai_exe_path', ''))
            if bonsai_exe_path:
                bonsai_install_dir = os.path.dirname(bonsai_exe_path)
                packages_dir = os.path.join(bonsai_install_dir, "Packages")
                
                # Clean up existing packages directory to force fresh install
                if os.path.exists(packages_dir):
                    logging.info("Removing existing packages directory for fresh install: %s" % packages_dir)
                    try:
                        self.force_remove_directory(packages_dir)
                        logging.info("Successfully removed existing packages directory")
                    except Exception as e:
                        logging.warning("Could not remove packages directory: %s. Setup script will attempt to update." % e)
            
            # Change to the directory containing the setup script
            script_dir = os.path.dirname(setup_script_path)
            original_dir = os.getcwd()
            os.chdir(script_dir)
            
            try:
                # Execute the setup script
                logging.info("Running setup script to reinstall packages...")
                
                # Use shell=True on Windows for .cmd files
                process = subprocess.Popen(
                    [setup_script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    shell=True
                )
                
                # Monitor the installation process
                stdout_lines = []
                stderr_lines = []
                
                # Read output in real-time
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        line = output.strip()
                        stdout_lines.append(line)
                        logging.info("Setup: %s" % line)
                
                # Get any remaining stderr
                stderr_output = process.stderr.read()
                if stderr_output:
                    stderr_lines.extend(stderr_output.strip().split('\n'))
                    for line in stderr_lines:
                        if line.strip():
                            logging.warning("Setup stderr: %s" % line.strip())
            
                # Wait for process to complete
                return_code = process.wait()
                
                if return_code == 0:
                    logging.info("Setup script completed successfully")
                    return True
                else:
                    logging.error("Setup script failed with return code: %s" % return_code)
                    if stderr_lines:
                        logging.error("Setup script errors: %s" % '\n'.join(stderr_lines))
                    return False
                    
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logging.error("Failed to run setup script: %s" % e)
            return False