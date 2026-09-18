"""Streamlit page for the overview narrative of Hungary's population changes."""

from collections.abc import Callable

import plotly.express as px
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_overview_context, OverviewPageContext

# Editorial constants
CONCENTRATION_N = 50
TOP_BOTTOM_N = 10

RELATIVE_CATEGORY_COLORS = {
    "Growing": "#2ca02c",
    "Declining slower than national average": "#f4c542",
    "Declining faster than national average": "#d62728",
}

DIVERGING_SCALE = [
    RELATIVE_CATEGORY_COLORS["Declining faster than national average"],
    RELATIVE_CATEGORY_COLORS["Declining slower than national average"],
    RELATIVE_CATEGORY_COLORS["Growing"],
]

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


@st.cache_data()
def get_context(
    concentration_n: int,
    top_bottom_n: int,
) -> OverviewPageContext:
    """Build the cached context object for the overview page.

    Args:
        concentration_n: Number of largest settlements to consider in the
            concentration summary.
        top_bottom_n: Number of settlements to highlight in the extreme
            change view.

    Returns:
        A populated overview-page context object.
    """
    app = get_app_data()
    ctx = build_overview_context(
        app=app,
        top_n_settlements=concentration_n,
        top_bottom_n=top_bottom_n,
    )
    warm_cached_properties(ctx)
    return ctx


def render_thesis() -> None:
    """Render the editorial introduction for the overview page."""
    st.caption("Part 1 of 2: The Decline")
    st.title("📉 National Overview")
    st.markdown(
        "This dashboard traces one story in two parts: a nation that's "
        "shrinking, and the specific places absorbing the loss. "
    )
    st.markdown(
        "Hungary's population has been declining for decades: and the "
        "decline isn't spread evenly. This page shows the national arc; "
        "the next page digs into *where* it's hitting hardest."
    )


def render_headline_metrics(ctx: OverviewPageContext) -> None:
    """Render the top-level KPI cards for the overview page.

    Args:
        ctx: The overview page context containing the headline metrics.
    """
    m = ctx.metrics

    st.metric(
        label=f"Population ({ctx.app.last_year})",
        value=m.latest,
        delta=m.change,
        format="%,.0f",
    )
    st.metric(
        label=f"Change since {ctx.app.first_year}",
        value=m.change_pct,
        delta=m.cagr,
        format="%.2f%%",
        delta_description="yearly CAGR",
    )
    st.metric(
        label="Settlements tracked",
        value=m.n_settlements,
        format="%,.0f",
    )


def render_concentration_teaser(ctx: OverviewPageContext) -> None:
    """Render an informational teaser about settlement concentration."""
    share = ctx.concentration_share
    st.info(
        f"📌 The **{CONCENTRATION_N} largest settlements** ({CONCENTRATION_N / ctx.metrics.n_settlements * 100:.2f}%) hold "
        f"**{share:.1f}%** of the national population, as of {ctx.app.last_year}. "
        "See *Winners & Losers* for exactly which settlements are driving the decline."
    )


def render_decline_yardstick(ctx: OverviewPageContext) -> None:
    """Render the benchmark settlement that illustrates the decline."""
    row = ctx.decline_yardstick
    verb = "lost" if ctx.metrics.change < 0 else "gained"
    st.info(
        f"🏘️ In {ctx.app.last_year - 1} alone, Hungary {verb} the equivalent of "
        f"**{row['settlement_name']}** (pop. {row['population']:,.0f})"
    )


def render_national_trend(ctx: OverviewPageContext) -> None:
    """Render the national population trend line chart."""
    st.plotly_chart(
        px.line(
            ctx.national_trend,
            x="year",
            y="population",
            title="National population over time",
        ),
        width="stretch",
    )


def render_map(ctx: OverviewPageContext) -> None:
    """Render the county-level choropleth map, colored by a user-selectable lens."""
    mode = st.radio("Color by", list(COUNTY_MAP_MODES), horizontal=True)
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


def render_section(
    title: str,
    fn: Callable[[OverviewPageContext], None],
    ctx: OverviewPageContext,
) -> None:
    """Render a titled section with a shared divider.

    Args:
        title: The section heading displayed to the user.
        fn: The renderer function for the section body.
        ctx: The context object supplied to the renderer.
    """
    st.subheader(title)
    fn(ctx)
    st.divider()


def main() -> None:
    """Render the full overview page."""
    ctx = get_context(
        concentration_n=CONCENTRATION_N,
        top_bottom_n=TOP_BOTTOM_N,
    )

    render_thesis()

    left, right = st.columns([1, 1.618])
    with left:
        render_decline_yardstick(ctx)
        render_headline_metrics(ctx)
    with right:
        render_national_trend(ctx)

    st.divider()

    render_section("🗺️ Growing vs. shrinking", render_map, ctx)
    render_concentration_teaser(ctx)


main()