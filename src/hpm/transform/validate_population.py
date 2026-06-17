"""Validation suite for cleaned Hungarian population data.

Each private validation function checks one property of a cleaned
population DataFrame (the output of
hpm.transformation.population._clean_population_data) and raises an
AssertionError with a descriptive message if violated. The public
validate_population_data function runs the full suite in sequence.

All checks here were derived empirically from data profiling; see
notebooks/01_data_profile_population.ipynb for the original exploration
and evidence behind each assertion.
"""

import pandas as pd


def _validate_required_columns(
    df: pd.DataFrame, required_columns: tuple, source: str
) -> None:
    """Check that every required column is present in the DataFrame.

    Args:
        df: Cleaned population DataFrame for a single year.
        required_columns: Column names that must be present.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any required column is missing.
    """
    missing = set(required_columns) - set(df.columns)
    assert not missing, f"{source}: missing required columns: {missing}"


def _validate_settlement_type_mapped(df: pd.DataFrame, source: str) -> None:
    """Check that every settlement_type value was successfully mapped.

    A null here indicates a raw settlement type value not covered by
    PopulationSchema.settlement_type_mapping, e.g. a future Excel
    introducing a new label or code.

    Args:
        df: Cleaned population DataFrame for a single year.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any settlement_type value is null.
    """
    unmapped = df["settlement_type"].isna().sum()
    assert unmapped == 0, (
        f"{source}: {unmapped} unmapped settlement types found"
    )


def _validate_settlement_code_unique(df: pd.DataFrame, source: str) -> None:
    """Check that settlement_code uniquely identifies each row.

    Args:
        df: Cleaned population DataFrame for a single year.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any settlement_code value is duplicated.
    """
    dupes = df["settlement_code"].duplicated().sum()
    assert dupes == 0, f"{source}: {dupes} duplicate settlement codes found"


def _validate_settlement_name_unique(df: pd.DataFrame, source: str) -> None:
    """Check that settlement_name uniquely identifies each row.

    Args:
        df: Cleaned population DataFrame for a single year.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any settlement_name value is duplicated.
    """
    dupes = df["settlement_name"].duplicated().sum()
    assert dupes == 0, f"{source}: {dupes} duplicate settlement names found"


def _validate_no_nulls(df: pd.DataFrame, columns: tuple, source: str) -> None:
    """Check that the given columns contain no null values.

    Args:
        df: Cleaned population DataFrame for a single year.
        columns: Column names that must be fully non-null.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any of the given columns contains a null value.
    """
    for col in columns:
        nulls = df[col].isna().sum()
        assert nulls == 0, f"{source}: column '{col}' has {nulls} nulls"


def _validate_population_positive(
    df: pd.DataFrame, columns: tuple, source: str
) -> None:
    """Check that the given population columns contain only positive values.

    Args:
        df: Cleaned population DataFrame for a single year.
        columns: Column names that must contain only values > 0.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any of the given columns contains a non-positive
            value.
    """
    for col in columns:
        assert (df[col] > 0).all(), (
            f"{source}: column '{col}' has non-positive values"
        )


def _validate_population_sums(df: pd.DataFrame, source: str) -> None:
    """Check that male_population + female_population equals population.

    Args:
        df: Cleaned population DataFrame for a single year.
        source: Label identifying the source file, used in error messages.

    Raises:
        AssertionError: If any row's male and female population does not
            sum to the total population.
    """
    mismatch = (
        df["male_population"] + df["female_population"] != df["population"]
    )
    assert not mismatch.any(), (
        f"{source}: {mismatch.sum()} rows where male+female != total"
    )


def validate_population_data(
    df: pd.DataFrame, required_columns: tuple, source: str
) -> None:
    """
    Run the full validation suite for a single year's cleaned population DataFrame.
    """
    _validate_required_columns(df, required_columns, source)
    _validate_settlement_type_mapped(df, source)
    _validate_settlement_code_unique(df, source)
    _validate_settlement_name_unique(df, source)
    _validate_no_nulls(
        df, ("settlement_code", "settlement_name", "settlement_type"), source
    )
    _validate_population_positive(
        df, ("male_population", "female_population", "population"), source
    )
    _validate_population_sums(df, source)
