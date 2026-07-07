from pathlib import Path
from hpm.db import connect


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def create_views() -> None:
    """
    Create or refresh semantic views in the database.

    This defines the canonical analytical datasets used by the
    analysis layer. Safe to run multiple times.
    """
    sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with connect() as conn:
        conn.executescript(sql)
        conn.commit()