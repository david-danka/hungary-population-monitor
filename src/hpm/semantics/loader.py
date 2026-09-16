import zlib
from pathlib import Path
from hpm.db import connect


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _schema_checksum(sql: str) -> int:
    """Return a signed 32-bit checksum of the schema SQL text.

    PRAGMA user_version stores a signed 32-bit integer, so the
    unsigned CRC32 is folded into that range.
    """
    unsigned = zlib.crc32(sql.encode("utf-8"))
    return unsigned - 2**32 if unsigned >= 2**31 else unsigned


def create_views() -> None:
    """
    Create or refresh semantic views in the database.

    This defines the canonical analytical datasets used by the
    analysis layer. Safe to run multiple times.

    Skips the DROP+CREATE script when schema.sql is unchanged since the
    last run: SQLite rewrites schema pages on every DROP+CREATE VIEW
    regardless of whether the definition actually changed, which turns
    a no-op call into a spurious diff on the database file. The
    schema's checksum is tracked via PRAGMA user_version, a 32-bit
    integer SQLite reserves in the file header for exactly this kind
    of app-defined versioning, so no extra table is needed.
    """
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    checksum = _schema_checksum(sql)

    with connect() as conn:
        current_version = conn.execute("PRAGMA user_version").fetchone()[0]
        if current_version == checksum:
            return

        conn.executescript(sql)
        conn.execute(f"PRAGMA user_version = {checksum}")
        conn.commit()
