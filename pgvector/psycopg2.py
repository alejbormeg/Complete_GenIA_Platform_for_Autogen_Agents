"""Compatibility layer mimicking :mod:`pgvector.psycopg2` when the library is unavailable."""

from __future__ import annotations

from typing import Any


def register_vector(_: Any) -> None:  # pragma: no cover - simple shim
    """Stub implementation used during local testing.

    The production stack installs the real :mod:`pgvector` package. In CI we provide
    this no-op to allow the integration tests to import the module without raising a
    :class:`ModuleNotFoundError`.
    """

    return None
