"""Allow running the FastAPI app via ``python -m api``."""

import uvicorn

from .app import app


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8001)


if __name__ == "__main__":  # pragma: no cover
    main()
