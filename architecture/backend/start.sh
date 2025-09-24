#!/bin/bash
set -euo pipefail

if [ -f /app/src/.env ]; then
    set -a
    # shellcheck disable=SC1091
    . /app/src/.env
    set +a
fi

exec uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-8001}"
