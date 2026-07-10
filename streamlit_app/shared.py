import functools
from typing import Any
import streamlit as st

from hpm.ui.context import load_app_data, AppData

@st.cache_data()
def get_app_data() -> AppData:
    """Return the application's shared dataset
    
    Single shared entry point for the app's base dataset. Every page
    calls this same function, so ``@st.cache_data`` dedupes across pages — the
    real DB fetch happens once per session, not once per page.

    Returns:
        AppData: Fully initialized application dataset shared across all
        Streamlit pages.

    """
    return load_app_data()


def warm_cached_properties(obj: Any) -> None:
    """Eagerly evaluate all ``@cached_property`` attributes on an object.
    
    ``@st.cache_data`` deep-copies its cached value on every retrieval, so a
    lazy cached_property would recompute on every rerun instead of only
    once. Forcing computation here, before the object is cached, means
    reruns copy already-computed results instead of recomputing them.

    Args:
        obj: Instance whose ``@cached_property`` attributes should be
            evaluated.
    
    Returns:
        None.
    """
    cls = type(obj)
    for name in dir(cls):
        if isinstance(getattr(cls, name, None), functools.cached_property):
            getattr(obj, name)