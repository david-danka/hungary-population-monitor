"""Transform GeoNames settlement dumps into a cleaned settlement table.

This module normalizes GeoNames raw exports for Hungary, converts
Budapest district roman numerals into zero-padded numbers, filters the
relevant feature classes, and prepares a small, typed DataFrame used
by the star-schema integration step.
"""

import re

import pandas as pd

from hpm.settings import settings
from hpm.transform.validate_settlement import validate_settlement_data


class GeoNamesSchema:
    budapest_district_pattern = r"Budapest\s+([IVX]+)\.*"

    raw_columns = [
        "geonameid",
        "name",
        "asciiname",
        "alternatenames",
        "latitude",
        "longitude",
        "feature_class",
        "feature_code",
        "country_code",
        "cc2",
        "admin1_code",
        "admin2_code",
        "admin3_code",
        "admin4_code",
        "population",
        "elevation",
        "dem",
        "timezone",
        "modification_date",
    ]

    allowed_feature_codes = {
        "PPL",
        "PPLA",
        "PPLA2",
        "ADM2",
    }

    # GeoNames admin1_code -> KSH county_code. See
    # notebooks/03_integration_validation_pop_geonames.ipynb for the derivation.
    admin1_to_county_code = {
        1: 3,
        2: 2,
        3: 4,
        4: 5,
        5: 1,
        6: 6,
        8: 7,
        9: 8,
        10: 9,
        11: 10,
        12: 11,
        14: 12,
        16: 13,
        17: 14,
        18: 15,
        20: 16,
        21: 17,
        22: 18,
        23: 19,
        24: 20,
    }

    # population and modification_date are kept through to dim_settlement
    # construction -- they're needed by star_schema._build_dim_settlement
    # to resolve same-(name, county) GeoNames redundancy *after* the join,
    # and are dropped before the final dim_settlement output.
    output_columns = [
        "name",
        "county_code",
        "latitude",
        "longitude",
        "population",
        "modification_date",
    ]

    dtypes = {
        "name": "string",
        "county_code": "Int64",  # nullable -- stale admin1 codes -> NaN
        "latitude": "float64",
        "longitude": "float64",
        "population": "int64",
        "modification_date": "string",  # ISO format; sorts correctly as string
    }


schema = GeoNamesSchema()

ROMAN_TO_INT = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
    "XXII": 22,
    "XXIII": 23,
}


def _normalize_settlement_name(name: str) -> str:
    """
    Normalize a settlement name, converting Budapest roman-numeral
    district notation to zero-padded numeric form.
    """
    match = re.search(schema.budapest_district_pattern, name)
    if match:
        roman_dist = match.group(1)
        district = ROMAN_TO_INT[roman_dist]
        return f"Budapest {district:02}"

    # default normalization
    return name


def transform_settlement_data() -> pd.DataFrame:
    """
    Extract populated settlements, county, and coordinates from GeoNames.
    """
    raw_df = pd.read_csv(
        settings.raw_settlements / "HU.txt",
        sep="\t",
        header=None,
        names=schema.raw_columns,
        low_memory=False,
    )

    populated = raw_df[
        raw_df["feature_code"].isin(schema.allowed_feature_codes)
    ].copy()
    populated["name"] = populated["name"].apply(_normalize_settlement_name)
    populated["county_code"] = populated["admin1_code"].map(schema.admin1_to_county_code)

    filtered = populated[schema.output_columns].reset_index(drop=True)
    filtered = filtered.astype(schema.dtypes)

    validate_settlement_data(filtered, schema.output_columns, source="HU.txt")

    return filtered
