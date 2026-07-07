import plotly.express as px
import streamlit as st

from utils.data import load_joined, year_bounds

st.title("🔎 Settlement Explorer")

df = load_joined()
first_year, last_year = year_bounds()
real = df

st.subheader("Look up a settlement")
# Settlement name alone isn't unique -- label with county to disambiguate.
options = (
    real[["settlement_name", "county_name"]]
    .drop_duplicates()
    .assign(
        label=lambda d: d["settlement_name"]
        + " ("
        + d["county_name"].fillna("?")
        + ")"
    )
    .sort_values("label")
)
choice = st.selectbox("Settlement", options["label"])
code = options.loc[options["label"] == choice, "settlement_name"].iloc[0]

series = real[real["settlement_name"] == code].sort_values("year")
st.plotly_chart(
    px.line(
        series,
        x="year",
        y=["male_population", "female_population", "population"],
    ),
    width="stretch",
)

st.divider()
st.subheader(f"Growth & decline leaderboard, {first_year} → {last_year}")

min_pop = st.slider("Minimum baseline population", 0, 5000, 200, step=50)
first_pop = real[real["year"] == first_year][["settlement_name", "population"]]
last_pop = real[real["year"] == last_year][["settlement_name", "population"]]
change = first_pop.merge(
    last_pop, on="settlement_name", suffixes=("_first", "_last")
)
change = change[change["population_first"] >= min_pop]
change["pct_change"] = (
    change["population_last"] / change["population_first"] - 1
) * 100

col1, col2 = st.columns(2)
with col1:
    st.write("**Fastest shrinking**")
    st.dataframe(
        change.nsmallest(15, "pct_change")[["settlement_name", "pct_change"]],
        hide_index=True,
    )
with col2:
    st.write("**Fastest growing**")
    st.dataframe(
        change.nlargest(15, "pct_change")[["settlement_name", "pct_change"]],
        hide_index=True,
    )
