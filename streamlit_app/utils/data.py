import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "hpm.db"
NO_ADDRESS_SETTLEMENT_CODE = 0  # "LAKCÍM NÉLKÜLI" -- real population, no place


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data
def load_dim_county() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM dim_county", conn)


@st.cache_data
def load_dim_settlement() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM dim_settlement", conn)


@st.cache_data
def load_fact_population() -> pd.DataFrame:
    with _connect() as conn:
        return pd.read_sql_query("SELECT * FROM fact_population", conn)


@st.cache_data
def load_joined() -> pd.DataFrame:
    """fact_population enriched with settlement name/coords and county
    name -- the table most pages actually want, built once and cached."""
    fact = load_fact_population()
    settlement = load_dim_settlement()[["settlement_code", "settlement_name", "latitude", "longitude"]]
    county = load_dim_county()

    df = fact.merge(settlement, on="settlement_code", how="left")
    df = df.merge(county, on="county_code", how="left")

    with _connect() as conn:
        df = pd.read_sql("SELECT * FROM population_settlements", conn)
    
    return df


@st.cache_data
def year_bounds() -> tuple[int, int]:
    fact = load_fact_population()
    return int(fact["year"].min()), int(fact["year"].max())