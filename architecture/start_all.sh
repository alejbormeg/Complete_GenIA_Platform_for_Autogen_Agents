#!/bin/bash

# Define the network name
NETWORK_NAME="common_network"

# Check if the network already exists, if not, create it
if ! docker network ls --format '{{.Name}}' | grep -w $NETWORK_NAME > /dev/null; then
    echo "Creating Docker network: $NETWORK_NAME"
    docker network create $NETWORK_NAME
else
    echo "Docker network '$NETWORK_NAME' already exists."
fi

declare -A directories=( 
    ["frontend"]="start_front_app.sh" 
    ["mlflow"]="start_mlflow.sh" 
    ["ray_cluster"]="start_ray_cluster.sh"
)

for dir in "${!directories[@]}"; do
    SCRIPT_PATH="./$dir/${directories[$dir]}"
    if [ -f "$SCRIPT_PATH" ]; then
        echo "Executing $SCRIPT_PATH"
        (cd $dir && bash ${directories[$dir]})
    else
        echo "Start script not found in $dir"
    fi
done
