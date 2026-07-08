# streamlit_app/pages/geography.py
import plotly.express as px
import streamlit as st

from hpm.ui.context import load_geography_context, GeographyPageContext
from hpm.ui.selectors import read_geography_params, GeographyParams


@st.cache_data()
def get_context(params: GeographyParams) -> GeographyPageContext:
    return load_geography_context(params)


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
    st.subheader(f"Share of national population in the {ctx.params.concentration_n} largest settlements")
    st.plotly_chart(
        px.line(ctx.concentration_trend, x="year", y="share", markers=True),
        width="stretch",
    )


def render_dominance_table(ctx: GeographyPageContext):
    st.subheader(f"County seat dominance, {ctx.last_year}")
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

    params = read_geography_params()
    ctx = get_context(params)

    render_thesis()
    st.divider()
    render_choropleth(ctx)
    st.divider()
    render_concentration_trend(ctx)
    st.divider()
    render_dominance_table(ctx)


main()