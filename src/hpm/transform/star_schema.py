import pandas as pd


NO_ADDRESS_SETTLEMENT_CODE = 0
"""KSH code for 'LAKCÍM NÉLKÜLI' (no fixed address) — a population
accounting bucket, not a real settlement. Has no GeoNames analog by
definition, so it's excluded from coordinate-match validation. See
notebooks/03_integration_validation.py, EXCLUDED_KSH_CODES.
"""


def _build_dim_county(df: pd.DataFrame) -> pd.DataFrame:
    """Extract a deduplicated county dimension from the wide population DataFrame.

    Args:
        df: Wide, cleaned population DataFrame with county_code/county_name columns.

    Returns:
        A DataFrame with one row per distinct county_code, ready for dim_county.
    """
    dim = df[["county_code", "county_name"]].dropna(subset=["county_code"])
    dim = dim.drop_duplicates(subset="county_code").sort_values("county_code")
    return dim.reset_index(drop=True)


def _build_dim_settlement(
    population_df: pd.DataFrame, settlements_df: pd.DataFrame
) -> pd.DataFrame:
    """Extract a deduplicated settlement dimension, enriched with coordinates.

    Mirrors the three-tier strategy in
    notebooks/03_integration_validation_pop_geonames.ipynb:

    Tier 1: names with exactly one GeoNames candidate match on name
    alone -- county isn't needed, and some candidates carry an
    unreliable county_code that must not be allowed to block an
    otherwise-unambiguous match.

    Tier 2: names with multiple GeoNames candidates match on
    (name, county_code) -- this correctly splits genuinely distinct
    settlements that share a name across different counties.

    Tier 3: applied AFTER the Tier 2 join, per matched settlement --
    if a settlement still matches more than one GeoNames record (a
    GeoNames-internal redundancy, not a real ambiguity), keep the one
    with the higher population, falling back to the most recent
    modification_date only when population also ties. This must
    happen after the join, not before: collapsing GeoNames duplicates
    before knowing which settlement(s) actually need them risks
    discarding a candidate a different settlement might require.

    Args:
        population_df: Wide, cleaned population DataFrame.
        settlements_df: Cleaned GeoNames settlement DataFrame (output of
            hpm.transform.settlement.transform_settlement_data), with
            name/latitude/longitude columns already normalized and
            deduplicated.

    Returns:
        A DataFrame with one row per distinct settlement_code, including
        settlement_name, latitude, and longitude, ready for
        dim_settlement.

    Raises:
        AssertionError: If any settlement fails to match a GeoNames
            record. The integration notebook found 100% coverage
            (3177/3177); a failure here means an upstream change broke
            that guarantee rather than indicating expected partial
            coverage, so this fails loudly instead of shipping nulls.
    """
    dim = population_df[
        ["settlement_code", "settlement_name", "county_code"]
    ].rename(columns={"settlement_name": "norm"})
    dim = dim.drop_duplicates(subset="settlement_code").sort_values(
        "settlement_code"
    )
    dim = dim.reset_index(drop=True)

    geo = settlements_df.rename(columns={"name": "norm"})

    name_counts = dim.merge(geo, on="norm", how="left").groupby("norm").size()
    dupe_names = set(name_counts[name_counts > 1].index)

    # Tier 1
    geo_for_t1 = geo.drop(columns=["county_code"])
    unambiguous_dim = dim[~dim["norm"].isin(dupe_names)]
    tier1 = unambiguous_dim.merge(geo_for_t1, on="norm", how="left")

    # Tier 2
    ambiguous_dim = dim[dim["norm"].isin(dupe_names)]
    tier2 = ambiguous_dim.merge(geo, on=["norm", "county_code"], how="left")

    # Tier 3 -- after the join, scoped to settlement code
    tier2_resolved = tier2.sort_values(
        ["population", "modification_date"], ascending=False, kind="stable"
    ).drop_duplicates(subset="settlement_code", keep="first")

    merged = pd.concat([tier1, tier2_resolved], ignore_index=True)

    assert merged["settlement_code"].duplicated().sum() == 0, (
        "Some settlement matched more than one GeoNames record"
    )

    real_settlements = merged[
        merged["settlement_code"] != NO_ADDRESS_SETTLEMENT_CODE
    ]

    unmatched = real_settlements[real_settlements["latitude"].isna()]
    assert unmatched.empty, (
        f"{len(unmatched)} settlements failed to match a GeoNames record: "
        f"{unmatched['settlement_name'].tolist()}"
    )

    merged = merged.drop(columns=["population", "modification_date"])

    renamed = merged.rename(columns={"norm": "settlement_name"})

    return renamed


def _build_fact_population(df: pd.DataFrame) -> pd.DataFrame:
    """Extract the population fact table from the wide population DataFrame.

    Args:
        df: Wide, cleaned population DataFrame.

    Returns:
        A DataFrame with one row per settlement per year, ready for
        fact_population.
    """
    return df[
        [
            "settlement_code",
            "settlement_type",
            "year",
            "county_code",
            "male_population",
            "female_population",
            "population",
        ]
    ].reset_index(drop=True)


def build_star_schema(
    population_df: pd.DataFrame, settlements_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split the wide population DataFrame into star schema components,
    enriching dim_settlement with GeoNames coordinates.

    Args:
        population_df: Combined, validated, wide population DataFrame.
        settlements_df: Cleaned, validated GeoNames settlement DataFrame.

    Returns:
        A tuple of (dim_county, dim_settlement, fact_population) DataFrames.
    """
    return (
        _build_dim_county(population_df),
        _build_dim_settlement(population_df, settlements_df),
        _build_fact_population(population_df),
    )
