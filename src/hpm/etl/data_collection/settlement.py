"""
GeoNames Hungary settlement data collector.

Downloads and extracts the official GeoNames HU dataset containing
settlement-level geographic coordinates and metadata.

This module is responsible for retrieving the raw reference dataset
used for mapping Hungarian settlements to latitude/longitude coordinates.
"""

from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests

from hpm.settings import settings

GEONAMES_HU_URL = "https://download.geonames.org/export/dump/HU.zip"


def download_geonames_hungary() -> Path:
    """
    Download and extract the GeoNames Hungary dataset.

    Downloads the HU.zip archive from GeoNames and extracts the HU.txt
    file containing settlement-level geographic data (including coordinates).

    If the file already exists locally, the download is skipped.

    Returns:
        Path to the extracted HU.txt file in the raw storage directory.
    """
    settings.raw_settlements.mkdir(
        parents=True,
        exist_ok=True,
    )

    target = settings.raw_settlements / "HU.txt"

    if target.exists():
        print("Skipping HU.txt")
        return target

    response = requests.get(
        GEONAMES_HU_URL,
        timeout=60,
    )
    response.raise_for_status()

    with ZipFile(BytesIO(response.content)) as zf:
        zf.extract(
            member="HU.txt",
            path=settings.raw_settlements,
        )

    print("Downloaded and extracted HU.txt")

    return target


def collect_settlement_data() -> None:
    """
    Entry point for settlement coordinate collection pipeline.

    Ensures the GeoNames Hungary dataset is downloaded and extracted
    into the configured raw data directory.
    """
    download_geonames_hungary()


if __name__ == "__main__":
    collect_settlement_data()
