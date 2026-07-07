import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data import load_joined, year_bounds

CHANGE_LABEL = "Change since {year}"
PCT_CHANGE_LABEL = "% change since {year}"


# ---------- 1. Sidebar / controls ----------

def render_sidebar_controls(df, first_year, last_year):
    with st.sidebar:
        year = st.slider("Year", first_year, last_year, last_year)
        counties = st.multiselect("Counties", sorted(df["county_name"].dropna().unique()))
        settlement_types = st.multiselect(
            "Settlement type", sorted(df["settlement_type"].dropna().unique())
        )
        exclude_budapest = st.checkbox("Exclude Budapest", value=False)

        st.divider()
        metric = st.radio(
            "Metric",
            ["Population", CHANGE_LABEL.format(year=first_year), PCT_CHANGE_LABEL.format(year=first_year)],
        )
        encoding = st.radio("Encode as", ["Color", "Size"])
        scale = st.radio("Scale", ["Linear", "Log"])
        classed = st.checkbox(
            "Use class bins (recommended for skewed data)",
            value=True,
            disabled=(encoding == "Size"),  # see note below
        )

    return dict(
        year=year, counties=counties, settlement_types=settlement_types,
        exclude_budapest=exclude_budapest, metric=metric,
        encoding=encoding, scale=scale.lower(), classed=classed,
    )


# ---------- 2. Filters (purely sequential, no interaction with anything else) ----------

def apply_filters(df, year, counties, settlement_types, exclude_budapest):
    view = df[df["year"] == year]
    if counties:
        view = view[view["county_name"].isin(counties)]
    if settlement_types:
        view = view[view["settlement_type"].isin(settlement_types)]
    if exclude_budapest:
        view = view[view["county_name"] != "BUD"]
    return view


# ---------- 3. Metric (raw column to feed everything downstream) ----------

def with_baseline(df, view, first_year):
    base = (
        df[df["year"] == first_year][["settlement_name", "population"]]
        .rename(columns={"population": "base_pop"})
    )
    return view.merge(base, on="settlement_name", how="left")


def compute_metric_column(df, view, metric, first_year):
    if metric == "Population":
        return view, "population"

    view = with_baseline(df, view, first_year)
    if metric == CHANGE_LABEL.format(year=first_year):
        view["change"] = view["population"] - view["base_pop"]
        return view, "change"

    view["pct_change"] = (view["population"] / view["base_pop"] - 1) * 100
    return view, "pct_change"


# ---------- 4. Value prep: scale x classing, fully independent of encoding ----------

def prepare_value_column(view, raw_col, scale="linear", classed=False, n_classes=6):
    """Returns (view, plot_col, meta) where meta describes how to wire it into px."""
    view = view.copy()
    values = view[raw_col]

    if classed:
        bins = pd.qcut(values.rank(method="first"), n_classes, duplicates="drop")
        # rank-based qcut sidesteps ties at the low end (lots of tiny villages share values)
        labels = pd.qcut(values, n_classes, duplicates="drop")
        view["_plot_val"] = labels.astype(str)
        order = labels.cat.categories.astype(str).tolist()
        return view, "_plot_val", {"categorical": True, "order": order}

    if scale == "log":
        shifted = values - min(values.min(), 0) + 1  # handles negative "change" values
        view["_plot_val"] = np.log10(shifted)
        return view, "_plot_val", {"categorical": False, "log": True, "raw_col": raw_col}

    view["_plot_val"] = values
    return view, "_plot_val", {"categorical": False, "log": False, "raw_col": raw_col}


# ---------- 5. Encoding: color vs size, independent of scale/classing ----------

def render_map(view, plot_col, encoding, meta, raw_col):
    common = dict(
        lat="latitude", lon="longitude",
        hover_name="settlement_name",
        hover_data={raw_col: True, "settlement_type": True},
        zoom=6, height=650,
    )

    if encoding == "Color":
        kwargs = {"color": plot_col}
        if meta["categorical"]:
            kwargs["category_orders"] = {plot_col: meta["order"]}
            kwargs["color_discrete_sequence"] = px.colors.sequential.Turbo[::len(px.colors.sequential.Turbo) // len(meta["order"])]
        else:
            kwargs["color_continuous_scale"] = "turbo"
        fig = px.scatter_map(view, **common, **kwargs)

    else:  # Size — size needs continuous non-negative numbers, so categorical bins don't apply
        size_basis = view[raw_col].abs() if meta["categorical"] else view[plot_col].abs()
        fig = px.scatter_map(view, **common, size=size_basis, size_max=30, color_discrete_sequence=["steelblue"])

    fig.update_layout(map_style="carto-positron", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig, width="stretch", theme="streamlit")


# ---------- 6. Composition root ----------

def main():
    st.title("🗺️ Settlement Map")
    df = load_joined()
    first_year, last_year = year_bounds()

    controls = render_sidebar_controls(df, first_year, last_year)

    view = apply_filters(
        df, controls["year"], controls["counties"],
        controls["settlement_types"], controls["exclude_budapest"],
    )
    view, raw_col = compute_metric_column(df, view, controls["metric"], first_year)
    view, plot_col, meta = prepare_value_column(
        view, raw_col, scale=controls["scale"], classed=controls["classed"]
    )
    render_map(view, plot_col, controls["encoding"], meta, raw_col)


main()