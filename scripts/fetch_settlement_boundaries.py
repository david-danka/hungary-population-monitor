"""One-time script: build data/geo/hungary_settlements.geojson from OSM
relation IDs listed in data/geo/settlement_osm_ids.csv.

Run manually, not part of the ETL pipeline or app runtime:
    python fetch_settlement_boundaries.py

Fetches each settlement's boundary GeoJSON individually from
polygons.openstreetmap.fr (a free, unauthenticated, rate-limited third-
party service), caches each raw response to disk so a crash/interrupt
doesn't lose earlier progress, then assembles everything into one
FeatureCollection. Failures (missing relation, invalid/empty geometry,
network error) are logged to a manifest CSV instead of silently dropped
-- with ~3,150 settlements, expect some real gaps, especially for tiny
villages that may not have a mapped boundary relation in OSM at all.

Resumable: re-running skips settlements whose cache file already exists.
Delete individual files in CACHE_DIR to force a re-fetch of just those.
"""

import csv
import json
import time
from pathlib import Path

import requests

INPUT_CSV = Path(__file__).resolve().parent.parent / "data" / "geo" / "settlement_osm_ids.csv"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "geo" / "hungary_settlements.geojson"
FAILURE_MANIFEST = Path(__file__).resolve().parent.parent / "data" / "geo" / "settlement_fetch_failures.csv"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "geo" / "_settlement_cache"

GEOJSON_URL_TEMPLATE = "http://polygons.openstreetmap.fr/get_geojson.py?id={id}&params=0"
REQUEST_DELAY_SECONDS = 0.2  # be polite to a free, shared service
REQUEST_TIMEOUT_SECONDS = 30


def fix_geometry_collection(geometry: dict) -> dict:
    """Unwraps a single-element GeometryCollection, which the service
    returns for some relations but which most GeoJSON consumers (and
    strict validators) don't expect for a single boundary."""
    if geometry.get("type") == "GeometryCollection" and len(geometry.get("geometries", [])) == 1:
        return geometry["geometries"][0]
    return geometry


def is_valid_geometry(geometry: dict) -> bool:
    """Minimal sanity check: has a real type and non-empty coordinates."""
    if not geometry or "type" not in geometry:
        return False
    coords = geometry.get("coordinates") or geometry.get("geometries")
    return bool(coords)


def load_settlement_ids() -> list[tuple[str, str]]:
    with INPUT_CSV.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [(row["settlement_name"], row["osm_relation_id"]) for row in reader]


def fetch_and_cache(settlement_name: str, osm_id: str) -> dict | None:
    """Returns the raw parsed geometry dict, using the on-disk cache if
    present. Returns None on any fetch/parse failure."""
    cache_file = CACHE_DIR / f"{osm_id}.json"

    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass  # corrupted cache entry, refetch below

    try:
        resp = requests.get(
            GEOJSON_URL_TEMPLATE.format(id=osm_id), timeout=REQUEST_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
        geometry = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"  FAILED  {settlement_name} ({osm_id}): {e}")
        return None

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(geometry), encoding="utf-8")
    time.sleep(REQUEST_DELAY_SECONDS)
    return geometry


def main():
    settlements = load_settlement_ids()
    print(f"Loaded {len(settlements)} settlement -> OSM ID pairs from {INPUT_CSV}")

    features = []
    failures = []

    for i, (settlement_name, osm_id) in enumerate(settlements, start=1):
        if i % 100 == 0:
            print(f"  ...{i}/{len(settlements)} processed")

        geometry = fetch_and_cache(settlement_name, osm_id)

        if geometry is None:
            failures.append((settlement_name, osm_id, "fetch_or_parse_error"))
            continue

        geometry = fix_geometry_collection(geometry)

        if not is_valid_geometry(geometry):
            failures.append((settlement_name, osm_id, "empty_or_invalid_geometry"))
            continue

        features.append({
            "type": "Feature",
            "properties": {"settlement_name": settlement_name, "osm_relation_id": osm_id},
            "geometry": geometry,
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )

    if failures:
        with FAILURE_MANIFEST.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["settlement_name", "osm_relation_id", "reason"])
            writer.writerows(failures)

    print(f"\nWrote {len(features)} settlement boundaries to {OUTPUT_PATH}")
    print(f"{len(failures)} settlements failed -- see {FAILURE_MANIFEST if failures else '(none)'}")
    if features:
        success_rate = len(features) / len(settlements) * 100
        print(f"Success rate: {success_rate:.1f}%")


if __name__ == "__main__":
    main()