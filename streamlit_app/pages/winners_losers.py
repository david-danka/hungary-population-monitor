"""Streamlit page for highlighting settlements that gained or lost population."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared import get_app_data, warm_cached_properties, RELATIVE_CATEGORY_COLORS, DIVERGING_SCALE
from hpm.ui.context import build_change_context, ChangePageContext

# Editorial constants, not exposed to users
N_DECLINE_CONTRIBUTION = 50


@st.cache_data()
def get_context(n_decline_contribution: int) -> ChangePageContext:
    """Build the cached change-page context.

    Args:
        n_decline_contribution: Number of largest losers to use when estimating
            their contribution to overall decline.

    Returns:
        A populated change-page context object.
    """
    app = get_app_data()
    ctx = build_change_context(
        app=app,
        n_largest_losers=n_decline_contribution,
    )
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


def render_decline_contribution(ctx: ChangePageContext) -> None:
    """Render the contribution of the biggest losers to overall decline."""
    pct = ctx.decline_contribution
    st.info(
        f"📌 The **{N_DECLINE_CONTRIBUTION} settlements** with the steepest population losses "
        f"account for **{pct:.1f}%** of all population lost across every "
        f"shrinking settlement in the dataset."
    )


def render_growth_decline_count(ctx: ChangePageContext) -> None:
    """Render the headline counts of growing and declining settlements."""
    counts = ctx.direction_counts
    c1, c2 = st.columns(2)
    c1.metric("📈 Settlements grew", counts["Growth"])
    c2.metric("📉 Settlements declined", counts["Decline"])


def render_growth_decline_summary(ctx: ChangePageContext) -> None:
    """Render the waterfall summary of growth, decline, and net change."""
    totals = ctx.total_change_by_direction
    fig = go.Figure(
        go.Waterfall(
            x=totals["label"],
            y=totals["value"],
            measure=totals["measure"],
            decreasing={"marker": {"color": "#d62728"}},
            increasing={"marker": {"color": "#2ca02c"}},
            totals={"marker": {"color": "#1f77b4"}},
            text=[f"{v:,.0f}" for v in totals["value"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Growth, decline, and the net", showlegend=False, height=350
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        f"Net change here should roughly match the national YoY figure "
        f"on Overview ({ctx.app.first_year}→{ctx.app.last_year} settlement-level sum); "
        "small differences can arise from settlements appearing/merging between years."
    )


def render_growth_decline_by_year(ctx: ChangePageContext) -> None:
    """Render the year-by-year chart of growth, decline, and net change."""
    yearly = ctx.yearly_totals
    fig = go.Figure()
    fig.add_bar(
        x=yearly["year"],
        y=yearly["total_growth"],
        name="Growth",
        marker_color="#2ca02c",
    )
    fig.add_bar(
        x=yearly["year"],
        y=yearly["total_decline"],
        name="Decline",
        marker_color="#d62728",
    )
    fig.add_scatter(
        x=yearly["year"],
        y=yearly["net"],
        name="Net",
        mode="lines+markers",
        line_color="#1f77b4",
    )
    fig.update_layout(
        barmode="relative",
        title="Growth, decline, and the net — by year",
        height=400,
    )
    st.plotly_chart(fig, width="stretch")


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


def main() -> None:
    """Render the full winners-and-losers page."""
    ctx = get_context(
        n_decline_contribution=N_DECLINE_CONTRIBUTION,
    )

    render_thesis()
    render_map(ctx)
    st.divider()
    render_leaderboard(ctx)
    st.divider()
    render_decline_contribution(ctx)
    render_growth_decline_count(ctx)
    render_growth_decline_summary(ctx)
    render_growth_decline_by_year(ctx)


main()
