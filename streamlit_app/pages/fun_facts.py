from collections import defaultdict
from dataclasses import dataclass

import pandas as pd
import streamlit as st
from utils.data import load_joined, year_bounds


@dataclass(slots=True)
class FunFacts:
    appeared: pd.Series
    disappeared: pd.Series
    county_changes: pd.DataFrame
    type_changes: pd.DataFrame
    history: dict[int, dict]
    latest_ratio: pd.Series
    before: pd.Series
    after: pd.Series


def find_attribute_changes(df, attr_col):
    """Settlements where `attr_col` (e.g. county_name, settlement_type) changed
    between any two consecutive years they appear in."""
    sub = (
        df[["settlement_name", "year", attr_col]]
        .dropna()
        .sort_values(["settlement_name", "year"])
    )
    sub["prev_val"] = sub.groupby("settlement_name")[attr_col].shift(1)
    sub["prev_year"] = sub.groupby("settlement_name")["year"].shift(1)
    changes = sub[sub[attr_col] != sub["prev_val"]].dropna(subset=["prev_val"])
    return changes.rename(columns={attr_col: "new_val"})[
        ["settlement_name", "prev_year", "year", "prev_val", "new_val"]
    ]


def find_appearance_events(df):
    """Settlements that appear partway through the series (newly independent)
    or disappear partway through (merged/absorbed)."""
    first_seen = df.groupby("settlement_name")["year"].min()
    last_seen = df.groupby("settlement_name")["year"].max()
    first_year, last_year = df["year"].min(), df["year"].max()

    appeared = first_seen[first_seen > first_year]
    disappeared = last_seen[last_seen < last_year]
    return appeared, disappeared


def least_populated(df, year=None):
    """Single least-populated settlement, either for one year or the lowest ever recorded."""
    sub = df if year is None else df[df["year"] == year]
    row = sub.loc[sub["population"].idxmin()]
    return row[["settlement_name", "year", "population"]]


def most_skewed_gender_ratio(
    df,
    year,
    male_col="male_population",
    female_col="female_population",
    min_pop=200,
):
    sub = df[(df["year"] == year) & (df["population"] >= min_pop)].copy()
    sub["ratio"] = sub[male_col] / sub[female_col]
    return sub.loc[sub["ratio"].sub(1).abs().idxmax()][
        ["settlement_name", male_col, female_col, "ratio"]
    ]


def prepare_fun_facts(df, first_year, last_year):
    appeared, disappeared = find_appearance_events(df)
    county_changes = find_attribute_changes(df, "county_name")
    type_changes = find_attribute_changes(df, "settlement_type")

    return FunFacts(
        appeared=appeared,
        disappeared=disappeared,
        county_changes=county_changes,
        type_changes=type_changes,
        history=build_history(appeared, county_changes, type_changes),
        latest_ratio=most_skewed_gender_ratio(df, last_year),
        before=least_populated(df, first_year),
        after=least_populated(df, last_year),
    )


def render_summary_metrics(facts: FunFacts):
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "🆕 New settlements",
        len(facts.appeared),
    )

    c2.metric(
        "🏛 County changes",
        len(facts.county_changes),
    )

    c3.metric(
        "🏘 Type changes",
        len(facts.type_changes),
    )

    c4.metric(
        "🤝 Merged",
        len(facts.disappeared),
    )

    st.divider()


def render_new_settlement_card(appeared):
    if not appeared.empty:
        settlement = appeared.index[0]
        year = appeared.iloc[0]

        with st.container(border=True):
            st.markdown("### 🆕 New settlement")
            st.markdown(f"**{settlement}**")
            st.caption(f"Became independent in **{year}**.")


def render_county_change_card(county_changes):
    if not county_changes.empty:
        row = county_changes.iloc[0]

        with st.container(border=True):
            st.markdown("### 🏛 County reassignment")

            st.markdown(
                f"""
**{row.settlement_name}**

{row.prev_val}
⬇️
{row.new_val}

({int(row.year)})
                """
            )


def render_gender_ratio_card(latest_ratio):
    with st.container(border=True):
        st.markdown("### 👥 Largest gender imbalance")

        st.metric(
            latest_ratio["settlement_name"],
            f"{latest_ratio['ratio']:.2f}",
            help="Male/Female ratio",
        )

        st.caption(
            f"{latest_ratio['male_population']:,} men\n\n"
            f"{latest_ratio['female_population']:,} women"
        )


def render_smallest_settlement_card(facts: FunFacts, first_year, last_year):
    with st.container(border=True):
        st.markdown("### 📉 Smallest settlement")

        c1, c2 = st.columns(2)

        c1.metric(
            str(first_year),
            facts.before["population"],
            facts.before["settlement_name"],
        )

        c2.metric(
            str(last_year),
            facts.after["population"],
            facts.after["settlement_name"],
        )


def render_highlights(facts: FunFacts, first_year, last_year):
    st.subheader("⭐ Highlights")

    left, right = st.columns(2)

    with left:
        render_new_settlement_card(facts.appeared)
        render_county_change_card(facts.county_changes)

    with right:
        render_gender_ratio_card(facts.latest_ratio)
        render_smallest_settlement_card(
            facts, first_year, last_year
        )
    st.divider()


def render_badges(names):
    badge_html = "".join(
        f"""
        <span style="
            display:inline-block;
            padding:4px 10px;
            margin:4px;
            border-radius:999px;
            background:#efefef;
            font-size:0.9rem;
        ">
            {name}
        </span>
        """
        for name in sorted(names)
    )

    st.markdown(
        badge_html,
        unsafe_allow_html=True,
    )


def build_history(appeared, county_changes, type_changes):
    years = defaultdict(
        lambda: {
            "new": [],
            "county": [],
            "types": [],
        }
    )

    for settlement, year in appeared.items():
        years[int(year)]["new"].append(settlement)

    for _, row in county_changes.iterrows():
        years[int(row.year)]["county"].append(row)

    for _, row in type_changes.iterrows():
        years[int(row.year)]["types"].append(row)

    return dict(sorted(years.items(), reverse=True))


# ============================================================================
# History renderers
# ============================================================================


def render_history(history):
    st.subheader("📅 Years of Change")

    for year, data in history.items():
        render_history_year(year, data)


def render_history_year(year, data):
    total = len(data["new"]) + len(data["county"]) + len(data["types"])

    with st.container(border=True):
        st.markdown(f"## {year}")
        render_year_summary(total, data)

        with st.expander(f"Show {total} event{'s' if total != 1 else ''}"):
            render_new_events(data["new"])
            render_county_events(data["county"])
            render_type_events(data["types"])


def render_year_summary(total, data):
    if total == 1:
        st.caption("1 recorded change")
    else:
        st.caption(f"{total} recorded changes")

    c1, c2, c3 = st.columns(3)

    c1.metric("🆕 New", len(data["new"]))
    c2.metric("🏛 County", len(data["county"]))
    c3.metric("🏘 Type", len(data["types"]))

    if total >= 10:
        st.success(f"🔥 Major administrative update ({total} changes)")
    elif total >= 5:
        st.info(f"📈 Busy year ({total} changes)")
    else:
        st.caption("Minor update")


# ============================================================================
# Event sections
# ============================================================================


def render_new_events(events):
    if not events:
        return

    st.markdown("### 🆕 New settlements")

    for settlement in sorted(events):
        st.markdown(f"- **{settlement}** became independent")


def render_county_events(events):
    if not events:
        return

    st.markdown("### 🏛 County reassignments")

    for row in events:
        st.markdown(
            f"- **{row.settlement_name}** {row.prev_val} → {row.new_val}"
        )


def render_type_events(events):
    if not events:
        return

    st.markdown("### 🏘 Settlement reclassifications")

    for (old, new), names in group_type_changes(events).items():
        st.markdown(
            f"**{len(names)} settlement{'s' if len(names) != 1 else ''}** "
            f"changed from **{old} → {new}**"
        )

        render_badges(names)


# ============================================================================
# Helpers
# ============================================================================


def group_type_changes(events):
    grouped = defaultdict(list)

    for row in events:
        grouped[(row.prev_val, row.new_val)].append(row.settlement_name)

    return grouped


def main():
    st.title("🔎 Fun Facts")
    df = load_joined()
    first_year, last_year = year_bounds()

    facts = prepare_fun_facts(df, first_year, last_year)

    render_summary_metrics(facts)
    render_highlights(facts, first_year, last_year)
    render_history(facts.history)


main()
