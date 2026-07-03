"""Transform raw Hungarian population Excel files into a clean, normalized dataset.

This module loads the raw population workbooks published
yearly by KSH (Hungarian Central Statistical Office), normalizes their
inconsistent schema across 2011-2026.

Schema assumptions and known anomalies (column renames, settlement type
encoding changes, the 2013 typo, the 2017 type inconsistency, etc.) were
derived from notebooks/01_data_profile_population.ipynb and are encoded
as constants on PopulationSchema below.
"""

import re
from pathlib import Path

import pandas as pd

from hpm.settings import settings
from hpm.etl.transform.validate_population import validate_population_data


class PopulationSchema:
    """Canonical assumptions for Hungarian population Excel files.

    All values here were derived empirically from data profiling
    (see notebooks/01_data_profile_population.ipynb) rather than assumed.

    Attributes:
        min_rows: Minimum expected row count per workbook, used as a
            sanity check during validation.
        sheet_index: Index of the worksheet containing data (always the
            first and only sheet).
        year_pattern: Regex used to extract the 4-digit year from the
            worksheet name.
        header_row: Zero-indexed row number where column headers live.
        column_mapping: Maps raw, era-specific Hungarian column names to
            canonical English field names.
        county_code_mapping: Maps 3-letter county abbreviations to their
            integer county code, used to backfill county_code for years
            (2011-2012) where the raw data lacks a county code column.
        settlement_type_mapping: Maps every known raw settlement type
            representation (string labels across two eras, numeric codes
            from 2026+, and known anomalies like the 2013 typo and 2017
            int/string inconsistency) to a canonical settlement type.
        dtypes: Final pandas dtypes applied to each output column.
        required_columns: Columns that must be present in the cleaned
            output; anything else is dropped.
    """

    sheet_index = 0
    year_pattern = r"(20\d{2})"
    header_row = 1

    # Column mapping
    column_mapping = {
        "Megye\nkód": "county_code",
        "Vármegye\nkód": "county_code",
        "KSH\nkód": "settlement_code",
        "Megye": "county_name",
        "Vármegye": "county_name",
        "Település": "settlement_name",
        "Település\ntípusa": "settlement_type",
        "Állandó férfi\nlakosság összesen": "male_population",
        "Állandó női\nlakosság összesen": "female_population",
        "Állandó lakosság\nösszesen": "population",
    }

    # County code mappings
    county_code_mapping = {
        "AAA": 0,
        "BAC": 3,
        "BAR": 2,
        "BEK": 4,
        "BOR": 5,
        "BUD": 1,
        "CSO": 6,
        "FEJ": 7,
        "GYO": 8,
        "HAJ": 9,
        "HEV": 10,
        "KOM": 11,
        "NOG": 12,
        "PES": 13,
        "SOM": 14,
        "SZA": 15,
        "SZO": 16,
        "TOL": 17,
        "VAS": 18,
        "VES": 19,
        "ZAL": 20,
    }

    # Settlement type mappings
    settlement_type_mapping = {
        # dummy
        "0": "no_address",
        # capital district
        "fővárosi kerület": "capital_district",
        "1": "capital_district",
        # county seat
        "megye székhely": "county_seat",
        "vármegye székhely": "county_seat",
        "2": "county_seat",
        # county-rank town
        "megyei jogú város": "county_rank_town",
        "megye jogú város": "county_rank_town",  # 2013 typo
        "vármegyei jogú város": "county_rank_town",
        "3": "county_rank_town",
        # town
        "város": "town",
        "6": "town",
        # large village
        "nagyközség": "large_village",
        "7": "large_village",
        # village
        "község": "village",
        "8": "village",
    }

    # Data types
    dtypes = {
        "settlement_code": "int64",
        "county_code": "Int64",  # nullable, since 2011-2012 lack it
        "county_name": "string",
        "settlement_name": "string",
        "settlement_type": "string",
        "male_population": "int64",
        "female_population": "int64",
        "population": "int64",
        "year": "int64",
    }

    # Required columns
    required_columns: tuple = (
        "county_code",
        "county_name",
        "settlement_name",
        "settlement_code",
        "settlement_type",
        "male_population",
        "female_population",
        "population",
    )


schema = PopulationSchema()


def _extract_year(xl: pd.ExcelFile) -> int | None:
    """Extract the 4-digit year from a workbook's sheet name.

    Args:
        xl: An opened Excel file handle for a single year's workbook.

    Returns:
        The extracted year as an integer, or None if no match was found.
    """
    match = re.search(schema.year_pattern, xl.sheet_names[0])
    year_from_sheetname = int(match.group(1)) if match else None

    return year_from_sheetname


def _clean_population_data(xl: pd.ExcelFile) -> pd.DataFrame:
    """Clean and normalize a single year's raw population workbook.

    Renames columns to canonical names, backfills missing county codes,
    normalizes settlement type encoding, strips whitespace anomalies from
    Budapest district names, and applies final dtypes.

    Args:
        xl: An opened Excel file handle for a single year's workbook.

    Returns:
        A cleaned DataFrame with columns matching
        PopulationSchema.required_columns plus a year column.
    """
    df = pd.read_excel(
        xl,
        header=schema.header_row,
        index_col=None,
        sheet_name=schema.sheet_index,
    )

    # Normalize column names
    df = df.rename(columns=schema.column_mapping)

    # Drop all, but required columns
    df = df.drop(columns=df.columns.difference(schema.required_columns))

    # County_code is absent in 2011-2012; backfill county_code
    if "county_code" not in df.columns:
        df["county_code"] = df["county_name"].map(schema.county_code_mapping)

    # Normalize settlement types
    df["settlement_type"] = (
        df["settlement_type"].astype(str).map(schema.settlement_type_mapping)
    )

    # Strip redundant whitespace from Budapest district names
    df["settlement_name"] = (
        df["settlement_name"].str.replace(r"\s+", " ", regex=True).str.strip()
    )

    # Add year
    df["year"] = _extract_year(xl)

    # Apply datatypes
    df = df.astype(schema.dtypes)

    return df


def transform_population_datasets() -> pd.DataFrame:
    """Clean, validate, and persist all raw population workbooks.

    Iterates over every Excel file in the raw population directory,
    cleans and validates each one individually, then concatenates and
    saves the combined result as a single CSV.

    Returns:
        The combined, cleaned population DataFrame spanning all years.
    """
    all_dfs = []

    for xl_file in settings.raw_population.iterdir():
        xl = pd.ExcelFile(xl_file)
        df = _clean_population_data(xl)
        validate_population_data(
            df, schema.required_columns, source=xl_file.name
        )
        all_dfs.append(df)

    return pd.concat(all_dfs)
