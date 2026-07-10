"""Per-settlement population change analysis for the Winners & Losers page.

Computes population change between two years at the individual settlement
level -- absolute and percentage framings, direction classification,
national-decline attribution, and year-by-year growth/decline totals.
Pure pandas/numpy; no UI or database dependencies.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def settlement_change(
    df: pd.DataFrame,
    first_year: int,
    last_year: int,
    min_baseline_pop: int = 0,
) -> pd.DataFrame:
    """Computes per-settlement population change between two years.

    Merges each settlement's population in `first_year` and `last_year`,
    then derives absolute change, percentage change, and a coarse growth/
    decline direction label. Performs no ranking or truncation -- callers
    slice the result (e.g. via `nlargest`/`nsmallest`) as needed.

    Args:
        df: Wide settlement-population table with at least the columns
            `settlement_name`, `settlement_type`, `county_name`,
            `latitude`, `longitude`, `population`, and `year`.
        first_year: Baseline year to measure change from.
        last_year: End year to measure change to.
        min_baseline_pop: Minimum population in `first_year` a settlement
            must have to be included. Excludes settlements where a tiny
            absolute swing produces a misleadingly large percentage change
            (e.g. a village growing from 4 to 12 people). Defaults to 0
            (no filtering).

    Returns:
        One row per settlement present in both years, with columns:
        `settlement_name`, `settlement_type`, `county_name`, `latitude`,
        `longitude`, `population_first`, `population_last`, `abs_change`,
        `pct_change`, and `direction` (`"Growth"` or `"Decline"`).
    """
    cols = [
        "settlement_name",
        "settlement_type",
        "county_name",
        "latitude",
        "longitude",
        "population",
    ]
    first = df[df["year"] == first_year][cols]
    last = df[df["year"] == last_year][["settlement_name", "population"]]

    merged = first.merge(
        last, on="settlement_name", suffixes=("_first", "_last")
    )
    merged = merged[merged["population_first"] >= min_baseline_pop]

    merged["abs_change"] = (
        merged["population_last"] - merged["population_first"]
    )
    merged["pct_change"] = (
        merged["population_last"] / merged["population_first"] - 1
    ) * 100
    merged["direction"] = np.where(
        merged["abs_change"] >= 0, "Growth", "Decline"
    )
    return merged


def national_decline_contribution(change_df: pd.DataFrame, n: int) -> float:
    """Computes the share of total population loss driven by the N biggest losers.

    Args:
        change_df: Output of `settlement_change`. Must contain `abs_change`.
        n: Number of the steepest-declining settlements to attribute.

    Returns:
        Percentage (0-100) of the total population lost across every
        declining settlement that is accounted for by the N settlements
        with the largest individual losses. Returns 0.0 if no settlement
        in `change_df` declined.
    """
    losses = change_df[change_df["abs_change"] < 0]
    total_loss = losses["abs_change"].sum()
    if total_loss == 0:
        return 0.0
    biggest_losers_loss = losses.nsmallest(n, "abs_change")["abs_change"].sum()
    return biggest_losers_loss / total_loss * 100


def count_by_direction(
    change_df: pd.DataFrame,
) -> dict[str, int]:
    """Counts settlements by growth/decline direction.

    Args:
        change_df: Output of `settlement_change`. Must contain `direction`.

    Returns:
        Dict with keys `"Growth"` and `"Decline"`, each mapped to the
        number of settlements with that direction. A direction absent
        from `change_df` maps to 0.
    """
    counts = change_df["direction"].value_counts()
    return {
        "Growth": int(counts.get("Growth", 0)),
        "Decline": int(counts.get("Decline", 0)),
    }


def total_change_by_direction(change_df: pd.DataFrame) -> pd.DataFrame:
    """Computes total population gained, lost, and the net, for a waterfall chart.

    Args:
        change_df: Output of `settlement_change`. Must contain `abs_change`.

    Returns:
        Three-row DataFrame with columns `label`, `value`, and `measure`
        (Plotly waterfall convention: `"relative"` for the growth/decline
        bars, `"total"` for the net-change bar), in the order Total
        growth, Total decline, Net change.
    """
    total_growth = change_df.loc[change_df["abs_change"] > 0, "abs_change"].sum()
    total_decline = change_df.loc[change_df["abs_change"] < 0, "abs_change"].sum()
    return pd.DataFrame({
        "label": ["Total growth", "Total decline", "Net change"],
        "value": [total_growth, total_decline, total_growth + total_decline],
        "measure": ["relative", "relative", "total"],
    })


def relative_change_category(change_df: pd.DataFrame, national_pct_change: float) -> pd.DataFrame:
    """Classifies each settlement's change relative to the national trend.

    Unlike a simple positive/negative split, this compares each
    settlement's percentage change against the national percentage
    change over the same period -- so a settlement losing population
    slower than the national average is distinguished from one losing
    population faster.

    Args:
        change_df: Output of `settlement_change`. Must contain `pct_change`.
        national_pct_change: The national population percentage change
            over the same period, as a point of comparison.

    Returns:
        Copy of `change_df` with an added `relative_category` column,
        one of: `"Growing"` (pct_change >= 0), `"Declining slower than
        national average"` (pct_change < 0 but >= national_pct_change),
        or `"Declining faster than national average"` (otherwise).
    """
    change_df = change_df.copy()
    conditions = [
        change_df["pct_change"] >= 0,
        change_df["pct_change"] >= national_pct_change,
    ]
    choices = ["Growing", "Declining slower than national average"]
    change_df["relative_category"] = np.select(
        conditions, choices, default="Declining faster than national average"
    )
    return change_df


def yearly_change_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Computes per-year totals of settlement-level year-over-year change.

    For each settlement, computes the year-over-year population delta,
    then sums separately across all growing and all declining settlements
    for each year -- showing how the composition of national change
    (not just its net value) evolves over time.

    Args:
        df: Wide settlement-population table with at least `settlement_name`,
            `year`, and `population`.

    Returns:
        One row per year (excluding each settlement's first recorded
        year, which has no prior value to diff against), with columns
        `year`, `total_growth` (sum of positive YoY deltas), `total_decline`
        (sum of negative YoY deltas), and `net` (their sum).
    """
    sorted_df = df.sort_values(["settlement_name", "year"]).copy()
    sorted_df["yoy_change"] = sorted_df.groupby("settlement_name")["population"].diff()
    sorted_df = sorted_df.dropna(subset=["yoy_change"])

    grouped = sorted_df.groupby("year")["yoy_change"]
    yearly = pd.DataFrame({
        "total_growth": grouped.apply(lambda s: s[s > 0].sum()),
        "total_decline": grouped.apply(lambda s: s[s < 0].sum()),
    }).reset_index()
    yearly["net"] = yearly["total_growth"] + yearly["total_decline"]
    return yearly