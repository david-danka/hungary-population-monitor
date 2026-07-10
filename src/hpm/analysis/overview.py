"""National-level population trend and settlement-ranking analysis.

Computes national population time series and growth metrics, per-year
settlement snapshots, rank-size/largest-settlement views, concentration
share, and population-change extremes -- feeding the Overview page.
Pure pandas/numpy; no UI or database dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PopulationChangeExtremes:
    """Top and bottom settlements by absolute population change.

    Attributes:
        top: Settlements with the largest absolute gains, sorted
            descending by `absolute_change`.
        bottom: Settlements with the largest absolute losses, sorted
            descending by `absolute_change` (i.e. least negative first).
    """
    top: pd.DataFrame
    bottom: pd.DataFrame


def year_bounds(df: pd.DataFrame) -> tuple[int, int]:
    """Finds the earliest and latest year present in the dataset.

    Args:
        df: Wide settlement-population table with a `year` column.

    Returns:
        Tuple of `(first_year, last_year)`.
    """

    return int(df["year"].min()), int(df["year"].max())


def national_population_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Computes the national population time series.

    Args:
        df: Wide settlement-population table with `year` and `population`
            columns.

    Returns:
        One row per year, with columns `year` and `population` (summed
        across all settlements).
    """
    return df.groupby("year", as_index=False)["population"].sum()


def national_population_at(df: pd.DataFrame, year: int) -> int:
    """Computes total national population in a given year.

    Args:
        df: Wide settlement-population table with `year` and `population`
            columns.
        year: Year to compute the total for.

    Returns:
        National population for `year`, summed across all settlements.
    """
    ts = national_population_by_year(df)
    return int(ts.loc[ts["year"] == year, "population"].iloc[0])


def percent_change(first: int, latest: int) -> float:
    """Computes percentage change between two values.

    Args:
        first: Baseline value.
        latest: Latest value.

    Returns:
        Percentage change from `first` to `latest` (e.g. `-5.2` for a
        5.2% decline).
    """
    return (latest / first - 1) * 100


def compound_annual_growth_rate(
    first: int, latest: int, n_years: int
) -> float:
    """Computes the compound annual growth rate (CAGR) between two values.

    Args:
        first: Baseline value.
        latest: Latest value.
        n_years: Number of years between the baseline and latest values.

    Returns:
        CAGR as a decimal fraction (e.g. `-0.012` for a -1.2% average
        yearly rate).
    """
    return (latest / first) ** (1 / n_years) - 1


def settlement_count(df: pd.DataFrame) -> int:
    """Counts the number of distinct settlements in the dataset.

    Args:
        df: Wide settlement-population table with a `settlement_name`
            column.

    Returns:
        Number of unique settlement names across all years.
    """
    return int(df["settlement_name"].nunique())


def settlements_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Builds a per-settlement snapshot for a given year.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            `settlement_type`, `latitude`, `longitude`, and `population`
            columns.
        year: Year to filter by.

    Returns:
        One row per settlement present in `year`, with columns
        `settlement_name`, `settlement_type`, `latitude`, `longitude`,
        and `population`.
    """
    return df[df["year"] == year][
        ["settlement_name", "settlement_type", "latitude", "longitude", "population"]
    ]

def settlement_type_mix_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Computes population distribution by settlement type for a given year.

    Args:
        df: Wide settlement-population table with `year`, `settlement_type`,
            and `population` columns.
        year: Year to filter by.

    Returns:
        One row per settlement type, with columns `settlement_type` and
        `population` (summed across all settlements of that type).
    """
    return (
        df[df["year"] == year]
        .groupby("settlement_type", as_index=False)["population"]
        .sum()
    )


def settlement_rank_size_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Computes the rank-size distribution of settlements for a given year.

    Args:
        df: Wide settlement-population table with `year` and `population`
            columns.
        year: Year to filter by.

    Returns:
        All settlements present in `year`, sorted descending by
        `population`, with an added `rank` column (1 = largest).
    """
    df = df[df["year"] == year]
    df = df.sort_values("population", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    return df


def largest_settlements_by_year(
    df: pd.DataFrame, year: int, n: int
) -> pd.DataFrame:
    """Finds the N largest settlements by population in a given year.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            and `population` columns.
        year: Year to filter by.
        n: Number of largest settlements to return.

    Returns:
        Top `n` settlements by population, with columns `settlement_name`
        and `population`, sorted descending.
    """

    filtered = df[df["year"] == year]
    sorted_df = filtered.sort_values(by="population", ascending=False)

    return sorted_df.head(n)[["settlement_name", "population"]]


def population_change_extremes(
    df: pd.DataFrame,
    first_year: int,
    last_year: int,
    top_bottom_n: int,
) -> pd.DataFrame:
    """Finds the top N winners and bottom N losers by absolute population change.

    Note:
        Direction is currently computed via a row-wise `.apply`, which is
        slower than a vectorized `numpy.where` for large frames; consider
        aligning this with the vectorized approach used in
        `analysis/change.py`'s `settlement_change`.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            and `population` columns.
        first_year: Baseline year to measure the change against.
        last_year: End year to subtract the baseline year's values from.
        top_bottom_n: Number of largest gainers and losers to return.

    Returns:
        `PopulationChangeExtremes` with `top` and `bottom` DataFrames,
        each containing `settlement_name`, `absolute_change`, and
        `direction` (`"Growth"` or `"Decline"`).
    """

    cols = ["settlement_name", "population"]
    first = df[df["year"] == first_year][cols]
    last = df[df["year"] == last_year][cols]

    merged = first.merge(last, on="settlement_name", suffixes=("_f", "_l"))
    merged["absolute_change"] = merged["population_l"] - merged["population_f"]
    merged["direction"] = merged["absolute_change"].apply(
        lambda x: "Growth" if x >= 0 else "Decline"
    )
    merged = merged.sort_values("absolute_change", ascending=False)

    result_cols = ["settlement_name", "absolute_change", "direction"]
    return PopulationChangeExtremes(
        top=merged.head(top_bottom_n)[result_cols],
        bottom=merged.tail(top_bottom_n)[result_cols],
    )


def concentration_share_by_year(df: pd.DataFrame, year: int, n: int) -> float:
    """Computes the share of national population held by the N largest settlements.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            and `population` columns.
        year: Year to compute the share for.
        n: Number of largest settlements to include.

    Returns:
        Percentage (0-100) of that year's national population held by
        the `n` largest settlements.
    """
    year_df = df[df["year"] == year]
    top_n_total = year_df.nlargest(n, "population")["population"].sum()
    national_total = year_df["population"].sum()
    return top_n_total / national_total * 100


def closest_settlement_by_population(df: pd.DataFrame, year: int, target: float) -> pd.Series:
    """Finds the settlement whose population is closest to a target value.

    Used to translate an abstract population figure (e.g. a year's net
    change) into a comparably-sized, named settlement.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            and `population` columns.
        year: Year to search within.
        target: Population value to find the closest match to.

    Returns:
        Series with `settlement_name` and `population` for the closest
        match found in `year`.
    """
    year_df = df[df["year"] == year]
    idx = (year_df["population"] - target).abs().idxmin()
    return year_df.loc[idx, ["settlement_name", "population"]]
