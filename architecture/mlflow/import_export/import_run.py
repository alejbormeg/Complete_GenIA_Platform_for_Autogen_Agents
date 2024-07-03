import mlflow.tensorflow
import mlflow
import sys


# EXECUTE THIS SCRIPT WITH THE CORRECT CONDA ENV FOR THE MODEL
# Check if correct number of arguments are provided
if len(sys.argv) != 4:
    print("Please provide arguments in the order: MLflow URL, "
          "target experiment ID "
          "and path to the artifacts")
    sys.exit(1)

mlflow_url = sys.argv[1]
target_experiment_id = sys.argv[2]  # Target experiment ID
local_export_dir = sys.argv[3]  # Directory where the run was exported

# Set MLflow tracking URI
mlflow.set_tracking_uri(mlflow_url)

# Load the TensorFlow model from the exported artifacts
model_path = f"file://{local_export_dir}"
loaded_model = mlflow.tensorflow.load_model(model_path)

# Log the TensorFlow model to the target experiment
with mlflow.start_run(experiment_id=target_experiment_id) as run:
    mlflow.tensorflow.log_model(
        loaded_model=loaded_model,
        artifact_path="model"
    )
