import json
import pandas as pd
from hpm.db import query
from hpm.settings import settings

COUNTY_GEOJSON_PATH = settings.base_dir / "data" / "geo" / "hungary_counties.geojson"


def population_settlements():
    return query("SELECT * FROM population_settlements")


def county_population():
    return query("""
        SELECT county_name, SUM(population) AS population
        FROM population_settlements
        GROUP BY county_name
    """)

def county_boundaries() -> dict:
    """
    Static GeoJSON FeatureCollection for Hungary's counties, keyed by
    `county_name` in each feature's properties. Generated once via
    scripts/fetch_county_boundaries.py — no live network calls at runtime.
    """
    return json.loads(COUNTY_GEOJSON_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    print(county_boundaries())