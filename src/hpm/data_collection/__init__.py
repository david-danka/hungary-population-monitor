"""Data collection helpers for fetching raw source files.

This package provides convenience functions that download and stage raw
population and settlement source files required by the transformation
and integration steps.
"""

from hpm.data_collection.population import collect_population_datasets
from hpm.data_collection.settlement import collect_settlement_data

__all__ = [
    "collect_population_datasets",
    "collect_settlement_data",
]