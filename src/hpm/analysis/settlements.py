"""Helpers for deriving settlement-level summaries and selection metadata."""

from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class SettlementSummary:
    """Summary statistics for one settlement across the observed time span."""

    settlement_name: str
    county_name: str
    settlement_type: str
    latest_population: int
    first_population: int
    abs_change: int
    pct_change: float
    population_rank: int
    n_settlements: int


def settlement_options(df: pd.DataFrame) -> pd.DataFrame:
    """Build a settlement selection table with disambiguated labels.

    Args:
        df: A DataFrame containing settlement-level population data.

    Returns:
        A DataFrame with one row per settlement and a display label.
    """
    options = df[["settlement_name", "county_name"]].drop_duplicates()
    options["label"] = (
        options["settlement_name"]
        + " ("
        + options["county_name"].fillna("Budapest")
        + ")"
    )
    return options.sort_values("label")


def settlement_series(df: pd.DataFrame, settlement_name: str) -> pd.DataFrame:
    """Return the full yearly population series for one settlement.

    Args:
        df: A DataFrame containing settlement population rows.
        settlement_name: The settlement whose history should be extracted.

    Returns:
        A DataFrame sorted by year for the requested settlement.
    """
    return df[df["settlement_name"] == settlement_name].sort_values("year")


def gender_ratio_series(df: pd.DataFrame, settlement_name: str) -> pd.DataFrame:
    """Return male-to-female ratios for a settlement across time.

    Args:
        df: A DataFrame containing settlement population rows.
        settlement_name: The settlement whose ratio series should be built.

    Returns:
        A DataFrame with the original series plus a `ratio` column.
    """
    series = settlement_series(df, settlement_name)
    return series.assign(ratio=series["male_population"] / series["female_population"])


def settlement_summary(
    df: pd.DataFrame, settlement_name: str, first_year: int, last_year: int
) -> SettlementSummary:
    """Build an at-a-glance summary for one settlement.

    Args:
        df: A DataFrame containing settlement population rows.
        settlement_name: The settlement to summarize.
        first_year: The earliest year to compare against.
        last_year: The latest year to summarize.

    Returns:
        A structured summary object with population change and rank details.
    """
    series = settlement_series(df, settlement_name)
    latest_row = series[series["year"] == last_year].iloc[0]
    first_row = series[series["year"] == first_year].iloc[0]

    latest_pop = int(latest_row["population"])
    first_pop = int(first_row["population"])

    last_year_df = df[df["year"] == last_year].sort_values(
        "population", ascending=False
    )
    rank = int((last_year_df["settlement_name"] == settlement_name).idxmax())
    rank = (
        int(
            last_year_df.reset_index(drop=True).index[
                last_year_df.reset_index(drop=True)["settlement_name"]
                == settlement_name
            ][0]
        )
        + 1
    )

    return SettlementSummary(
        settlement_name=settlement_name,
        county_name=latest_row["county_name"]
        if pd.notna(latest_row["county_name"])
        else "Budapest",
        settlement_type=latest_row["settlement_type"],
        latest_population=latest_pop,
        first_population=first_pop,
        abs_change=latest_pop - first_pop,
        pct_change=(latest_pop / first_pop - 1) * 100,
        population_rank=rank,
        n_settlements=len(last_year_df),
    )
