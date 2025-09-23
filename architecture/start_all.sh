#!/bin/bash

set -euo pipefail

NETWORK_NAME="common_network"

if ! docker network ls --format '{{.Name}}' | grep -w "$NETWORK_NAME" >/dev/null 2>&1; then
    echo "Creating Docker network: $NETWORK_NAME"
    docker network create "$NETWORK_NAME"
else
    echo "Docker network '$NETWORK_NAME' already exists."
fi

echo "Starting Ray cluster"
(
    cd ray_cluster
    ./start_ray_cluster.sh
)

echo "Ray cluster bootstrapped."
echo
cat <<INSTRUCTIONS
Next steps:
  1. Launch the FastAPI backend:    ./architecture/start_backend.sh
  2. Launch the Starlite frontend:  ./architecture/start_frontend.sh
  3. Open the frontend in your browser (default http://localhost:3000)
INSTRUCTIONS
