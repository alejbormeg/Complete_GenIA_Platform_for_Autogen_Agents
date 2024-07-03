import os
import subprocess
from mlflow.tracking import MlflowClient
import mlflow

def export_all_experiments(output_dir):
    mlflow.set_tracking_uri("http://localhost")
    client = MlflowClient("http://localhost")

    # Get a list of all experiments
    experiments = client.search_experiments()

    for experiment in experiments:
        experiment_name = experiment.name
        experiment_id = experiment.experiment_id

        # Create a directory for each experiment
        experiment_dir = os.path.join(output_dir, experiment_name)
        os.makedirs(experiment_dir, exist_ok=True)

        # Execute the export command for the experiment
        export_command = f"export MLFLOW_TRACKING_URI=http://localhost; export-experiment --experiment {experiment_id} --output-dir {experiment_dir}"
        subprocess.run(export_command, shell=True, check=True)

        print(f"Exported experiment '{experiment_name}' to '{experiment_dir}'")

# Specify the output directory for exporting the experiments
output_directory = "/tmp/export"

# Call the function to export all experiments
export_all_experiments(output_directory)
