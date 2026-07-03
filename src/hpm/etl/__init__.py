"""Hungary Population Monitor ETL subpackage.

Provides the orchestrator function for running the complete ETL pipeline.
"""

from hpm.etl.pipeline import run_pipeline

__all__ = [
    "run_pipeline",
]