"""
GTSS Pakistan — Tobacco Survey Dashboard
KPI Scorecard — Southampton-style scorecard (indicator, sparkline, RAG status,
trend arrow) built entirely from our own GATS 2014 vs 2024 comparison data.

Honesty note: we only have TWO survey years (2014, 2024) for these
indicators — not an annual series — so sparklines are 2-point trend lines,
and "status" is judged against the indicator's own 2014 value (there is no
separate national benchmark to compare Pakistan against, since this *is*
the national data).
"""

import re

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_comparison
from utils.theme import (
    apply_theme, kpi_row, page_footer, filter_header, filter_status, count_active,
    inject_responsive_css,
)

st.set_page_config(page_title="GTSS Pakistan | KPI Scorecard", page_icon="📋", layout="wide")
inject_responsive_css()

THEME = apply_theme("scorecard")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

GREEN, AMBER, RED, GREY = "#2E7D32", "#E9A400", "#C0392B", "#8895A7"

st.title("📋 KPI Scorecard — GATS 2014 vs 2024")
st.caption(
    "Scorecard-style view of the adult tobacco indicators that have both a 2014 and a 2024 "
    f"value. Theme: {THEME['name']}"
)

# ---------------------------------------------------------------------------
# CATEGORIZE + DIRECTION (what counts as "better") FOR EACH INDICATOR
# ---------------------------------------------------------------------------
CATEGORY_MAP = {
    "Current tobacco use": "Tobacco Use",
    "Current tobacco smoking": "Tobacco Use",
    "Avg cigarettes/day (daily smokers)": "Tobacco Use",
    "SHS exposure: Home": "Secondhand Smoke",
    "SHS exposure: Workplace": "Secondhand Smoke",
    "SHS exposure: Government buildings": "Secondhand Smoke",
    "SHS exposure: Private buildings": "Secondhand Smoke",
    "SHS exposure: Healthcare facilities": "Secondhand Smoke",
    "SHS exposure: Restaurants": "Secondhand Smoke",
    "SHS exposure: Marriage halls": "Secondhand Smoke",
    "SHS exposure: Public transportation": "Secondhand Smoke",
    "SHS exposure: Universities": "Secondhand Smoke",
    "SHS exposure: Schools": "Secondhand Smoke",
    "Quit attempt (past 12 months)": "Cessation & Advice",
    "Advised to quit by healthcare provider": "Cessation & Advice",
    "Considered quitting due to warnings": "Cessation & Advice",
    "Noticed health warnings on packages": "Packaging & Marketing",
    "Noticed tobacco ads/promos in stores": "Packaging & Marketing",
    "Noticed any tobacco ads/promos/sponsorships": "Packaging & Marketing",
    "Avg cost of 20 manufactured cigarettes (PKR, inflation-adj.)": "Cost & Affordability",
    "Avg monthly cigarette expenditure (PKR, inflation-adj.)": "Cost & Affordability",
}

# "decrease" = lower 2024 value is the good outcome, "increase" = higher is good,
# "neutral" = price/spend figures where we won't editorialize a judgement.
DIRECTION_MAP = {
    "Current tobacco use": "decrease",
    "Current tobacco smoking": "decrease",
    "Avg cigarettes/day (daily smokers)": "decrease",
    "SHS exposure: Home": "decrease",
    "SHS exposure: Workplace": "decrease",
    "SHS exposure: Government buildings": "decrease",
    "SHS exposure: Private buildings": "decrease",
    "SHS exposure: Healthcare facilities": "decrease",
    "SHS exposure: Restaurants": "decrease",
    "SHS exposure: Marriage halls": "decrease",
    "SHS exposure: Public transportation": "decrease",
    "SHS exposure: Universities": "decrease",
    "SHS exposure: Schools": "decrease",
    "Quit attempt (past 12 months)": "increase",
    "Advised to quit by healthcare provider": "increase",
    "Considered quitting due to warnings": "increase",
    "Noticed health warnings on packages": "increase",
    "Noticed tobacco ads/promos in stores": "decrease",
    "Noticed any tobacco ads/promos/sponsorships": "decrease",
    "Avg cost of 20 manufactured cigarettes (PKR, inflation-adj.)": "neutral",
    "Avg monthly cigarette expenditure (PKR, inflation-adj.)": "neutral",
}

UNIT_MAP = {
    "Avg cigarettes/day (daily smokers)": "cigs/day",
    "Avg cost of 20 manufactured cigarettes (PKR, inflation-adj.)": "PKR",
    "Avg monthly cigarette expenditure (PKR, inflation-adj.)": "PKR",
}

# ---------------------------------------------------------------------------
# LOAD + BUILD SCORECARD (Overall group covers all 21 indicators)
# ---------------------------------------------------------------------------
df_cmp = load_comparison()
overall = df_cmp[df_cmp["Group"].str.strip().str.lower() == "overall"].copy()
overall["Category"] = overall["Indicator"].map(CATEGORY_MAP).fillna("Other")
overall["Direction"] = overall["Indicator"].map(DIRECTION_MAP).fillna("neutral")
overall["Unit"] = overall["Indicator"].map(UNIT_MAP).fillna("%")
overall["Delta"] = (overall["2024 Value"] - overall["2014 Value"]).round(2)

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()
search = st.sidebar.text_input("Search indicator name")
cat_opts = sorted(overall["Category"].unique().tolist())
cat_sel = st.sidebar.multiselect("Category", cat_opts, default=cat_opts)

filtered = overall[overall["Category"].isin(cat_sel)]
if search:
    filtered = filtered[filtered["Indicator"].str.contains(search, case=False, na=False)]

n_active_filters = count_active(bool(search), sorted(cat_sel) != sorted(cat_opts))


def rag_status(row):
    if row["Direction"] == "neutral":
        return "Context", GREY
    scale = max(abs(row["2014 Value"]), abs(row["2024 Value"]), 1)
    rel_change = abs(row["Delta"]) / scale
    if rel_change < 0.02:
        return "Similar", AMBER
    good_sign = -1 if row["Direction"] == "decrease" else 1
    if row["Delta"] * good_sign > 0:
        return "Better", GREEN
    return "Worse", RED


filtered[["Status", "StatusColor"]] = filtered.apply(
    lambda r: pd.Series(rag_status(r)), axis=1
)
filtered["Arrow"] = filtered["Delta"].apply(lambda d: "▲" if d > 0 else ("▼" if d < 0 else "▶"))

filter_status(len(overall), len(filtered), n_active_filters, noun="indicators")

# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY — states the overall scorecard result in one sentence
# before the detailed table. Computed live from the filtered rows above.
# ---------------------------------------------------------------------------
judged = filtered[filtered["Status"] != "Context"]
n_better, n_worse = int((judged["Status"] == "Better").sum()), int((judged["Status"] == "Worse").sum())
if len(judged):
    judged = judged.copy()
    judged["Scale"] = judged[["2014 Value", "2024 Value"]].abs().max(axis=1).clip(lower=1)
    judged["RelChange"] = judged["Delta"].abs() / judged["Scale"]
    worst = judged[judged["Status"] == "Worse"].sort_values("RelChange", ascending=False)
    worst_note = f" The biggest concern: **{worst.iloc[0]['Indicator']}**." if len(worst) else ""
    st.markdown(
        f"""
        <div style="
            background:rgba(46,125,50,0.08);
            border-left:4px solid {THEME['primary']};
            border-radius:8px;
            padding:0.9rem 1.1rem;
            margin-bottom:1rem;
            font-size:1.0rem;
            line-height:1.5;
        ">
            Of <b>{len(judged)}</b> indicators judged, <b>{n_better} improved</b> and
            <b>{n_worse} got worse</b> since 2014.{worst_note}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# SUMMARY ROW
# ---------------------------------------------------------------------------
kpi_row(
    [
        {"label": "Indicators shown", "value": f"{len(filtered)}"},
        {"label": "🟢 Better", "value": f"{(filtered['Status'] == 'Better').sum()}"},
        {"label": "🟡 Similar", "value": f"{(filtered['Status'] == 'Similar').sum()}"},
        {"label": "🔴 Worse", "value": f"{(filtered['Status'] == 'Worse').sum()}"},
    ],
    accent=ACCENT,
)

st.divider()


# ---------------------------------------------------------------------------
# SPARKLINE (2-point line — that's the honest shape of our data: only two
# survey years exist, 2014 and 2024, not an annual series)
# ---------------------------------------------------------------------------
def sparkline_svg(v1: float, v2: float, color: str, width: int = 70, height: int = 26) -> str:
    lo, hi = min(v1, v2), max(v1, v2)
    rng = (hi - lo) or 1
    pad = 5

    def y(v):
        return height - pad - ((v - lo) / rng) * (height - 2 * pad)

    x1, x2 = pad, width - pad
    y1, y2 = y(v1), y(v2)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<line x1="{x1}" y1="{y1:.1f}" x2="{x2}" y2="{y2:.1f}" stroke="{color}" stroke-width="2"/>'
        f'<circle cx="{x1}" cy="{y1:.1f}" r="2.6" fill="{color}"/>'
        f'<circle cx="{x2}" cy="{y2:.1f}" r="2.6" fill="{color}"/>'
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# SCORECARD TABLE (custom HTML — gives full control over sparkline + RAG dot,
# which a native st.dataframe can't render inline)
# ---------------------------------------------------------------------------
st.subheader("Scorecard")

rows_html = ""
for _, r in filtered.sort_values("Category").iterrows():
    spark = sparkline_svg(r["2014 Value"], r["2024 Value"], r["StatusColor"])
    rows_html += f"""
    <tr>
        <td style="padding:10px 12px; border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600; color:#1f2937;">{r['Indicator']}</div>
            <div style="font-size:0.75rem; color:#6b7280;">{r['Category']}</div>
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['2014 Value']:.1f} {r['Unit']}
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['2024 Value']:.1f} {r['Unit']}
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb;">
            {spark}
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['Delta']:+.1f} {r['Unit']}
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb;">
            <span style="display:inline-block; width:12px; height:12px; border-radius:50%; background:{r['StatusColor']};"></span>
            <span style="font-size:0.8rem; color:#374151; margin-left:4px;">{r['Status']}</span>
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; font-size:1.05rem; color:{r['StatusColor']};">
            {r['Arrow']}
        </td>
    </tr>
    """

table_html = f"""
<div class="scroll-table-wrap" style="max-height:640px; overflow-y:auto; border:1px solid #e5e7eb; border-radius:8px;">
<table style="width:100%; min-width:640px; border-collapse:collapse; font-size:0.9rem;">
    <thead style="position:sticky; top:0; background:{THEME['primary']}; color:white; z-index:1;">
        <tr>
            <th style="padding:10px 12px; text-align:left;">Indicator</th>
            <th style="padding:10px 12px;">2014</th>
            <th style="padding:10px 12px;">2024</th>
            <th style="padding:10px 12px;">Trend</th>
            <th style="padding:10px 12px;">Change</th>
            <th style="padding:10px 12px;">Status</th>
            <th style="padding:10px 12px;">Direction</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>
</div>
"""

st.markdown(re.sub(r"^[ \t]+", "", table_html, flags=re.MULTILINE), unsafe_allow_html=True)

st.caption(
    "**Status** compares the 2024 value to 2014 for that same indicator (🟢 moved in the healthy "
    "direction, 🟡 changed less than ~2%, 🔴 moved the wrong way). ⚪ Context = cost/spending "
    "figures, shown without a judgement call. **Direction** is the raw trend arrow (▲ up / ▼ down), "
    "independent of whether that's good or bad for that indicator."
)

st.divider()

# ---------------------------------------------------------------------------
# GENDER BREAKDOWN — the only two indicators where Male/Female rows exist
# ---------------------------------------------------------------------------
gendered = df_cmp[df_cmp["Group"].isin(["Male", "Female"])]
if not gendered.empty:
    st.subheader("Male vs Female — where gender breakdowns exist")
    st.caption(
        "Only 2 of the 21 indicators were published with a Male/Female split in our source data — "
        "shown here rather than faked for the rest."
    )
    melted = gendered.melt(
        id_vars=["Indicator", "Group"],
        value_vars=["2014 Value", "2024 Value"],
        var_name="Year",
        value_name="Value",
    )
    melted["Year"] = melted["Year"].str.replace(" Value", "", regex=False)
    fig = px.bar(
        melted,
        x="Indicator",
        y="Value",
        color="Group",
        facet_col="Year",
        barmode="group",
        color_discrete_sequence=[COLORWAY[0], COLORWAY[3]],
        text_auto=".1f",
    )
    fig.update_layout(showlegend=True, legend_title="")
    st.plotly_chart(fig, use_container_width=True)

page_footer("Scorecard built from the GATS 2014 vs 2024 comparison dataset")
