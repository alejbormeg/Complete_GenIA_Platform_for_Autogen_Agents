"""Starlite application serving the demo UI."""

from __future__ import annotations

from pathlib import Path

from starlite import Starlite
from starlite.config import TemplateConfig
from starlite.template import JinjaTemplateEngine

from .routes import build_router
from .settings import FrontendSettings


def create_app(*, settings: FrontendSettings | None = None) -> Starlite:
    resolved_settings = settings or FrontendSettings()
    template_config = TemplateConfig(
        directory=Path(__file__).parent / "templates",
        engine=JinjaTemplateEngine,
    )
    router = build_router(settings=resolved_settings)
    return Starlite(route_handlers=[router], template_config=template_config)


__all__ = ["create_app", "FrontendSettings"]
