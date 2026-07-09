# streamlit_app/pages/geography.py
import plotly.express as px
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_geography_context, GeographyPageContext

# Editorial constants
CONCENTRATION_N = 10

@st.cache_data()
def get_context(concentration_n: int) -> GeographyPageContext:
    app = get_app_data()
    ctx = build_geography_context(
        app=app,
        concentration_n=concentration_n,
    )
    warm_cached_properties(ctx)
    return ctx


def render_thesis():
    st.title("🧭 Where It Concentrates")
    st.markdown(
        "The national decline hides a second story: population is pooling "
        "into fewer, larger places while the countryside empties out faster "
        "than the headline number suggests."
    )


def render_choropleth(ctx: GeographyPageContext):
    fig = px.choropleth_map(
        ctx.county_change,
        geojson=ctx.county_geojson,
        locations="county_name",
        featureidkey="properties.county_name",
        color="pct_change",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        hover_name="county_name",
        center={"lat": 47.1625, "lon": 19.5033},
        zoom=6, height=600,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, width="stretch")


def render_concentration_trend(ctx: GeographyPageContext):
    st.subheader(f"Share of national population in the {CONCENTRATION_N} largest settlements")
    st.plotly_chart(
        px.line(ctx.concentration_trend, x="year", y="share", markers=True),
        width="stretch",
    )


def render_dominance_table(ctx: GeographyPageContext):
    st.subheader(f"County seat dominance, {ctx.app.last_year}")
    st.caption("How much of each county's population lives in its single largest settlement.")

    fig = px.bar(
        ctx.largest_settlement_dominance.head(10),
        x="share", y="county_name", orientation="h",
        hover_data=["settlement_name"],
        title="Top 10 most dominated counties",
    )
    st.plotly_chart(fig, width="stretch")


def main():
    st.set_page_config(page_title="Geography — Hungary Population", layout="wide")

    ctx = get_context(
        concentration_n=CONCENTRATION_N,
    )

    render_thesis()
    st.divider()
    render_choropleth(ctx)
    st.divider()
    render_concentration_trend(ctx)
    st.divider()
    render_dominance_table(ctx)


main()