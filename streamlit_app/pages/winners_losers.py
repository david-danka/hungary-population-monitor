"""Streamlit page for highlighting settlements that gained or lost population."""

import plotly.express as px
import streamlit as st

from shared import get_app_data, warm_cached_properties, RELATIVE_CATEGORY_COLORS, DIVERGING_SCALE
from hpm.ui.context import build_change_context, ChangePageContext


@st.cache_data()
def get_context() -> ChangePageContext:
    """Build the cached change-page context.

    Returns:
        A populated change-page context object.
    """
    app = get_app_data()
    ctx = build_change_context(app=app)
    warm_cached_properties(ctx)
    return ctx


def render_thesis() -> None:
    """Render the introductory copy for the winners-and-losers page."""
    st.caption("Part 2 of 2: Winners & Losers")
    st.title("📊 Winners & Losers")
    st.markdown(
        "The national decline isn't one uniform slide — it's concentrated "
        "in a specific set of places, while others are actually growing. "
        "This page names them."
    )


def render_leaderboard(ctx: ChangePageContext) -> None:
    """Render the leaderboard of biggest gainers and losers."""
    st.subheader("Leaderboard")
    min_baseline_pop = st.slider(
        "Minimum baseline population",
        0,
        5000,
        200,
        step=50,
        help="Excludes tiny settlements where small absolute swings look like huge percentages.",
    )
    n_rows = st.slider("Rows to show", 5, 30, 15)
    metric = st.radio(
        "Rank by", ["Absolute change", "Percent change"], horizontal=True
    )

    change = ctx.change[ctx.change["population_first"] >= min_baseline_pop]
    col = "abs_change" if metric == "Absolute change" else "pct_change"

    losers = change.nsmallest(n_rows, col)[
        ["settlement_name", "settlement_type", col]
    ]
    gainers = change.nlargest(n_rows, col)[
        ["settlement_name", "settlement_type", col]
    ]

    left, right = st.columns(2)
    with left:
        st.markdown("**📉 Biggest losers**")
        st.dataframe(losers, hide_index=True, width="stretch")
    with right:
        st.markdown("**📈 Biggest gainers**")
        st.dataframe(gainers, hide_index=True, width="stretch")


MAP_MODES = {
    "Relative to national": {
        "color": "relative_category",
        "color_discrete_map": RELATIVE_CATEGORY_COLORS,
        "title": "Settlement performance, {first_year} → {last_year}",
        "caption": (
            "Settlements are colored by how they compare to the national "
            "baseline, not raw magnitude — so a village losing population "
            "slower than the national average still reads as 'doing OK'."
        ),
    },
    "Percent magnitude": {
        "color": "pct_change",
        "color_continuous_scale": DIVERGING_SCALE,
        "color_continuous_midpoint": 0,
        "range_color": [-10, 10],
        "title": "Settlement performance by magnitude, {first_year} → {last_year}",
        "caption": (
            "Ignores the national baseline entirely — color reflects each "
            "settlement's own percentage change directly, so the deepest "
            "reds and greens are the most extreme movers in relative terms."
        ),
    },
    "Absolute headcount": {
        "color": "abs_change",
        "color_continuous_scale": DIVERGING_SCALE,
        "color_continuous_midpoint": 0,
        "range_color": [-1000, 1000],
        "title": "Settlement performance by headcount, {first_year} → {last_year}",
        "caption": (
            "Colored by raw population gained or lost, not percentage — "
            "this is where the national decline's actual bodies are "
            "concentrated. A big city losing 1% can outweigh a village "
            "losing 50%."
        ),
    },
}


def render_map(ctx: ChangePageContext) -> None:
    """Render the settlement map, colored by a user-selectable lens."""
    st.subheader("Map: settlement performance")
    mode = st.radio("Color by", list(MAP_MODES), horizontal=True)
    settings = MAP_MODES[mode]

    st.caption(settings["caption"])

    fig = px.choropleth_map(
        ctx.change_with_category,
        geojson=ctx.app.settlement_geojson,
        locations="settlement_name",
        featureidkey="properties.settlement_name",
        color=settings["color"],
        color_discrete_map=settings.get("color_discrete_map"),
        color_continuous_scale=settings.get("color_continuous_scale"),
        color_continuous_midpoint=settings.get("color_continuous_midpoint"),
        range_color=settings.get("range_color"),
        center={"lat": 47.1625, "lon": 19.5033},
        zoom=6,
        height=650,
        title=settings["title"].format(
            first_year=ctx.app.first_year, last_year=ctx.app.last_year
        ),
        hover_name="settlement_name",
        hover_data={"pct_change": ":.1f", "abs_change": ":,.0f"},
    )

    fig.update_layout(
        map_style="carto-positron", margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    st.plotly_chart(fig, width="stretch", theme="streamlit")


COUNTY_MAP_MODES = {
    "Relative to national": {
        "data": "county_change_with_category",
        "color": "relative_category",
        "color_discrete_map": RELATIVE_CATEGORY_COLORS,
        "title": "County performance, {first_year} → {last_year}",
        "caption": (
            "Counties are colored by how they compare to the national "
            "baseline, not raw magnitude — so a county losing population "
            "slower than the national average still reads as 'doing OK'."
        ),
    },
    "Percent magnitude": {
        "data": "county_change",
        "color": "pct_change",
        "color_continuous_scale": DIVERGING_SCALE,
        "color_continuous_midpoint": 0,
        "title": "County performance by magnitude, {first_year} → {last_year}",
        "caption": (
            "Ignores the national baseline entirely — color reflects each "
            "county's own percentage change directly."
        ),
    },
    "Absolute headcount": {
        "data": "county_change",
        "color": "abs_change",
        "color_continuous_scale": DIVERGING_SCALE,
        "color_continuous_midpoint": 0,
        "title": "County performance by headcount, {first_year} → {last_year}",
        "caption": (
            "Colored by raw population gained or lost, not percentage — "
            "this is where the national decline's actual bodies are "
            "concentrated."
        ),
    },
}


def render_county_map(ctx: ChangePageContext) -> None:
    """Render the county-level choropleth map, colored by a user-selectable lens."""
    st.subheader("Map: county performance")
    mode = st.radio("Color by", list(COUNTY_MAP_MODES), horizontal=True, key="county_map_mode")
    settings = COUNTY_MAP_MODES[mode]

    st.caption(settings["caption"])

    fig = px.choropleth_map(
        getattr(ctx, settings["data"]),
        geojson=ctx.county_geojson,
        locations="county_name",
        featureidkey="properties.county_name",
        color=settings["color"],
        color_discrete_map=settings.get("color_discrete_map"),
        color_continuous_scale=settings.get("color_continuous_scale"),
        color_continuous_midpoint=settings.get("color_continuous_midpoint"),
        range_color=settings.get("range_color"),
        center={"lat": 47.1625, "lon": 19.5033},
        zoom=6,
        height=650,
        hover_name="county_name",
        title=settings["title"].format(
            first_year=ctx.app.first_year, last_year=ctx.app.last_year
        ),
    )

    fig.update_layout(
        map_style="carto-positron",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )

    st.plotly_chart(fig, width="stretch", theme="streamlit")


def main() -> None:
    """Render the full winners-and-losers page."""
    ctx = get_context()

    render_thesis()
    render_county_map(ctx)
    st.divider()
    render_map(ctx)
    st.divider()
    render_leaderboard(ctx)


main()
