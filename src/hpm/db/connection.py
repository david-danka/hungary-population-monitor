import sqlite3

from hpm.settings import settings

DB_PATH = settings.database / "hpm.db"


def connect() -> sqlite3.Connection:
    """
    Create a connection to the SQLite database.

    Returns a new connection to the project's SQLite file.
    The connection is configured for use in multi-threaded
    environments (e.g., Streamlit).

    Returns:
        sqlite3.Connection: Active database connection.
    """
    return sqlite3.connect(DB_PATH, check_same_thread=False)