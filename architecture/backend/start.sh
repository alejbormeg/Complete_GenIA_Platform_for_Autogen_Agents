#!/bin/bash
set -euo pipefail

if [ -f /app/src/.env ]; then
    # Load default values from .env without overriding variables injected by the runtime
    eval "$(python - <<'PY'
import os
import shlex
from dotenv import dotenv_values

for key, value in dotenv_values('/app/src/.env').items():
    if not key:
        continue
    if value is None:
        continue
    if key in os.environ:
        continue
    print(f"export {key}={shlex.quote(value)}")
PY
    )"
fi

exec uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-8001}"
