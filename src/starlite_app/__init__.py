from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import httpx
from litestar import Litestar, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.logging import LoggingConfig
from litestar.template.config import TemplateConfig

from .routes import build_router
from .settings import FrontendSettings

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

logging_config = LoggingConfig(
    root={"level": "INFO", "handlers": ["queue_listener"]},
    formatters={"standard": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    log_exceptions="always",
)

@get("/ping-backend")
async def ping_backend() -> Dict[str, str]:
    settings = FrontendSettings()
    url = f"{settings.backend_url.rstrip('/')}/healthz"
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get(url)
        r.raise_for_status()
        body = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else r.text
        )
    return {"backend_status": "ok", "from": url, "body": body}

def create_app() -> Litestar:
    settings = FrontendSettings()
    frontend_router = build_router(settings=settings)
    return Litestar(
        route_handlers=[frontend_router, ping_backend],
        template_config=TemplateConfig(directory=TEMPLATES_DIR, engine=JinjaTemplateEngine),
        debug=True,
        logging_config=logging_config,
    )

app = create_app()
__all__ = ["app", "create_app"]
