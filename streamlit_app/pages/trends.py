import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data import load_joined

# ===================================================
# DATA BUILDERS
# ===================================================

def compute_county_trend(df):
    return df.groupby(["county_name", "year"], as_index=False)["population"].sum()


def compute_type_trend(df):
    return df.groupby(["settlement_type", "year"], as_index=False)["population"].sum()


def index_to_first_year(view, group_col):
    view = view.copy()

    first_vals = (
        view.sort_values("year")
        .groupby(group_col)["population"]
        .first()
    )

    view["indexed"] = view.apply(
        lambda r: r["population"] / first_vals[r[group_col]] * 100,
        axis=1
    )

    return view


def compute_top_share(df, top_n):
    latest_year = df["year"].max()

    top_settlements = (
        df[df["year"] == latest_year]
        .groupby("settlement_name", as_index=False)["population"]
        .sum()
        .nlargest(top_n, "population")["settlement_name"]
    )

    top_df = df[df["settlement_name"].isin(top_settlements)]

    top_trend = top_df.groupby("year", as_index=False)["population"].sum()
    total_trend = df.groupby("year", as_index=False)["population"].sum()

    merged = top_trend.merge(total_trend, on="year", suffixes=("_top", "_total"))
    merged["share"] = merged["population_top"] / merged["population_total"] * 100

    return merged


# ===================================================
# RENDERERS
# ===================================================

def render_county_trends(view, indexed):
    st.subheader("County population over time")

    if indexed:
        view = index_to_first_year(view, "county_name")
        y_col = "indexed"
    else:
        y_col = "population"

    st.plotly_chart(
        px.line(view, x="year", y=y_col, color="county_name"),
        width="stretch"
    )


def render_type_trends(df, indexed):
    st.subheader("Settlement type trajectories")

    view = compute_type_trend(df)

    if indexed:
        view = index_to_first_year(view, "settlement_type")
        y_col = "indexed"
    else:
        y_col = "population"

    st.plotly_chart(
        px.line(view, x="year", y=y_col, color="settlement_type"),
        width="stretch"
    )


def render_top_share(df, top_n):
    st.subheader(f"Share of population in top {top_n} settlements")

    merged = compute_top_share(df, top_n)

    st.plotly_chart(
        px.line(merged, x="year", y="share", markers=True),
        width="stretch"
    )


# ===================================================
# UI
# ===================================================

def render_controls(df):
    counties = st.multiselect(
        "Counties",
        sorted(df["county_name"].unique()),
        default=["Budapest"] if "Budapest" in df["county_name"].values else None
    )

    indexed = st.checkbox("Index to first year = 100", value=True)
    top_n = st.slider("Top N settlements", 5, 20, 10)

    return counties, indexed, top_n


def filter_df(df, counties):
    if not counties:
        return df
    return df[df["county_name"].isin(counties)]


# ===================================================
# MAIN
# ===================================================

def main():
    st.title("📈 Trends")

    df = load_joined()

    counties, indexed, top_n = render_controls(df)
    df = filter_df(df, counties)

    county_view = compute_county_trend(df)

    st.divider()
    render_county_trends(county_view, indexed)

    st.divider()
    render_type_trends(df, indexed)

    st.divider()
    render_top_share(df, top_n)


main()