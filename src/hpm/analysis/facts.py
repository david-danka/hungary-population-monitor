"""Administrative and demographic 'fun facts' analysis.

Detects settlement lifecycle events (new settlements, mergers), county and
settlement-type reassignments, extreme gender ratios, and population
records -- feeding the Fun Facts page.
"""
from __future__ import annotations

from collections import defaultdict

import pandas as pd


def find_attribute_changes(df: pd.DataFrame, attr_col: str) -> pd.DataFrame:
    """Finds settlements whose attribute value changed between consecutive years.

    Args:
        df: Wide settlement-population table with `settlement_name`,
            `year`, and the column named by `attr_col`.
        attr_col: Name of the column to detect changes in (e.g.
            `"county_name"` or `"settlement_type"`).

    Returns:
        One row per detected change, with columns `settlement_name`,
        `prev_year`, `year` (the year the new value was first recorded),
        `prev_val`, and `new_val`. Rows with no prior recorded value
        (a settlement's first appearance) are excluded, since there is
        nothing to compare against.
    """
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
    """Finds settlements that started or stopped being tracked mid-series.

    Args:
        df: Wide settlement-population table with `settlement_name` and
            `year` columns.

    Returns:
        Tuple of `(appeared, disappeared)`:

        - `appeared`: Series indexed by `settlement_name`, valued by the
          year each settlement was first recorded, for settlements whose
          first recorded year is later than the dataset's overall first
          year (i.e. newly independent settlements).
        - `disappeared`: Series indexed by `settlement_name`, valued by
          the year each settlement was last recorded, for settlements
          whose last recorded year is earlier than the dataset's overall
          last year (i.e. merged/absorbed settlements).
    """
    first_seen = df.groupby("settlement_name")["year"].min()
    last_seen = df.groupby("settlement_name")["year"].max()
    first_year, last_year = df["year"].min(), df["year"].max()

    appeared = first_seen[first_seen > first_year]
    disappeared = last_seen[last_seen < last_year]
    return appeared, disappeared


def least_populated(df: pd.DataFrame, year: int | None = None) -> pd.Series:
    """Finds the single least-populated settlement.

    Args:
        df: Wide settlement-population table with `settlement_name`,
            `year`, and `population` columns.
        year: Year to filter by. If `None`, searches across all
            (settlement, year) rows in `df`, so the result may reflect
            any year in the dataset, not necessarily the same one for
            different calls.

    Returns:
        Series with `settlement_name`, `year`, and `population` for the
        row with the minimum population found.
    """
    sub = df if year is None else df[df["year"] == year]
    row = sub.loc[sub["population"].idxmin()]
    return row[["settlement_name", "year", "population"]]


def most_male_skewed(df: pd.DataFrame, year: int, min_pop: int = 200) -> pd.Series:
    """Finds the settlement with the highest male-to-female population ratio.

    Args:
        df: Wide settlement-population table with `year`,
            `male_population`, `female_population`, and `population`
            columns.
        year: Year to filter by.
        min_pop: Minimum total population a settlement must have to be
            considered. Excludes tiny settlements where a handful of
            people produce an extreme, not-meaningful ratio. Defaults
            to 200.

    Returns:
        Series with `settlement_name`, `male_population`,
        `female_population`, and `ratio` (male / female) for the
        settlement with the highest ratio among those meeting `min_pop`.
    """
    sub = df[(df["year"] == year) & (df["population"] >= min_pop)].copy()
    sub["ratio"] = sub["male_population"] / sub["female_population"]
    return sub.loc[sub["ratio"].idxmax()][
        ["settlement_name", "male_population", "female_population", "ratio"]
    ]


def most_female_skewed(df: pd.DataFrame, year: int, min_pop: int = 200) -> pd.Series:
    """Finds the settlement with the lowest male-to-female population ratio.

    Args:
        df: Wide settlement-population table with `year`,
            `male_population`, `female_population`, and `population`
            columns.
        year: Year to filter by.
        min_pop: Minimum total population a settlement must have to be
            considered. Excludes tiny settlements where a handful of
            people produce an extreme, not-meaningful ratio. Defaults
            to 200.

    Returns:
        Series with `settlement_name`, `male_population`,
        `female_population`, and `ratio` (male / female) for the
        settlement with the lowest ratio among those meeting `min_pop`.
    """
    sub = df[(df["year"] == year) & (df["population"] >= min_pop)].copy()
    sub["ratio"] = sub["male_population"] / sub["female_population"]
    return sub.loc[sub["ratio"].idxmin()][
        ["settlement_name", "male_population", "female_population", "ratio"]
    ]


def most_recent_new_settlement(appeared: pd.Series) -> tuple[str, int] | None:
    """Finds the settlement that most recently became independently tracked.

    Args:
        appeared: The `appeared` Series returned by `find_appearance_events`
            (indexed by `settlement_name`, valued by first-appearance year).

    Returns:
        Tuple of `(settlement_name, year)` for the settlement with the
        latest first-appearance year, or `None` if `appeared` is empty.
    """
    if appeared.empty:
        return None
    settlement = appeared.idxmax()
    return settlement, int(appeared.loc[settlement])


def most_recent_county_change(
    county_changes: pd.DataFrame,
) -> pd.Series | None:
    """Finds the most recent county reassignment on record.

    Args:
        county_changes: Output of `find_attribute_changes(df, "county_name")`.

    Returns:
        Series for the row with the latest `year`, or `None` if
        `county_changes` is empty.
    """
    if county_changes.empty:
        return None
    return county_changes.sort_values("year").iloc[-1]


def build_history(
    appeared: pd.Series,
    county_changes: pd.DataFrame,
    type_changes: pd.DataFrame,
) -> dict[int, dict]:
    """Groups appearance, county, and type-change events by year.

    Args:
        appeared: The `appeared` Series returned by `find_appearance_events`.
        county_changes: Output of `find_attribute_changes(df, "county_name")`.
        type_changes: Output of `find_attribute_changes(df, "settlement_type")`.

    Returns:
        Dict mapping each year (with at least one recorded event) to a
        dict with keys `"new"` (list of settlement names that appeared
        that year), `"county"` (list of county-change rows that year),
        and `"types"` (list of type-change rows that year). Sorted by
        year, most recent first.
    """
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
    """Groups settlement-type reclassification events by (old, new) pair.

    Args:
        events: List of rows (as in `build_history`'s `"types"` list),
            each with `prev_val`, `new_val`, and `settlement_name`.

    Returns:
        Dict mapping each `(prev_val, new_val)` pair to the list of
        settlement names that made that specific reclassification.
    """
    grouped = defaultdict(list)
    for row in events:
        grouped[(row.prev_val, row.new_val)].append(row.settlement_name)
    return grouped
