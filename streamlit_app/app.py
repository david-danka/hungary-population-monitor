"""Application entry point.

Initializes the Hungary Population Monitor Streamlit application,
performs one-time bootstrap setup, configures the application's page
navigation, and starts the selected page.

The bootstrap step prepares shared application state before any page is
executed, ensuring each page runs against the same initialized
environment.
"""

from pathlib import Path

import streamlit as st
from hpm.bootstrap import prepare

FAVICON_PATH = Path(__file__).resolve().parent / "assets" / "hungary_flag.png"

prepare()

pg = st.navigation({
    "The Argument": [
        st.Page("pages/overview.py", title="Overview", icon="📉", default=True),
        st.Page("pages/winners_losers.py", title="Winners & Losers", icon="📊"),
    ],
    "Explore It Yourself": [
        st.Page("pages/explorer.py", title="Explorer", icon="🔎"),
        st.Page("pages/fun_facts.py", title="Fun Facts", icon="💡"),
    ],
})

st.set_page_config(
    page_title="Hungary Population Monitor",
    page_icon=str(FAVICON_PATH),
    layout="wide",
)

pg.run()