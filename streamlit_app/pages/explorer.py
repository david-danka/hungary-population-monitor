"""Streamlit page for exploring settlement-level population history."""

import plotly.express as px
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_explorer_context, ExplorerPageContext


@st.cache_data()
def get_context() -> ExplorerPageContext:
    """Build the cached context object for the explorer page.

    Returns:
        A populated explorer-page context object.
    """
    app = get_app_data()
    ctx = build_explorer_context(app)
    warm_cached_properties(ctx)
    return ctx


def render_thesis() -> None:
    """Render the introductory copy for the explorer page."""
    st.title("🔎 Explorer")
    st.markdown(
        "Look up any settlement and see its own story against the national one."
    )


def render_selector(ctx: ExplorerPageContext) -> str:
    """Render the settlement selector and return the chosen settlement name.

    Args:
        ctx: The explorer page context containing the available settlements.

    Returns:
        The selected settlement name.
    """
    options = ctx.options
    choice = st.selectbox("Settlement", options["label"])
    return options.loc[options["label"] == choice, "settlement_name"].iloc[0]


def render_summary(ctx: ExplorerPageContext, settlement_name: str) -> None:
    """Render the summary metrics for a selected settlement.

    Args:
        ctx: The explorer page context.
        settlement_name: The settlement to summarize.
    """
    s = ctx.summary(settlement_name)

    st.subheader(f"{s.settlement_name} ({s.county_name})")
    st.caption(f"{s.settlement_type.replace('_', ' ').title()}")

    c1, c2, c3 = st.columns(3)
    c1.metric(
        f"Population ({ctx.app.last_year})",
        f"{s.latest_population:,}",
        delta=s.abs_change,
    )
    c2.metric(f"Change since {ctx.app.first_year}", f"{s.pct_change:.1f}%")
    c3.metric(
        "National rank by population",
        f"#{s.population_rank} of {s.n_settlements}",
    )


def render_trend(ctx: ExplorerPageContext, settlement_name: str) -> None:
    """Render the population trend chart for a single settlement.

    Args:
        ctx: The explorer page context.
        settlement_name: The settlement to plot.
    """
    series = ctx.series(settlement_name)

    long = series.melt(
        id_vars="year",
        value_vars=["male_population", "female_population"],
        var_name="sex",
        value_name="count",
    )
    long["sex"] = long["sex"].map(
        {
            "male_population": "Male",
            "female_population": "Female",
        }
    )

    fig = px.area(
        long,
        x="year",
        y="count",
        color="sex",
        title=f"{settlement_name}: population over time",
        labels={"count": "Population", "sex": ""},
        color_discrete_map={"Male": "#4C72B0", "Female": "#DD8452"},
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width="stretch")


def render_gender_ratio(ctx: ExplorerPageContext, settlement_name: str) -> None:
    """Render the male-to-female ratio chart for one settlement.

    Args:
        ctx: The explorer page context.
        settlement_name: The settlement to plot.
    """
    series = ctx.gender_ratio(settlement_name)
    fig = px.line(
        series, x="year", y="ratio", title="Male-to-female ratio over time"
    )
    fig.add_hline(
        y=1.0,
        line_dash="dot",
        annotation_text="parity",
        annotation_position="top left",
    )
    st.plotly_chart(fig, width="stretch")


def main() -> None:
    """Render the full explorer page."""
    st.set_page_config(page_title="Explorer", layout="wide")
    ctx = get_context()

    render_thesis()
    settlement_name = render_selector(ctx)
    st.divider()
    render_summary(ctx, settlement_name)
    render_trend(ctx, settlement_name)
    render_gender_ratio(ctx, settlement_name)


main()
