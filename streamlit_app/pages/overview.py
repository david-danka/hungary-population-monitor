# streamlit_app/pages/overview.py
from collections.abc import Callable

import plotly.express as px
import streamlit as st

from hpm.ui.context import load_overview_context, OverviewPageContext
from hpm.ui.selectors import read_overview_params, OverviewParams

CONCENTRATION_N = 50  # display constant, not a user-tunable param


@st.cache_data()
def get_context(params: OverviewParams) -> OverviewPageContext:
    return load_overview_context(params)


def render_thesis():
    st.title("🇭🇺 The Shrinking Whole")
    st.markdown(
        "Hungary's population has been declining for decades — and the "
        "decline isn't spread evenly. This page shows the national arc; "
        "later pages dig into *where* it's hitting hardest and *why*."
    )


def render_headline_metrics(ctx: OverviewPageContext) -> None:
    m = ctx.metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label=f"Population ({ctx.last_year})",
        value=m.latest, delta=m.change, format="%,.0f",
    )
    col2.metric(
        label=f"Change since {ctx.first_year}",
        value=m.change_pct, delta=m.cagr,
        format="%.2f%%", delta_description="yearly CAGR",
    )
    col3.metric(
        label="Settlements tracked",
        value=m.n_settlements, format="%,.0f",
    )


def render_concentration_teaser(ctx: OverviewPageContext) -> None:
    share = ctx.concentration_share(CONCENTRATION_N)
    st.info(
        f"📌 The **{CONCENTRATION_N} largest settlements** ({CONCENTRATION_N / ctx.metrics.n_settlements * 100:.2f}%) hold "
        f"**{share:.1f}%** of the national population, as of {ctx.last_year}. "
        "See the *Geography* page for how this concentration is shifting over time."
    )


def render_decline_yardstick(ctx: OverviewPageContext) -> None:
    row = ctx.decline_yardstick
    verb = "lost" if ctx.metrics.change < 0 else "gained"
    st.info(
        f"🏘️ In {ctx.last_year - 1} alone, Hungary {verb} the equivalent of "
        f"**{row['settlement_name']}** (pop. {row['population']:,.0f})"
    )


def render_national_trend(ctx: OverviewPageContext):
    st.plotly_chart(
        px.line(ctx.national_trend, x="year", y="population",
                title="National population over time"),
        width="stretch",
    )


def render_map(ctx: OverviewPageContext):
    import numpy as np
    settlements = ctx.settlements
    types = sorted(settlements["settlement_type"].unique())
    selected = st.multiselect("Settlement type", types, default=types)
    view = settlements[settlements["settlement_type"].isin(selected)]

    fig = px.scatter_map(
        view, lat="latitude", lon="longitude",
        size=np.sqrt(view["population"]), size_max=30,
        color="settlement_type", hover_name="settlement_name",
        hover_data={"population": True, "settlement_type": True},
        zoom=6, height=650,
        title=f"Settlements by population, {ctx.last_year}",
    )
    fig.update_layout(map_style="carto-positron", margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_section(title, fn: Callable[[OverviewPageContext], None], ctx):
    st.subheader(title)
    fn(ctx)
    st.divider()


def main():
    st.set_page_config(page_title="The Shrinking Whole", layout="wide")

    params = read_overview_params()
    ctx = get_context(params)

    render_thesis()
    render_headline_metrics(ctx)
    render_concentration_teaser(ctx)
    render_decline_yardstick(ctx)
    st.divider()

    render_section("📈 The national trend", render_national_trend, ctx)
    render_section("🗺️ Where people live", render_map, ctx)


main()