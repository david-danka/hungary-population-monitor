"""Build the normalized star schema SQLite database from cleaned population data.

Takes the wide, denormalized DataFrame produced by
hpm.transform.population.transform_population_datasets() and splits it
into dim_county, dim_settlement, and fact_population tables, then
persists them to a SQLite database along with a convenience view that
joins them back together for easy querying.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from hpm.settings import settings

SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS dim_county (
    county_code INTEGER PRIMARY KEY,
    county_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_settlement (
    settlement_code INTEGER PRIMARY KEY,
    settlement_name TEXT NOT NULL,
    county_code INTEGER NOT NULL,
    latitude REAL,
    longitude REAL
);

CREATE TABLE IF NOT EXISTS fact_population (
    settlement_code INTEGER NOT NULL,
    year INTEGER NOT NULL,
    county_code INTEGER,
    settlement_type TEXT NOT NULL,
    male_population INTEGER NOT NULL,
    female_population INTEGER NOT NULL,
    population INTEGER NOT NULL,
    PRIMARY KEY (settlement_code, year),
    FOREIGN KEY (settlement_code) REFERENCES dim_settlement(settlement_code),
    FOREIGN KEY (county_code) REFERENCES dim_county(county_code)
);
"""


def load_star_schema(
    dim_county: pd.DataFrame,
    dim_settlement: pd.DataFrame,
    fact_population: pd.DataFrame,
) -> Path:
    """Persist star schema DataFrames into a SQLite database.

    Args:
        dim_county: County dimension table.
        dim_settlement: Settlement dimension table.
        fact_population: Population fact table.

    Returns:
        The path to the created SQLite database file.
    """
    settings.database.mkdir(parents=True, exist_ok=True)
    db_path = settings.database / "hpm.db"

    db_path.unlink(missing_ok=True)  # drop stale db so schema changes take effect

    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_DDL)

        dim_county.to_sql("dim_county", conn, if_exists="append", index=False)
        dim_settlement.to_sql("dim_settlement", conn, if_exists="append", index=False)
        fact_population.to_sql("fact_population", conn, if_exists="append", index=False)

    return db_path
