import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from utils.data import load_joined, year_bounds


# =============================================================================
# Data
# =============================================================================


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two points, in kilometers."""
    r = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    )
    return 2 * r * np.arcsin(np.sqrt(a))


def prepare_features():
    df = load_joined()
    first_year, last_year = year_bounds()

    first_df = df[df.year == first_year].copy()
    last_df = df[df.year == last_year].copy()

    # =================================================
    # POPULATION PCT CHANGE
    # =================================================

    feature_df = df[
        [
            "settlement_name",
            "county_name",
            "settlement_type",
            "latitude",
            "longitude",
        ]
    ].drop_duplicates("settlement_name")

    first_df["sex_ratio_start"] = (
        first_df["male_population"] / first_df["female_population"]
    )

    to_drop = [
        "county_name",
        "settlement_type",
        "latitude",
        "longitude",
        "year",
        "male_population",
        "female_population",
    ]

    first_df = first_df.drop(columns=to_drop).rename(
        columns={"population": "pop_start"}
    )

    last_df = last_df.drop(columns=to_drop).rename(
        columns={"population": "pop_end"}
    )

    feature_df = feature_df.merge(first_df, on="settlement_name")
    feature_df = feature_df.merge(last_df, on="settlement_name")

    feature_df["growth_pct"] = (
        feature_df["pop_end"] - feature_df["pop_start"]
    ) / feature_df["pop_start"]

    # =============================================
    # DISTANCE FROM BUDAPEST
    # =============================================

    bp_lat, bp_lon = feature_df[feature_df["settlement_name"] == "Budapest"][
        ["latitude", "longitude"]
    ].iloc[0]

    def dist_from_bp(lat, lon):
        return haversine_km(bp_lat, bp_lon, lat, lon)
    
    feature_df["dist_from_bp"] = haversine_km(
        bp_lat, bp_lon,
        feature_df["latitude"].to_numpy(),
        feature_df["longitude"].to_numpy(),
    )

    feature_df = feature_df.dropna()

    return feature_df


# =============================================================================
# Models
# =============================================================================


def build_preprocessor():
    numeric = [
        "latitude",
        "longitude",
        "sex_ratio_start",
        "pop_start",
        "dist_from_bp",
    ]

    categorical = [
        "county_name",
        "settlement_type",
    ]

    return ColumnTransformer(
        [
            ("num", StandardScaler(), numeric),
            (
                "cat",
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",
                ),
                categorical,
            ),
        ]
    )


def build_pipeline(model):
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            ("model", model),
        ]
    )


def evaluate(model, X_test, y_test):
    pred = model.predict(X_test)

    return {
        "pred": pred,
        "r2": r2_score(y_test, pred),
        "mae": mean_absolute_error(y_test, pred),
        "rmse": root_mean_squared_error(y_test, pred),
    }


def train_models(feature_df):
    X = feature_df.drop(
        columns=[
            "settlement_name",
            "growth_pct",
            "pop_end",
        ]
    )

    y = feature_df["growth_pct"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        random_state=42,
        test_size=0.20,
    )

    lr = build_pipeline(LinearRegression())

    rf = build_pipeline(
        RandomForestRegressor(
            random_state=42,
            n_estimators=100,
            n_jobs=-1,
        )
    )

    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)

    return {
        "X_test": X_test,
        "y_test": y_test,
        "lr": lr,
        "rf": rf,
        "lr_result": evaluate(lr, X_test, y_test),
        "rf_result": evaluate(rf, X_test, y_test),
    }


# =============================================================================
# Feature importance
# =============================================================================


def linear_coefficients(model):
    features = model.named_steps["preprocessor"].get_feature_names_out()

    coef = model.named_steps["model"].coef_

    return pd.DataFrame(
        {
            "feature": features,
            "coefficient": coef,
            "abs": abs(coef),
        }
    ).sort_values("abs", ascending=False)


def random_forest_importance(model):
    features = model.named_steps["preprocessor"].get_feature_names_out()

    importance = model.named_steps["model"].feature_importances_

    return pd.DataFrame(
        {
            "feature": features,
            "importance": importance,
        }
    ).sort_values("importance", ascending=False)


# =============================================================================
# Renderers
# =============================================================================


def render_metrics(lr_result, rf_result):
    st.subheader("📈 Model comparison")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "R²",
        f"{rf_result['r2']:.3f}",
        delta=f"{rf_result['r2'] - lr_result['r2']:.3f}",
    )

    c2.metric(
        "MAE",
        f"{rf_result['mae']:.3f}",
        delta=f"{lr_result['mae'] - rf_result['mae']:.3f}",
        delta_color="inverse",
    )

    c3.metric(
        "RMSE",
        f"{rf_result['rmse']:.3f}",
        delta=f"{lr_result['rmse'] - rf_result['rmse']:.3f}",
        delta_color="inverse",
    )

    st.caption("Random Forest compared against a Linear Regression baseline.")


def render_prediction_plots(y_test, lr_result, rf_result):
    plot_df = pd.DataFrame(
        {
            "Actual": y_test,
            "Linear": lr_result["pred"],
            "Random Forest": rf_result["pred"],
        }
    )

    col1, col2 = st.columns(2)

    for col, label in zip(
        [col1, col2],
        ["Linear", "Random Forest"],
    ):
        with col:
            fig = px.scatter(
                plot_df,
                x="Actual",
                y=label,
                trendline="ols",
                title=label,
            )

            fig.add_shape(
                type="line",
                x0=plot_df.Actual.min(),
                y0=plot_df.Actual.min(),
                x1=plot_df.Actual.max(),
                y1=plot_df.Actual.max(),
            )

            st.plotly_chart(fig, width="stretch")


def render_feature_importance(lr, rf):
    coef = linear_coefficients(lr)

    fig = px.bar(
        coef.head(15).sort_values("abs"),
        x="coefficient",
        y="feature",
        orientation="h",
    )

    st.plotly_chart(fig, width="stretch")

    importance = random_forest_importance(rf)

    fig = px.bar(
        importance.head(15).sort_values("importance"),
        x="importance",
        y="feature",
        orientation="h",
    )

    st.plotly_chart(fig, width="stretch")


def render_largest_errors(feature_df, X_test, y_test, pred):
    errors = X_test.copy()

    errors["actual"] = y_test
    errors["predicted"] = pred

    errors["abs_error"] = (errors.actual - errors.predicted).abs()

    errors = errors.merge(
        feature_df[["settlement_name"]],
        left_index=True,
        right_index=True,
    )

    st.subheader("Largest prediction errors")

    st.dataframe(
        errors.sort_values(
            "abs_error",
            ascending=False,
        )[
            [
                "settlement_name",
                "actual",
                "predicted",
                "abs_error",
            ]
        ].head(20),
        width="stretch",
    )


# =============================================================================
# Main
# =============================================================================


def main():
    st.title("🧠 Population Growth Drivers")

    feature_df = prepare_features()

    results = train_models(feature_df)

    render_metrics(
        results["lr_result"],
        results["rf_result"],
    )

    st.divider()

    render_prediction_plots(
        results["y_test"],
        results["lr_result"],
        results["rf_result"],
    )

    st.divider()

    render_feature_importance(
        results["lr"],
        results["rf"],
    )

    st.divider()

    render_largest_errors(
        feature_df,
        results["X_test"],
        results["y_test"],
        results["rf_result"]["pred"],
    )

main()
