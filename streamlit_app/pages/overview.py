"""Streamlit page for the overview narrative of Hungary's population changes."""

from collections.abc import Callable

import plotly.express as px
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_overview_context, OverviewPageContext

# Editorial constants
CONCENTRATION_N = 50
TOP_BOTTOM_N = 10


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
    st.title("🇭🇺 The Shrinking Whole")
    st.markdown(
        "Hungary's population has been declining for decades — and the "
        "decline isn't spread evenly. This page shows the national arc; "
        "later pages dig into *where* it's hitting hardest and *why*."
    )


def render_headline_metrics(ctx: OverviewPageContext) -> None:
    """Render the top-level KPI cards for the overview page.

    Args:
        ctx: The overview page context containing the headline metrics.
    """
    m = ctx.metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label=f"Population ({ctx.app.last_year})",
        value=m.latest,
        delta=m.change,
        format="%,.0f",
    )
    col2.metric(
        label=f"Change since {ctx.app.first_year}",
        value=m.change_pct,
        delta=m.cagr,
        format="%.2f%%",
        delta_description="yearly CAGR",
    )
    col3.metric(
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
        "See the *Geography* page for how this concentration is shifting over time."
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
    """Render the interactive settlement map for the latest year."""
    import numpy as np

    settlements = ctx.settlements
    types = sorted(settlements["settlement_type"].unique())
    selected = st.multiselect("Settlement type", types, default=types)
    view = settlements[settlements["settlement_type"].isin(selected)]

    fig = px.scatter_map(
        view,
        lat="latitude",
        lon="longitude",
        size=np.sqrt(view["population"]),
        size_max=30,
        color="settlement_type",
        hover_name="settlement_name",
        hover_data={"population": True, "settlement_type": True},
        zoom=6,
        height=650,
        title=f"Settlements by population, {ctx.app.last_year}",
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
    st.set_page_config(page_title="The Shrinking Whole", layout="wide")

    ctx = get_context(
        concentration_n=CONCENTRATION_N,
        top_bottom_n=TOP_BOTTOM_N,
    )

    render_thesis()
    render_headline_metrics(ctx)
    render_concentration_teaser(ctx)
    render_decline_yardstick(ctx)
    st.divider()

    render_section("📈 The national trend", render_national_trend, ctx)
    render_section("🗺️ Where people live", render_map, ctx)


main()