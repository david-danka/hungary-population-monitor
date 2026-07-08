"""
One-time script: build data/geo/hungary_counties.geojson from OSM relations.

Run manually, not part of the app's runtime pipeline or ETL:
    python scripts/fetch_county_boundaries.py

Source: OSM relation IDs listed on the Hungary/Boundaries wiki page;
individual boundary GeoJSON served by polygons.openstreetmap.fr.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

WIKI_URL = "https://wiki.openstreetmap.org/wiki/Hungary/Boundaries"
GEOJSON_URL_TEMPLATE = (
    "http://polygons.openstreetmap.fr/get_geojson.py?id={id}&params=0"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "geo"
    / "hungary_counties.geojson"
)

# OSM display name -> your dim_county.county_name spelling.
COUNTY_NAME_OVERRIDES: dict[str, str] = {
    "Pest megye": "PES",
    "Budapest": "BUD",
    "Bács-Kiskun megye": "BAC",
    "Baranya megye": "BAR",
    "Békés megye": "BEK",
    "Borsod-Abaúj-Zemplén megye": "BOR",
    "Csongrád megye": "CSO",
    "Fejér megye": "FEJ",
    "Győr-Moson-Sopron megye": "GYO",
    "Hajdú-Bihar megye": "HAJ",
    "Heves megye": "HEV",
    "Jász-Nagykun-Szolnok megye": "SZO",
    "Komárom-Esztergom megye": "KOM",
    "Nógrád megye": "NOG",
    "Somogy megye": "SOM",
    "Szabolcs-Szatmár-Bereg megye": "SZA",
    "Tolna megye": "TOL",
    "Vas megye": "VAS",
    "Veszprém megye": "VES",
    "Zala megye": "ZAL",
}


def parse_relation_table(table: Tag) -> list[tuple[str, str]]:
    """Extract (name, OSM relation ID) pairs from a boundary table."""
    rows: list[tuple[str, str]] = []

    for tr in table.find_all("tr")[1:]:  # skip header
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue

        name = cells[0].get_text(strip=True)

        relation_id = None
        for a in cells[1].find_all("a"):
            text = a.get_text(strip=True)
            if re.fullmatch(r"\d+", text):
                relation_id = text
                break

        if relation_id is not None:
            rows.append((name, relation_id))

    return rows


def fetch_county_table() -> list[tuple[str, str]]:
    """Returns (county_name, osm_relation_id) pairs from the 'Megyék' table."""
    resp = requests.get(WIKI_URL, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    header = next(
        (
            h2
            for h2 in soup.find_all("h2")
            if "Megyék" in h2.get_text(strip=True)
        ),
        None,
    )

    if header is None:
        raise RuntimeError("Couldn't locate the 'Megyék' section.")

    table = header.find_next_sibling("table")
    if not isinstance(table, Tag):
        raise RuntimeError("Couldn't locate the county table.")

    rows = parse_relation_table(table)

    if not rows:
        raise RuntimeError("County table was found but no relation IDs were parsed.")

    return rows


def fix_geometry_collection(geometry: dict) -> dict:
    if (
        geometry.get("type") == "GeometryCollection"
        and len(geometry["geometries"]) == 1
    ):
        return geometry["geometries"][0]
    return geometry


def fetch_feature(county_name: str, relation_id: str) -> dict:
    resp = requests.get(
        GEOJSON_URL_TEMPLATE.format(id=relation_id),
        timeout=30,
    )
    resp.raise_for_status()

    clean_name = COUNTY_NAME_OVERRIDES.get(county_name, county_name)

    return {
        "type": "Feature",
        "properties": {
            "county_name": clean_name,
            "osm_relation_id": relation_id,
        },
        "geometry": fix_geometry_collection(resp.json()),
    }


def main() -> None:
    features = []

    for name, relation_id in fetch_county_table():
        print(f"Fetching {name} ({relation_id})...")
        features.append(fetch_feature(name, relation_id))
        time.sleep(1)  # be polite to a free service

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": features,
            }
        ),
        encoding="utf-8",
    )

    print(f"Wrote {len(features)} counties to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()