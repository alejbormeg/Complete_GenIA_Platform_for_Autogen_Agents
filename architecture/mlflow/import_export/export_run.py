import mlflow
import sys

# Check if correct number of arguments are provided
if len(sys.argv) != 4:
    print("Please provide arguments in the order: MLflow URL," 
          "local path,"
          "model URI")
    sys.exit(1)

mlflow_url = sys.argv[1]
local_export_dir = sys.argv[2]  # Directory to save downloaded artifacts
model_uri = sys.argv[3]  # Model URI

# Set MLflow tracking URI
mlflow.set_tracking_uri(mlflow_url)

# Download the run's artifacts to a local directory
mlflow.artifacts.download_artifacts(model_uri, dst_path=local_export_dir)
