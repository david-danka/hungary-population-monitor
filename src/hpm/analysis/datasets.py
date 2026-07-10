"""Helpers for loading and summarizing the core analysis datasets."""

import json
import pandas as pd
from hpm.db import query
from hpm.settings import settings

COUNTY_GEOJSON_PATH = settings.base_dir / "data" / "geo" / "hungary_counties.geojson"


def population_settlements():
    """Load the joined population-settlement dataset.

    Returns:
        A DataFrame containing the raw population and settlement rows used by
        the analysis layer.
    """
    return query("SELECT * FROM population_settlements")


def county_population():
    """Aggregate total population by county.

    Returns:
        A DataFrame with one row per county and its summed population.
    """
    return query("""
        SELECT county_name, SUM(population) AS population
        FROM population_settlements
        GROUP BY county_name
    """)


def county_boundaries() -> dict:
    """Return the cached GeoJSON county boundaries for Hungary.

    Returns:
        A GeoJSON FeatureCollection containing county geometries keyed by the
        county name in each feature's properties.
    """
    return json.loads(COUNTY_GEOJSON_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    print(county_boundaries())