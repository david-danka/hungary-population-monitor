from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PopulationChangeExtremes:
    top: pd.DataFrame
    bottom: pd.DataFrame


def year_bounds(df: pd.DataFrame) -> tuple[int, int]:
    """
    Find earliest and latest year in population_settlements table.

    Args:
        df (pd.DataFrame): population_settlements wide table

    Returns:
        tuple[int, int]: first and last year found in population_settlements table.
    """

    return int(df["year"].min()), int(df["year"].max())


def national_population_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate national population time series.

    Args:
        df (pd.DataFrame): population_settlements wide table

    Returns:
        pd.DataFrame: national population time series
    """
    return df.groupby("year", as_index=False)["population"].sum()


def national_population_at(df: pd.DataFrame, year: int) -> int:
    """
    Total national population in a given year.

    Args:
        df (pd.DataFrame): population_settlements wide table

    Returns:
        int: national population
    """
    ts = national_population_by_year(df)
    return int(ts.loc[ts["year"] == year, "population"].iloc[0])


def percent_change(first: int, latest: int) -> float:
    return (latest / first - 1) * 100


def compound_annual_growth_rate(
    first: int, latest: int, n_years: int
) -> float:
    return (latest / first) ** (1 / n_years) - 1


def settlement_count(df: pd.DataFrame) -> int:
    return int(df["settlement_name"].nunique())


def settlements_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Per-settlement snapshot for a year: location, type, and population."""
    return df[df["year"] == year][
        ["settlement_name", "settlement_type", "latitude", "longitude", "population"]
    ]

def settlement_type_mix_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Population distribution by settlement type for the given year.

    Args:
        df (pd.DataFrame): population_settlements wide table
        year (int): year to filter by

    Returns:
        pd.DataFrame:
    """
    return (
        df[df["year"] == year]
        .groupby("settlement_type", as_index=False)["population"]
        .sum()
    )


def settlement_rank_size_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Rank-size distribution of settlements for selected year.

    Args:
        df (pd.DataFrame): population_settlements wide table
        year (int): year to filter by

    Returns:
        pd.DataFrame: ranked settlements with log-ready structure.
    """
    df = df[df["year"] == year]
    df = df.sort_values("population", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    return df


def largest_settlements_by_year(
    df: pd.DataFrame, year: int, n: int
) -> pd.DataFrame:
    """
    Largest N settlements based on population in the selected year.

    Args:
        df (pd.DataFrame): population_wide table
        year (int): year to filter by
        n (int): number of the largest settlements

    Returns:
        pd.DataFrame: `n` largest settlements with population
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
    """
    Top N winners and bottom N losers by absolute population change.

    Args:
        df (pd.DataFrame): population_settlements wide table
        first_year (int): base year to measure the change against
        last_year (int): end year to subtract base year values from
        top_bottom_n (int): number of largest gainers and losers to return

    Returns:
        RankedChanges: top and bottom settlements by absolute_change, each
        with a `direction` column ("Growth"/"Decline"). No presentation concerns.
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
    """% of national population held by the N largest settlements in a year."""
    year_df = df[df["year"] == year]
    top_n_total = year_df.nlargest(n, "population")["population"].sum()
    national_total = year_df["population"].sum()
    return top_n_total / national_total * 100


def closest_settlement_by_population(df: pd.DataFrame, year: int, target: float) -> pd.Series:
    """Settlement whose population in `year` is closest to `target`."""
    year_df = df[df["year"] == year]
    idx = (year_df["population"] - target).abs().idxmin()
    return year_df.loc[idx, ["settlement_name", "population"]]
