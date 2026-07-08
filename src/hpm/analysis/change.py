# analysis/change.py — new module
from __future__ import annotations
import numpy as np
import pandas as pd


def settlement_change(
    df: pd.DataFrame,
    first_year: int,
    last_year: int,
    min_baseline_pop: int = 0,
) -> pd.DataFrame:
    """
    Per-settlement population change between two years, with both absolute
    and percentage framings. No ranking/truncation — callers slice as needed.
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
    """
    % of the *total national population lost* (summed over all declining
    settlements) that the N biggest individual losers account for.
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
    """
    Count the number of decliner and grower settlements

    Args:
        df (pd.DataFrame): output of `population_settlements` function
        base_year (int): year to measure the change against
        end_year (int): year to measure the change to

    Returns:
        dict[str, int]: count grower and decliner settlements
    """
    counts = change_df["direction"].value_counts()
    return {
        "Growth": int(counts.get("Growth", 0)),
        "Decline": int(counts.get("Decline", 0)),
    }


def total_change_by_direction(change_df: pd.DataFrame) -> pd.DataFrame:
    """Total population gained, total lost, and the net — for a waterfall chart."""
    total_growth = change_df.loc[change_df["abs_change"] > 0, "abs_change"].sum()
    total_decline = change_df.loc[change_df["abs_change"] < 0, "abs_change"].sum()
    return pd.DataFrame({
        "label": ["Total growth", "Total decline", "Net change"],
        "value": [total_growth, total_decline, total_growth + total_decline],
        "measure": ["relative", "relative", "total"],
    })


def relative_change_category(change_df: pd.DataFrame, national_pct_change: float) -> pd.DataFrame:
    """Classifies each settlement against the national pct change, not zero:
    Growing / Declining slower than national / Declining faster than national."""
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
    """Per-year totals of settlement-level YoY growth and decline, plus net."""
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