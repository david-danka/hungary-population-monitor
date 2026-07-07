from collections.abc import Callable

import pandas as pd
import plotly.express as px
import streamlit as st

from hpm.ui.context import load_overview_context, OverviewPageContext
from hpm.ui.selectors import read_overview_params, OverviewParams


@st.cache_data()
def get_context(params: OverviewParams) -> OverviewPageContext:
    return load_overview_context(params)


def render_headline_metrics(ctx: OverviewPageContext) -> None:
    m = ctx.metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label=f"Population ({ctx.last_year})",
        value=m.latest,
        delta=m.change,
        format="%,.0f",
    )

    col2.metric(
        label=f"Change since {ctx.first_year}",
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


def render_national_trend(ctx: OverviewPageContext):
    st.plotly_chart(
        px.line(
            ctx.national_trend,
            x="year",
            y="population",
            title="National population over time",
        ),
        width="stretch",
    )


def render_map(ctx: OverviewPageContext):
    fig = px.scatter_map(ctx.df)
    """
    fig = px.scatter_map(view, **common, size=size_basis, size_max=30, color_discrete_sequence=["steelblue"])

    fig.update_layout(map_style="carto-positron", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, width="stretch", theme="streamlit")
    """

def render_county_ranking(ctx: OverviewPageContext):
    fig = px.bar(
        ctx.county_population,
        x="population",
        y="county_name",
        orientation="h",
        title="County population (ranked)",
    )
    fig.update_layout(
        yaxis=dict(dtick=1, automargin=True),
        height=25 * len(ctx.county_population),
        margin=dict(l=150, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, width="stretch")


def render_settlement_mix(ctx: OverviewPageContext):
    fig = px.treemap(
        ctx.settlement_type_mix,
        path=[px.Constant("Hungary"), "settlement_type"],
        values="population",
        title=f"Population by settlement type, {ctx.last_year}",
    )
    fig.update_traces(
        root_color="rgba(0,0,0,0)",
        textinfo="label+percent root",
    )
    st.plotly_chart(
        fig,
        width="stretch",
    )


def render_rank_size(ctx: OverviewPageContext):
    fig = px.scatter(
        ctx.settlement_rank,
        x="rank",
        y="population",
        log_x=True,
        log_y=True,
        color="settlement_type",
        hover_name="settlement_name",
        title=f"Rank-size distribution of Hungarian settlements, {ctx.last_year}",
    )
    fig.update_layout(
        xaxis_title="rank (log scale)", yaxis_title="population (log scale)"
    )
    st.plotly_chart(fig, width="stretch")


def render_top_settlements(ctx: OverviewPageContext):
    fig = px.bar(
        ctx.largest_settlements.sort_values(by="population", ascending=True),
        x="population",
        y="settlement_name",
        orientation="h",
        title=f"Largest {ctx.params.top_n_settlements} settlements ({ctx.last_year})",
    )
    st.plotly_chart(fig, width="stretch")


def render_absolutes(ctx: OverviewPageContext):
    ranked = ctx.change_extremes
    gap = pd.DataFrame({
        "settlement_name": ["⋮"],
        "absolute_change": [None],
        "direction": ["gap"],
    })
    combined = pd.concat([ranked.top, gap, ranked.bottom], ignore_index=True)

    fig = px.bar(
        combined,
        x="absolute_change",
        y="settlement_name",
        orientation="h",
        color="direction",
        color_discrete_map={
            "Growth": "#2ca02c",
            "Decline": "#d62728",
            "gap": "rgba(0,0,0,0)",
        },
        title=(
            f"Absolute top {ctx.params.top_bottom_n} winners "
            f"and bottom {ctx.params.top_bottom_n} losers, since {ctx.first_year}"
        ),
    )

    fig.update_layout(
        yaxis=dict(
            categoryorder="array",
            categoryarray=combined["settlement_name"][
                ::-1
            ],  # reverse: top row = first item
            title=None,
        ),
        xaxis_title="Population change",
        showlegend=False,
        margin=dict(l=160, r=20, t=20, b=20),
    )

    st.plotly_chart(fig, width="stretch")


def render_section(
    title: str, fn: Callable[[OverviewPageContext], None], ctx: OverviewPageContext
) -> None:
    st.subheader(title)
    fn(ctx)
    st.divider()


def render_structure(ctx: OverviewPageContext):
    render_settlement_mix(ctx)
    render_rank_size(ctx)


def render_extremes(ctx: OverviewPageContext):
    render_top_settlements(ctx)
    render_absolutes(ctx)


def main():
    st.set_page_config(page_title="Hungary Population Monitor", layout="wide")
    st.title("🇭🇺 Hungary Population Monitor")

    params = read_overview_params()
    ctx = get_context(params)

    render_headline_metrics(ctx)

    st.divider()
    render_section("📈 System dynamics", render_national_trend, ctx)
    render_section("🧭 Geographic structure", render_county_ranking, ctx)
    render_section("📊 Population structure", render_structure, ctx)
    render_section("🔥 Extremes & change", render_extremes, ctx)


main()
