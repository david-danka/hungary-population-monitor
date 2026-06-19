# hpm/transform/validate_settlement.py
"""Validation suite for cleaned GeoNames settlement data.

Each private validation function checks one property of a cleaned
settlement DataFrame (the output of
hpm.transform.settlement.transform_settlement_data) and raises an
AssertionError with a descriptive message if violated. The public
validate_settlement_data function runs the full suite in sequence.

All checks here were derived empirically from data profiling; see
notebooks/02_data_profile_settlements.ipynb for the original exploration
and evidence behind each assertion.
"""

import pandas as pd

EXPECTED_BUDAPEST_DISTRICTS = 23

# Hungarian geographic bounds, per profiling Finding 2
LATITUDE_BOUNDS = (45, 49)
LONGITUDE_BOUNDS = (16, 23)


def _validate_required_columns(
    df: pd.DataFrame, required_columns: list, source: str
) -> None:
    """Check that every required column is present in the DataFrame."""
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"{source}: missing required columns: {missing}"


def _validate_no_nulls(df: pd.DataFrame, columns: tuple, source: str) -> None:
    """Check that the given columns contain no null values."""
    for col in columns:
        nulls = df[col].isna().sum()
        assert nulls == 0, f"{source}: column '{col}' has {nulls} nulls"


def _validate_coordinate_bounds(df: pd.DataFrame, source: str) -> None:
    """Check that latitude/longitude fall within valid Hungarian bounds."""
    lat_min, lat_max = LATITUDE_BOUNDS
    lon_min, lon_max = LONGITUDE_BOUNDS

    bad_lat = ~df["latitude"].between(lat_min, lat_max)
    assert not bad_lat.any(), (
        f"{source}: {bad_lat.sum()} rows with latitude outside "
        f"[{lat_min}, {lat_max}]"
    )

    bad_lon = ~df["longitude"].between(lon_min, lon_max)
    assert not bad_lon.any(), (
        f"{source}: {bad_lon.sum()} rows with longitude outside "
        f"[{lon_min}, {lon_max}]"
    )


def _validate_name_unique(df: pd.DataFrame, source: str) -> None:
    """Check that settlement name uniquely identifies each row.

    This is a postcondition on transform_settlement_data's
    drop_duplicates step. A failure here means either that step was
    removed/changed upstream, or normalization collapsed two distinct
    raw names into one before dedup ran against the wrong key.
    """
    dupes = df["name"].duplicated().sum()
    assert dupes == 0, f"{source}: {dupes} duplicate settlement names found"


def _validate_budapest_districts_complete(df: pd.DataFrame, source: str) -> None:
    """Check that all 23 normalized Budapest districts are present.

    Profiling found exactly 23 districts in the 'Budapest [IVX]+.'
    convention; after normalization these become 'Budapest 01' ..
    'Budapest 23'. A mismatch means the normalization regex stopped
    matching some raw district name (e.g. a 'kerület'-suffixed variant
    that doesn't fit the pattern).
    """
    expected = {
        f"Budapest {i:02}" for i in range(1, EXPECTED_BUDAPEST_DISTRICTS + 1)
    }
    missing = expected - set(df["name"])
    assert not missing, (
        f"{source}: missing normalized Budapest districts: {sorted(missing)}"
    )


def validate_settlement_data(
    df: pd.DataFrame, required_columns: list, source: str
) -> None:
    """
    Run the full validation suite for the cleaned settlement DataFrame.
    """
    _validate_required_columns(df, required_columns, source)
    _validate_no_nulls(df, tuple(required_columns), source)
    _validate_coordinate_bounds(df, source)
    _validate_name_unique(df, source)
    _validate_budapest_districts_complete(df, source)