"""Application settings for the Hungary population monitoring pipeline.

This module defines the immutable configuration values used across data
collection and preprocessing workflows. It exposes a single `settings`
instance configured from the repository layout.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """
    Immutable configuration object for the data pipeline.

    Attributes:
        base_dir: Absolute path to the project root directory.
        raw_population: Directory containing raw population Excel files.
        raw_settlements: Directory containing raw GeoNames settlement files.
        database: Directory where the SQLite database file will be written.
    """

    base_dir: Path = Path(__file__).resolve().parent.parent.parent

    raw_population: Path = base_dir / "data/raw/population"

    raw_settlements: Path = base_dir / "data/raw/settlements"

    database: Path = base_dir / "data/database"


settings = Settings()
