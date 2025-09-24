#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

ACTION="${1:-up}"

if docker compose version >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DOCKER_COMPOSE=(docker-compose)
else
  echo "Docker Compose is required but not installed." >&2
  exit 1
fi

case "$ACTION" in
  up)
    "${DOCKER_COMPOSE[@]}" -f "$COMPOSE_FILE" up -d --build
    echo "Containers started."
    echo "Backend:  http://localhost:8001"
    echo "Frontend: http://localhost:3000"
    ;;
  down)
    "${DOCKER_COMPOSE[@]}" -f "$COMPOSE_FILE" down
    ;;
  logs)
    "${DOCKER_COMPOSE[@]}" -f "$COMPOSE_FILE" logs -f
    ;;
  *)
    echo "Usage: $0 [up|down|logs]" >&2
    exit 1
    ;;
 esac
