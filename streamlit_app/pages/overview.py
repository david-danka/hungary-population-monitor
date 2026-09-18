"""Streamlit page for the overview narrative of Hungary's population changes."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_overview_context, OverviewPageContext

# Editorial constants
TOP_BOTTOM_N = 10
N_DECLINE_CONTRIBUTION = 50


@st.cache_data()
def get_context(
    top_bottom_n: int,
    n_decline_contribution: int,
) -> OverviewPageContext:
    """Build the cached context object for the overview page.

    Args:
        top_bottom_n: Number of settlements to highlight in the extreme
            change view.
        n_decline_contribution: Number of largest losers to use when
            estimating their contribution to overall decline.

    Returns:
        A populated overview-page context object.
    """
    app = get_app_data()
    ctx = build_overview_context(
        app=app,
        top_bottom_n=top_bottom_n,
        n_largest_losers=n_decline_contribution,
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


def render_decline_contribution(ctx: OverviewPageContext) -> None:
    """Render the contribution of the biggest losers to overall decline."""
    pct = ctx.decline_contribution
    st.info(
        f"📌 The **{N_DECLINE_CONTRIBUTION} settlements** with the steepest population losses "
        f"account for **{pct:.1f}%** of all population lost across every "
        f"shrinking settlement in the dataset."
    )


def render_growth_decline_count(ctx: OverviewPageContext) -> None:
    """Render the headline counts of growing and declining settlements."""
    counts = ctx.direction_counts
    st.metric("📈 Settlements grew", counts["Growth"])
    st.metric("📉 Settlements declined", counts["Decline"])


def render_growth_decline_summary(ctx: OverviewPageContext) -> None:
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
        f"above ({ctx.app.first_year}→{ctx.app.last_year} settlement-level sum); "
        "small differences can arise from settlements appearing/merging between years."
    )


def render_growth_decline_by_year(ctx: OverviewPageContext) -> None:
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


def main() -> None:
    """Render the full overview page."""
    ctx = get_context(
        top_bottom_n=TOP_BOTTOM_N,
        n_decline_contribution=N_DECLINE_CONTRIBUTION,
    )

    render_thesis()

    left, right = st.columns([1, 1.618])
    with left:
        render_decline_yardstick(ctx)
        render_headline_metrics(ctx)
    with right:
        render_national_trend(ctx)

    st.divider()

    wide, narrow = st.columns([1.618, 1])
    with wide:
        render_growth_decline_summary(ctx)
    with narrow:
        render_decline_contribution(ctx)
        render_growth_decline_count(ctx)

    render_growth_decline_by_year(ctx)


main()