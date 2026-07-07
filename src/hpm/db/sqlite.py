from __future__ import annotations

import pandas as pd

from hpm.db.connection import connect


def query(sql: str, **params) -> pd.DataFrame:
    """
    Execute a SQL query and return the result as a DataFrame.

    This function provides the single entry point for data access
    in the application. It handles connection lifecycle management
    and returns query results in a pandas-friendly format.

    Parameters:
        sql (str): SQL query string. Can include named parameters
            in the form :param_name.
        **params: Values for parameterized query execution.

    Returns:
        pd.DataFrame: Query result as a DataFrame. Returns an empty
        DataFrame if the query produces no rows.
    """
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params or None)