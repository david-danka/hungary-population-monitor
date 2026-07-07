"""
Database access layer for the Hungary Population Monitor.

Exposes a single SQL query interface used by the analysis layer.
Handles connection management and returns results as pandas DataFrames.
"""
from hpm.db.connection import connect
from hpm.db.sqlite import query


__all__ = [
    "connect",
    "query",
]