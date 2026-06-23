"""Transformation utilities for cleaning and integrating datasets.

Expose the core transformation entrypoints used by the pipeline:
- :func:`transform_population_datasets`
- :func:`transform_settlement_data`
- :func:`build_star_schema`
"""

from hpm.transform.population import transform_population_datasets
from hpm.transform.settlement import transform_settlement_data
from hpm.transform.star_schema import build_star_schema

__all__ = [
    "transform_population_datasets",
    "transform_settlement_data",
    "build_star_schema",
]