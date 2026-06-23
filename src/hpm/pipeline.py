"""Orchestrate the end-to-end Hungary population ETL pipeline.

This module wires together collection, transformation and loading steps
into a single convenience function :func:`run_pipeline` which is used by
the CLI entrypoint and allows straightforward programmatic execution
from scripts and tests.
"""

from hpm.load import load_star_schema
from hpm.transform import (
    transform_population_datasets,
    transform_settlement_data,
    build_star_schema,
)
from hpm.data_collection import (
    collect_population_datasets,
    collect_settlement_data,
)


def run_pipeline() -> None:
    """Execute the full data pipeline from collection to database load.

    Sequence:
    1. Download and stage population and settlement source files.
    2. Transform raw files into cleaned DataFrames.
    3. Build star-schema components (dim_county, dim_settlement,
       fact_population).
    4. Persist the star schema to the configured SQLite database.

    The function performs side effects (network I/O and filesystem
    writes) and returns ``None`` on successful completion.
    """

    collect_population_datasets()
    collect_settlement_data()
    population_df = transform_population_datasets()
    settlements_df = transform_settlement_data()
    dim_county, dim_settlement, fact_population = build_star_schema(
        population_df, settlements_df
    )
    load_star_schema(dim_county, dim_settlement, fact_population)


if __name__ == "__main__":
    run_pipeline()