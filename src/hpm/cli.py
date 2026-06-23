"""Console entrypoint for the Hungary Population Monitor pipeline.

This module exposes a thin `cli` function intended to be used as a
console-script entrypoint. It delegates to :func:`hpm.pipeline.run_pipeline`
to execute the full ETL pipeline.
"""

from hpm.pipeline import run_pipeline


def cli() -> None:
    """Invoke the full data pipeline.

    The function is a small wrapper suitable for use by packaging entry
    points (console_scripts). It runs the end-to-end pipeline and returns
    only after completion.
    """

    run_pipeline()