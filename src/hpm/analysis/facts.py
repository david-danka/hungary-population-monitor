# analysis/facts.py
from __future__ import annotations
from collections import defaultdict

import pandas as pd


def find_attribute_changes(df: pd.DataFrame, attr_col: str) -> pd.DataFrame:
    """Settlements where `attr_col` (e.g. county_name, settlement_type) changed
    between any two consecutive years they appear in."""
    sub = (
        df[["settlement_name", "year", attr_col]]
        .dropna()
        .sort_values(["settlement_name", "year"])
    )
    sub["prev_val"] = sub.groupby("settlement_name")[attr_col].shift(1)
    sub["prev_year"] = sub.groupby("settlement_name")["year"].shift(1)
    changes = sub[sub[attr_col] != sub["prev_val"]].dropna(subset=["prev_val"])
    return changes.rename(columns={attr_col: "new_val"})[
        ["settlement_name", "prev_year", "year", "prev_val", "new_val"]
    ]


def find_appearance_events(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Settlements that appear partway through the series (newly independent)
    or disappear partway through (merged/absorbed)."""
    first_seen = df.groupby("settlement_name")["year"].min()
    last_seen = df.groupby("settlement_name")["year"].max()
    first_year, last_year = df["year"].min(), df["year"].max()

    appeared = first_seen[first_seen > first_year]
    disappeared = last_seen[last_seen < last_year]
    return appeared, disappeared


def least_populated(df: pd.DataFrame, year: int | None = None) -> pd.Series:
    """Single least-populated settlement, either for one year or overall."""
    sub = df if year is None else df[df["year"] == year]
    row = sub.loc[sub["population"].idxmin()]
    return row[["settlement_name", "year", "population"]]


def most_male_skewed(df: pd.DataFrame, year: int, min_pop: int = 200) -> pd.Series:
    """Settlement with the highest male/female ratio (most male-skewed)."""
    sub = df[(df["year"] == year) & (df["population"] >= min_pop)].copy()
    sub["ratio"] = sub["male_population"] / sub["female_population"]
    return sub.loc[sub["ratio"].idxmax()][
        ["settlement_name", "male_population", "female_population", "ratio"]
    ]


def most_female_skewed(df: pd.DataFrame, year: int, min_pop: int = 200) -> pd.Series:
    """Settlement with the lowest male/female ratio (most female-skewed)."""
    sub = df[(df["year"] == year) & (df["population"] >= min_pop)].copy()
    sub["ratio"] = sub["male_population"] / sub["female_population"]
    return sub.loc[sub["ratio"].idxmin()][
        ["settlement_name", "male_population", "female_population", "ratio"]
    ]


def most_recent_new_settlement(appeared: pd.Series) -> tuple[str, int] | None:
    """The settlement that most recently became independently tracked."""
    if appeared.empty:
        return None
    settlement = (
        appeared.idxmax() if False else appeared.sort_values().index[-1]
    )
    return settlement, int(appeared.loc[settlement])


def most_recent_county_change(
    county_changes: pd.DataFrame,
) -> pd.Series | None:
    """The most recent county reassignment on record."""
    if county_changes.empty:
        return None
    return county_changes.sort_values("year").iloc[-1]


def build_history(
    appeared: pd.Series,
    county_changes: pd.DataFrame,
    type_changes: pd.DataFrame,
) -> dict[int, dict]:
    """Groups appearance/reassignment/reclassification events by year, for
    a year-by-year administrative history view."""
    years = defaultdict(lambda: {"new": [], "county": [], "types": []})

    for settlement, year in appeared.items():
        years[int(year)]["new"].append(settlement)

    for _, row in county_changes.iterrows():
        years[int(row.year)]["county"].append(row)

    for _, row in type_changes.iterrows():
        years[int(row.year)]["types"].append(row)

    return dict(sorted(years.items(), reverse=True))


def group_type_changes(
    events: list[pd.Series],
) -> dict[tuple[str, str], list[str]]:
    """Groups settlement-type reclassification events by (old, new) pair."""
    grouped = defaultdict(list)
    for row in events:
        grouped[(row.prev_val, row.new_val)].append(row.settlement_name)
    return grouped
