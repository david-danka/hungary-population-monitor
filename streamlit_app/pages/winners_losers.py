# streamlit_app/pages/winners_losers.py
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared import get_app_data, warm_cached_properties
from hpm.ui.context import build_change_context, ChangePageContext

# Editorial constants, not exposed to users
DEFAULT_MIN_BASELINE_POP = 200
DEFAULT_N_LEADERBOARD = 15
N_DECLINE_CONTRIBUTION = 50


RELATIVE_CATEGORY_COLORS = {
    "Growing": "#2ca02c",
    "Declining slower than national average": "#f4c542",
    "Declining faster than national average": "#d62728",
}


@st.cache_data()
def get_context(n_decline_contribution: int) -> ChangePageContext:
    app = get_app_data()
    ctx = build_change_context(
        app=app,
        n_largest_losers=n_decline_contribution,
    )
    warm_cached_properties(ctx)
    return ctx


def render_thesis():
    st.title("📊 Winners & Losers")
    st.markdown(
        "The national decline isn't one uniform slide — it's concentrated "
        "in a specific set of places, while others are actually growing. "
        "This page names them."
    )


def render_decline_contribution(ctx: ChangePageContext):
    pct = ctx.decline_contribution
    st.info(
        f"📌 The **{N_DECLINE_CONTRIBUTION} settlements** with the steepest population losses "
        f"account for **{pct:.1f}%** of all population lost across every "
        f"shrinking settlement in the dataset."
        f"{ctx.direction_counts}"
    )


def render_growth_decline_summary_0(ctx):
    counts = ctx.direction_counts
    c1, c2 = st.columns(2)
    c1.metric("📈 Settlements grew", counts["Growth"])
    c2.metric("📉 Settlements declined", counts["Decline"])

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
        line_color="black",
    )
    fig.update_layout(
        barmode="relative",
        title="Growth, decline, and the net — by year",
        height=400,
    )
    st.plotly_chart(fig, width="stretch")


def render_growth_decline_summary(ctx):
    counts = ctx.direction_counts
    c1, c2 = st.columns(2)
    c1.metric("📈 Settlements grew", counts["Growth"])
    c2.metric("📉 Settlements declined", counts["Decline"])

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


def render_leaderboard(ctx: ChangePageContext):
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


def render_map_2(ctx: ChangePageContext):
    st.subheader("Map: performance relative to the national trend")
    st.caption(
        f"National change over this period: {ctx.national_pct_change:.1f}%. "
        "Settlements are colored by how they compare to that baseline, not "
        "raw magnitude — so a village losing population slower than the "
        "national average still reads as 'doing OK'."
    )

    view = ctx.change_with_category
    fig = px.scatter_map(
        view,
        lat="latitude",
        lon="longitude",
        size=np.sqrt(view["population_last"]),
        size_max=30,
        color="relative_category",
        color_discrete_map=RELATIVE_CATEGORY_COLORS,
        hover_name="settlement_name",
        hover_data={"pct_change": ":.1f", "abs_change": ":,.0f"},
        zoom=6,
        height=650,
        title=f"Settlement performance, {ctx.app.first_year} → {ctx.app.last_year}",
    )
    fig.update_layout(
        map_style="carto-positron", margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def render_map(ctx: ChangePageContext):
    change = ctx.change
    metric = st.radio(
        "Rank by",
        ["Absolute change", "Percent change"],
        horizontal=True,
        key=1,
    )
    change_type = "abs_change" if metric == "Absolute change" else "pct_change"
    lo, hi = (
        int(change["population_first"].min()),
        int(change["population_first"].max()),
    )
    pop_range = st.slider(
        "Population range (baseline year)",
        lo,
        hi,
        (lo, hi),
        help="Narrow this to exclude a few huge cities that otherwise dominate the map's scale.",
    )
    view = change[change["population_first"].between(*pop_range)]

    fig = px.scatter_map(
        view,
        lat="latitude",
        lon="longitude",
        size=np.sqrt(view["population_last"]),
        size_max=30,
        color=change_type,
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        hover_name="settlement_name",
        hover_data={"pct_change": ":.1f", "abs_change": ":,.0f"},
        zoom=6,
        height=650,
        title=f"Population change by settlement, {ctx.app.first_year} → {ctx.app.last_year}",
    )
    fig.update_layout(
        map_style="carto-positron", margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    st.plotly_chart(fig, width="stretch", theme="streamlit")


def main():
    st.set_page_config(page_title="Winners & Losers", layout="wide")

    ctx = get_context(
        n_decline_contribution=N_DECLINE_CONTRIBUTION,
    )

    render_thesis()
    render_decline_contribution(ctx)
    st.divider()
    render_growth_decline_summary(ctx)
    render_growth_decline_summary_0(ctx)
    st.divider()
    render_leaderboard(ctx)
    st.divider()
    render_map(ctx)
    render_map_2(ctx)


main()
