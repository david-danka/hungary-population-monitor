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
        gov_url: Source URL for Hungarian population datasets.
        raw_excels: Directory where raw Excel files are stored.
        processed_excels: Directory for processed dataset outputs.
    """

    base_dir: Path = Path(__file__).resolve().parent.parent

    gov_url: str = "https://kormany.hu/nyilvantartasok/statisztika/lakossagi-szamadatok"

    raw_excels: Path = base_dir / "data" / "raw" / "excels"

    processed_excels: Path = base_dir / "data" / "processed" / "excels"


settings = Settings()
