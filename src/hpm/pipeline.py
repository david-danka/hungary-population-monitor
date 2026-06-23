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