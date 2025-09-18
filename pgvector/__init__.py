"""Local fallback implementation for pgvector integration used in tests."""

from .psycopg2 import register_vector

__all__ = ["register_vector"]
