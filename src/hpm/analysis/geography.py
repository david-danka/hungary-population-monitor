"""County- and settlement-level geographic distribution analysis.

Computes county population aggregates and trajectories, population-change
choropleth data, concentration/urbanization measures (top-N share, Gini
coefficient, Lorenz curve), and county-seat dominance ratios -- feeding
the Geography page.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

def county_population_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Computes total population per county for a given year.

    Args:
        df: Wide settlement-population table with `year`, `county_name`,
            and `population` columns.
        year: Year to filter by.

    Returns:
        One row per county, with columns `county_name` and `population`
        (summed across all settlements in that county), sorted ascending
        by `population`.
    """
    return (
        df[df["year"] == year]
        .groupby("county_name", as_index=False)["population"]
        .sum()
        .sort_values("population")
    )

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

def county_population_change(df: pd.DataFrame, first_year: int, last_year: int) -> pd.DataFrame:
    """Computes per-county population change between two years.

    Args:
        df: Wide settlement-population table with `year`, `county_name`,
            and `population` columns.
        first_year: Baseline year to measure the change against.
        last_year: End year to subtract the baseline year's values from.

    Returns:
        One row per county present in both years, with columns
        `county_name`, `population_first`, `population_last`,
        `pct_change`, and `abs_change`. Intended as the color source for
        a choropleth map.
    """
    first = df[df["year"] == first_year].groupby("county_name", as_index=False)["population"].sum()
    last = df[df["year"] == last_year].groupby("county_name", as_index=False)["population"].sum()
    merged = first.merge(last, on="county_name", suffixes=("_first", "_last"))
    merged["pct_change"] = (merged["population_last"] / merged["population_first"] - 1) * 100
    merged["abs_change"] = merged["population_last"] - merged["population_first"]
    return merged

def concentration_share_trend(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Computes the share of national population held by the N largest settlements, per year.

    Args:
        df: Wide settlement-population table with `year`, `settlement_name`,
            and `population` columns.
        n: Number of largest settlements to include, each year.

    Returns:
        One row per year, with columns `year` and `share` (percentage,
        0-100, of that year's national population held by the `n`
        largest settlements that year).
    """
    records = []
    for year, year_df in df.groupby("year"):
        top_n_total = year_df.nlargest(n, "population")["population"].sum()
        national_total = year_df["population"].sum()
        records.append({"year": year, "share": top_n_total / national_total * 100})
    return pd.DataFrame(records)

def largest_settlement_share_by_county(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Computes each county's largest settlement's share of that county's population.

    Measures county-seat dominance -- how much of a county's total
    population is concentrated in its single biggest settlement.

    Args:
        df: Wide settlement-population table with `year`, `county_name`,
            `settlement_name`, and `population` columns.
        year: Year to compute shares for.

    Returns:
        One row per county, with columns `county_name`, `settlement_name`
        (that county's largest settlement), `largest_settlement_pop`,
        `county_total`, and `share` (percentage, 0-100), sorted
        descending by `share`.
    """
    year_df = df[df["year"] == year]
    county_totals = year_df.groupby("county_name")["population"].sum()
    idx = year_df.groupby("county_name")["population"].idxmax()
    largest = year_df.loc[idx, ["county_name", "settlement_name", "population"]]
    largest = largest.rename(columns={"population": "largest_settlement_pop"})
    largest = largest.merge(county_totals.rename("county_total"), on="county_name")
    largest["share"] = largest["largest_settlement_pop"] / largest["county_total"] * 100
    return largest.sort_values("share", ascending=False)

def county_population_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Computes each county's population trajectory across all years.

    Args:
        df: Wide settlement-population table with `year`, `county_name`,
            and `population` columns.

    Returns:
        One row per (county, year) pair, with columns `county_name`,
        `year`, and `population` (summed across all settlements in that
        county for that year).
    """
    return df.groupby(["county_name", "year"], as_index=False)["population"].sum()


def index_to_first_year(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Indexes population to 100 at each group's first year.

    Enables trajectory comparison across groups with very different
    absolute population scales (e.g. Budapest vs. a small county), by
    plotting relative growth/decline instead of raw values.

    Args:
        df: Long-format table with `year`, `population`, and a grouping
            column (e.g. `county_name`).
        group_col: Name of the column to group by (each group's first
            year, by `year`, is used as its own base of 100).

    Returns:
        Copy of `df` with an added `indexed` column: `population` scaled
        so each group's first recorded year equals 100.
    """
    df = df.copy()
    first_vals = df.sort_values("year").groupby(group_col)["population"].transform("first")
    df["indexed"] = df["population"] / first_vals * 100
    return df


def gini_coefficient(values: np.ndarray) -> float:
    """Computes the Gini coefficient of inequality for an array of values.

    Args:
        values: Non-negative numeric array (e.g. settlement populations).

    Returns:
        Gini coefficient in [0, 1]: 0 means every unit holds an equal
        share of the total; 1 means a single unit holds the entire total.
    """
    values = np.sort(values)
    n = len(values)
    cumulative = np.cumsum(values)
    return (n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n


def lorenz_curve(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Computes Lorenz curve coordinates for settlement population inequality.

    Args:
        df: Wide settlement-population table with `year` and `population`
            columns.
        year: Year to compute the curve for.

    Returns:
        DataFrame with columns `cum_settlements_pct` and
        `cum_population_pct`, both in [0, 1] and starting at `(0, 0)`,
        tracing the cumulative population share held by the cumulative
        share of settlements when sorted ascending by population. The
        further this curve bows below the `y = x` line of perfect
        equality, the more unequal the distribution.
    """
    year_df = df[df["year"] == year].sort_values("population").reset_index(drop=True)
    total_pop = year_df["population"].sum()

    cum_population_pct = year_df["population"].cumsum() / total_pop
    cum_settlements_pct = (year_df.index + 1) / len(year_df)

    return pd.DataFrame({
        "cum_settlements_pct": np.insert(cum_settlements_pct.values, 0, 0),
        "cum_population_pct": np.insert(cum_population_pct.values, 0, 0),
    })


def settlement_gini_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Computes settlement-level population inequality (Gini) for each year.

    Args:
        df: Wide settlement-population table with `year` and `population`
            columns.

    Returns:
        One row per year, with columns `year` and `gini` (see
        `gini_coefficient`), sorted ascending by `year`.
    """
    records = [
        {"year": year, "gini": gini_coefficient(year_df["population"].values)}
        for year, year_df in df.groupby("year")
    ]
    return pd.DataFrame(records).sort_values("year")