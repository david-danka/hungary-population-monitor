import streamlit as st

from hpm.ui.context import load_app_data, AppData

@st.cache_data()
def get_app_data() -> AppData:
    """Single shared entry point for the app's base dataset. Every page
    calls this same function, so st.cache_data dedupes across pages — the
    real DB fetch happens once per session, not once per page."""
    return load_app_data()