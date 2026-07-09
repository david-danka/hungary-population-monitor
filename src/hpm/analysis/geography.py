# analysis/geography.py — new module
import pandas as pd

def county_population_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    County population for selected year

    Args:
        df (pd.DataFrame): population_settlements wide table
        year (int): year to filter by

    Returns:
        pd.DataFrame: county-level population table for `year`
    """
    return (
        df[df["year"] == year]
        .groupby("county_name", as_index=False)["population"]
        .sum()
        .sort_values("population")
    )

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

def county_population_change(df: pd.DataFrame, first_year: int, last_year: int) -> pd.DataFrame:
    """Per-county population change between two years, for choropleth coloring."""
    first = df[df["year"] == first_year].groupby("county_name", as_index=False)["population"].sum()
    last = df[df["year"] == last_year].groupby("county_name", as_index=False)["population"].sum()
    merged = first.merge(last, on="county_name", suffixes=("_first", "_last"))
    merged["pct_change"] = (merged["population_last"] / merged["population_first"] - 1) * 100
    merged["abs_change"] = merged["population_last"] - merged["population_first"]
    return merged

def concentration_share_trend(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Share of national population held by the N largest settlements, per year."""
    records = []
    for year, year_df in df.groupby("year"):
        top_n_total = year_df.nlargest(n, "population")["population"].sum()
        national_total = year_df["population"].sum()
        records.append({"year": year, "share": top_n_total / national_total * 100})
    return pd.DataFrame(records)

def largest_settlement_share_by_county(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Each county's largest settlement's share of that county's total population."""
    year_df = df[df["year"] == year]
    county_totals = year_df.groupby("county_name")["population"].sum()
    idx = year_df.groupby("county_name")["population"].idxmax()
    largest = year_df.loc[idx, ["county_name", "settlement_name", "population"]]
    largest = largest.rename(columns={"population": "largest_settlement_pop"})
    largest = largest.merge(county_totals.rename("county_total"), on="county_name")
    largest["share"] = largest["largest_settlement_pop"] / largest["county_total"] * 100
    return largest.sort_values("share", ascending=False)

def county_population_trend(df: pd.DataFrame) -> pd.DataFrame:
    """County-level population trajectory across all years."""
    return df.groupby(["county_name", "year"], as_index=False)["population"].sum()