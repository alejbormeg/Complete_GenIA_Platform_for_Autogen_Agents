from __future__ import annotations

from pathlib import Path

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

from .routes import build_router
from .settings import FrontendSettings

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"


def create_app() -> Litestar:
    settings = FrontendSettings()

    return Litestar(
        route_handlers=[build_router(settings=settings)],
        template_config=TemplateConfig(
            directory=TEMPLATES_DIR,
            engine=JinjaTemplateEngine,
        ),
    )


app = create_app()

__all__ = ["create_app", "app"]
