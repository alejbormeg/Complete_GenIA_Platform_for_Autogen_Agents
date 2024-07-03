from export_experiments import export_all_experiments
from import_experiments import import_from_dir

# Specify the output directory for exporting the experiments
path = "/tmp/export"

export_all_experiments(path)
import_from_dir(path)