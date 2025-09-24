"""Litestar routes serving the demo frontend."""

from __future__ import annotations

from litestar import Router, get
from litestar.di import Provide
from litestar.response import Template

from .settings import FrontendSettings


def build_router(*, settings: FrontendSettings) -> Router:
    dependencies = {"settings": Provide(lambda: settings, sync_to_thread=False)}

    @get("/")
    async def index(settings: FrontendSettings) -> Template:
        return Template(
            template_name="index.html",
            context={
                "backend_url": settings.backend_url,
                "default_chunk_size": settings.default_chunk_size,
                "pg_database": settings.pg_database,
                "embedding_model": settings.embedding_model,
            },
        )

    @get("/healthz")
    async def health(settings: FrontendSettings) -> dict[str, str]:
        return {"status": "ok", "backend_url": settings.backend_url}

    return Router(path="", route_handlers=[index, health], dependencies=dependencies)
