"""Load subpackage public API.

This module exposes the loading utilities used to persist the star
schema into durable storage (SQLite by default).
"""

from hpm.load.sqlite_loader import load_star_schema

__all__ = [
    "load_star_schema",
]