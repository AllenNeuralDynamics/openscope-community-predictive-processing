#!/usr/bin/env python
"""Minimal packaging test for BonsaiExperiment using existing CSV directory.

Does NOT generate CSVs; expects a folder containing:
    orientations_orientations*.csv
    orientations_logger*.csv

Run (Python 2.7 env):
    python test_packaging.py "C:\\Users\\jeromel\\Downloads\\769904_20251015T235544"

Outputs dry_run.pkl inside the provided session directory.
"""
import os, sys, datetime, types

def main():
        if len(sys.argv) < 2:
                print("Usage: python test_packaging.py <session_folder_with_csvs>")
                return
        session_dir = sys.argv[1]
        if not os.path.isdir(session_dir):
                print("Directory not found: %s" % session_dir)
                return

        # Inject mock mpeconfig before importing launcher to avoid production dependency
        mock = types.ModuleType('mpeconfig')
        def source_configuration(name, send_start_log=False):
                return {
                        'root_datapath': 'C:/ProgramData/AIBS_MPE/camstim/',
                        'Behavior': {}, 'Encoder': {'radius_cm': 6.0}, 'Reward': {}, 'Licksensing': {},
                        'Sync': {}, 'Stim': {}, 'LIMS': {}, 'SweepStim': {'backupdir': None}, 'Display': {},
                        'Datastream': {}, 'DigitalEncoder': {'radius_cm': 6.0}, 'shared': {}
                }
        mock.source_configuration = source_configuration
        sys.modules['mpeconfig'] = mock
        sys.path.append(os.path.dirname(__file__))
        from bonsai_experiment_launcher import BonsaiExperiment

        exp = BonsaiExperiment()
        exp.session_folder = session_dir
        exp.session_output_path = os.path.join(session_dir, 'dry_run.pkl')
        exp.params['output_path'] = exp.session_output_path
        exp.mouse_id = 'test_mouse'
        exp.user_id = 'tester'
        # Avoid path lookups by leaving bonsai_path blank
        exp.params['bonsai_path'] = ''
        exp.start_time = datetime.datetime.now()
        exp.save_output()
        print('Pickle created at: %s' % exp.session_output_path)
        print('File size bytes: %s' % (os.path.isfile(exp.session_output_path) and os.path.getsize(exp.session_output_path) or 'NOT_CREATED'))

if __name__ == '__main__':
        main()
