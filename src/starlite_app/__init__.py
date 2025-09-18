"""Starlite application exposing the LangChain NL2SQL workflow."""

from __future__ import annotations

from starlite import Starlite

from langchain_app import LangChainAppSettings, NL2SQLWorkflow

from .routes import build_router


def create_app(
    *,
    settings: LangChainAppSettings | None = None,
    workflow: NL2SQLWorkflow | None = None,
) -> Starlite:
    """Instantiate the Starlite application."""

    resolved_settings = settings or LangChainAppSettings.from_env()
    resolved_workflow = workflow or NL2SQLWorkflow(resolved_settings)
    router = build_router(settings=resolved_settings, workflow=resolved_workflow)
    return Starlite(route_handlers=[router])


__all__ = ["create_app"]
