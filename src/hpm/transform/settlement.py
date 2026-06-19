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

    output_columns = [
        "name",
        "latitude",
        "longitude",
    ]

    dtypes = {
        "name": "string",
        "latitude": "float64",
        "longitude": "float64",
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
    match = re.search(schema.budapest_district_pattern, name)

    if match:
        roman_dist = match.group(1)
        district = ROMAN_TO_INT[roman_dist]
        return f"Budapest {district:02}"

    # default normalization
    return name


def transform_settlement_data() -> pd.DataFrame:
    """
    Extract populated settlements and coordinates from GeoNames dataset.
    """
    raw_df = pd.read_csv(
        settings.raw_settlements / "HU.txt",
        sep="\t",
        header=None,
        names=schema.raw_columns,
        low_memory=False,
    )

    populated = raw_df[raw_df["feature_code"].isin(schema.allowed_feature_codes)]

    filtered = populated[schema.output_columns].copy()

    filtered["name"] = filtered["name"].apply(_normalize_settlement_name)

    filtered = filtered.drop_duplicates(subset="name").reset_index(drop=True)

    filtered = filtered.astype(schema.dtypes)

    validate_settlement_data(filtered, schema.output_columns, source="HU.txt")

    return filtered
