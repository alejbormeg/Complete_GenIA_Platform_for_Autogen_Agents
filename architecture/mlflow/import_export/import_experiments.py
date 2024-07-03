import os
import subprocess

export_dir = '/tmp/export'

def import_from_dir(path):
    # Get a list of subfolders in the export directory
    subfolders = [f.path for f in os.scandir(export_dir) if f.is_dir()]
    url="http://10.34.1.50"
    # Iterate through the subfolders and import each experiment
    for subfolder in subfolders:
        experiment_name = subfolder.split('/')[-1]  # Extract experiment name from the subfolder path
        import_command = f"export MLFLOW_TRACKING_URI={url}; import-experiment --experiment-name {experiment_name} --input-dir {subfolder}"
        subprocess.run(import_command, shell=True, check=True)
        print(f"imported '{subfolder}' to Mlflow server {url}")

import_from_dir(export_dir)
