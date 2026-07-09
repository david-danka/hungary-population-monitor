from shared import get_app_data, warm_cached_properties
from hpm.analysis.facts import group_type_changes
from hpm.ui.context import build_facts_context, FactsPageContext

import streamlit as st

MIN_POP_FOR_GENDER_RATIO = 0


@st.cache_data()
def get_context(min_pop_for_gender_ratio: int) -> FactsPageContext:
    app = get_app_data()
    ctx = build_facts_context(
        app=app, min_pop_for_gender_ratio=min_pop_for_gender_ratio
    )
    warm_cached_properties(ctx)
    return ctx


def render_summary_metrics(ctx: FactsPageContext):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🆕 New settlements", len(ctx.appeared))
    c2.metric("🏛 County changes", len(ctx.county_changes))
    c3.metric("🏘 Type changes", len(ctx.type_changes))
    c4.metric("🤝 Merged", len(ctx.disappeared))
    st.divider()


def render_new_settlement_card(ctx: FactsPageContext):
    newest = ctx.newest_settlement
    if newest is None:
        return
    settlement, year = newest
    with st.container(border=True):
        st.markdown("### 🆕 Newest settlement")
        st.markdown(f"**{settlement}**")
        st.caption(f"Became independent in **{year}**.")


def render_county_change_card(ctx: FactsPageContext):
    row = ctx.latest_county_change
    if row is None:
        return
    with st.container(border=True):
        st.markdown("### 🏛 Most recent county reassignment")
        st.markdown(
            f"**{row.settlement_name}**\n\n{row.prev_val}\n⬇️\n{row.new_val}\n\n({int(row.year)})"
        )


# page.py
def render_gender_ratio_card(ctx: FactsPageContext):
    with st.container(border=True):
        st.markdown("### 👥 Largest gender imbalances")
        col1, col2 = st.columns(2)

        with col1:
            m = ctx.most_male_skewed_settlement
            st.metric(
                m["settlement_name"],
                f"{m['ratio']:.2f}",
                help="Male/Female ratio — most male-skewed",
            )
            st.caption(
                f"{m['male_population']:,} men, {m['female_population']:,} women"
            )

        with col2:
            f = ctx.most_female_skewed_settlement
            st.metric(
                f["settlement_name"],
                f"{f['ratio']:.2f}",
                help="Male/Female ratio — most female-skewed",
            )
            st.caption(
                f"{f['male_population']:,} men, {f['female_population']:,} women"
            )


def render_smallest_settlement_card(ctx: FactsPageContext):
    with st.container(border=True):
        st.markdown("### 📉 Smallest settlement")
        c1, c2 = st.columns(2)
        first = ctx.smallest_settlement_first_year
        last = ctx.smallest_settlement_last_year
        c1.caption(first["settlement_name"])
        c1.metric(
            str(ctx.app.first_year),
            first["population"],
        )
        c2.caption(last["settlement_name"])
        c2.metric(
            str(ctx.app.last_year),
            last["population"],
        )


def render_highlights(ctx: FactsPageContext):
    st.subheader("⭐ Highlights")
    left, right = st.columns(2)
    with left:
        render_new_settlement_card(ctx)
        render_county_change_card(ctx)
    with right:
        render_gender_ratio_card(ctx)
        render_smallest_settlement_card(ctx)
    st.divider()


def render_badges(names):
    badge_html = "".join(
        f'<span style="display:inline-block;padding:4px 10px;margin:4px;'
        f'border-radius:999px;background:#efefef;font-size:0.9rem;">{name}</span>'
        for name in sorted(names)
    )
    st.markdown(badge_html, unsafe_allow_html=True)


def render_history(ctx: FactsPageContext):
    st.subheader("📅 Years of Change")
    for year, data in ctx.history.items():
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
    st.caption(
        "1 recorded change" if total == 1 else f"{total} recorded changes"
    )
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
            f"**{len(names)} settlement{'s' if len(names) != 1 else ''}** changed from **{old} → {new}**"
        )
        render_badges(names)


def main():
    st.set_page_config(page_title="Fun Facts", layout="wide")
    ctx = get_context(
        min_pop_for_gender_ratio=MIN_POP_FOR_GENDER_RATIO,
    )

    st.title("🔎 Fun Facts")
    render_summary_metrics(ctx)
    render_highlights(ctx)
    render_history(ctx)


main()
