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
        zoom=6,
        height=600,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, width="stretch")


def render_concentration_trend(ctx: GeographyPageContext):
    st.subheader(
        f"Share of national population in the {CONCENTRATION_N} largest settlements"
    )
    st.plotly_chart(
        px.line(ctx.concentration_trend, x="year", y="share", markers=True),
        width="stretch",
    )


def render_dominance_table(ctx: GeographyPageContext):
    st.subheader(f"County seat dominance, {ctx.app.last_year}")
    st.caption(
        "How much of each county's population lives in its single largest settlement."
    )

    fig = px.bar(
        ctx.largest_settlement_dominance.head(10),
        x="share",
        y="county_name",
        orientation="h",
        hover_data=["settlement_name"],
        title="Top 10 most dominated counties",
    )
    st.plotly_chart(fig, width="stretch")


def index_to_first_year(view, group_col):
    view = view.copy()

    first_vals = (
        view.sort_values("year").groupby(group_col)["population"].first()
    )

    view["indexed"] = view.apply(
        lambda r: r["population"] / first_vals[r[group_col]] * 100, axis=1
    )

    return view


def render_county_trends(ctx: GeographyPageContext):
    st.subheader("County population over time")
    indexed = st.checkbox("Index to first year = 100", value=True)
    view = ctx.county_population_trend

    if indexed:
        view = index_to_first_year(view, "county_name")
        y_col = "indexed"
    else:
        y_col = "population"

    st.plotly_chart(
        px.line(view, x="year", y=y_col, color="county_name"),
        width="stretch",
    )


def main():
    st.set_page_config(
        page_title="Geography — Hungary Population", layout="wide"
    )

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
    st.divider()
    render_county_trends(ctx)


main()
