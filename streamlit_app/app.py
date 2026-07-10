"""Application entry point.

Initializes the Hungary Population Monitor Streamlit application,
performs one-time bootstrap setup, configures the application's page
navigation, and starts the selected page.

The bootstrap step prepares shared application state before any page is
executed, ensuring each page runs against the same initialized
environment.
"""

import streamlit as st
from hpm.bootstrap import prepare

prepare()

pg = st.navigation([
    st.Page("pages/overview.py", title="Overview", icon=":material/insights:", default=True),
    st.Page("pages/geography.py", title="Geography", icon=":material/thumb_up:",),
    st.Page("pages/winners_losers.py", title="Winners & Losers", icon=":material/thumb_up:",),
    st.Page("pages/explorer.py", title="Explorer", icon=":material/search_insights:"),
    st.Page("pages/fun_facts.py", title="Fun Facts", icon=":material/lightbulb:"),
])
st.set_page_config(page_title="Hungary Population Monitor", page_icon=":material/bar_chart:")

pg.run()