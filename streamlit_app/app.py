import streamlit as st
from hpm.bootstrap import prepare

prepare()

pg = st.navigation([
    st.Page("pages/overview.py", title="Overview", icon=":material/insights:", default=True),
    st.Page("pages/geography.py", title="Geography", icon=":material/thumb_up:",),
    st.Page("pages/map.py", title="Map", icon=":material/map:"),
    st.Page("pages/trends.py", title="Trends", icon=":material/trending_up:"),
    st.Page("pages/insights.py", title="Insights", icon=":material/location_city:"),
    st.Page("pages/explorer.py", title="Explorer", icon=":material/search_insights:"),
    st.Page("pages/fun_facts.py", title="Fun Facts", icon=":material/lightbulb:"),
    st.Page("pages/sandbox.py", title="Sandbox", icon=":material/box:")
])
st.set_page_config(page_title="Hungary Population Monitor", page_icon=":material/bar_chart:")

pg.run()