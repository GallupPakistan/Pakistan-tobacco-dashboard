"""
GTSS Pakistan — Tobacco Survey Dashboard
Youth Trend — GYTS 2013 vs 2022 scorecard, built the same way as the adult
KPI Scorecard (indicator, sparkline, RAG status, trend arrow), but for the
youth surveys. Extends the same before/after logic used for adults to
youth, using only genuinely comparable questions across the two surveys.

Honesty note: the 2013 file is pre-aggregated (no row-level youth data
for that year), so every 2013 value here is looked up from published
weighted percentages by matching on the exact survey question / answer
option text — not hardcoded — and the 2022 values come the same way from
the CDC-calculated derived-indicators file. If a source CSV changes, the
numbers on this page change with it.
"""

import re

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_gyts_2013, load_gyts_2022_derived
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, slope_chart, hbar, themed_pie, page_footer,
    filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="GTSS Pakistan | Youth Trend 2013-2022", page_icon="🧒", layout="wide")
inject_responsive_css()

THEME = apply_theme("youth_trend")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

GREEN, AMBER, RED, GREY = "#2E7D32", "#E9A400", "#C0392B", "#8895A7"

st.title("🧒 Youth Trend — GYTS 2013 vs 2022")
st.caption(
    "Scorecard-style view of youth tobacco indicators with a comparable question in both the "
    f"2013 and 2022 GYTS surveys. Theme: {THEME['name']}"
)

df13 = load_gyts_2013()
df22 = load_gyts_2022_derived()


def q2013(question_kw: str, answer_kw: str = None, complement_of_zero: bool = False):
    """Look up a weighted percent from the 2013 aggregated table by matching
    on (part of) the survey question text and, optionally, the answer option."""
    subset = df13[df13["Survey Question"].str.contains(question_kw, case=False, na=False, regex=False)]
    if complement_of_zero:
        zero_row = subset[subset["Answer Option"].str.contains("0 days", case=False, na=False, regex=False)]
        return round(100 - zero_row["Weighted Percent"].iloc[0], 1) if len(zero_row) else None
    if answer_kw:
        row = subset[subset["Answer Option"].str.contains(answer_kw, case=False, na=False, regex=False)]
        return float(row["Weighted Percent"].iloc[0]) if len(row) else None
    return None


def q2022(indicator_kw: str):
    """Look up a weighted percent from the 2022 derived-indicators table."""
    row = df22[df22["Indicator Description"].str.contains(indicator_kw, case=False, na=False, regex=False)]
    return float(row["Weighted Percent"].iloc[0]) if len(row) else None


# ---------------------------------------------------------------------------
# INDICATOR DEFINITIONS — (label, category, direction, 2013 lookup, 2022 lookup)
# direction: "decrease" = lower 2022 value is the healthy outcome,
#            "increase" = higher 2022 value is the healthy outcome
# ---------------------------------------------------------------------------
INDICATORS = [
    ("Ever smoked cigarettes", "Tobacco Use", "decrease",
     q2013("cigarette smoking, even one or two puffs", "Yes"),
     q2022("ever smoked cigarettes")),
    ("Currently smoke cigarettes (past 30 days)", "Tobacco Use", "decrease",
     q2013("how many days did you smoke cigarettes", complement_of_zero=True),
     q2022("currently smoke cigarettes")),
    ("Ever used smokeless tobacco", "Tobacco Use", "decrease",
     q2013("ever tried or experimented with any form of smokeless", "Yes"),
     q2022("ever used any smokeless tobacco products")),
    ("Currently use smokeless tobacco", "Tobacco Use", "decrease",
     q2013("during the past 30 days, did you use any form of smokeless", "Yes"),
     q2022("currently use smokeless tobacco products")),
    ("Secondhand smoke exposure — Home (7 days)", "Secondhand Smoke", "decrease",
     q2013("smoked inside your home", complement_of_zero=True),
     q2022("exposed to tobacco smoke at home in the past 7 days")),
    ("Secondhand smoke exposure — Enclosed public places (7 days)", "Secondhand Smoke", "decrease",
     q2013("enclosed public place, other than your home", complement_of_zero=True),
     q2022("exposed to tobacco smoke in enclosed public places")),
    ("Secondhand smoke exposure — Outdoor public places (7 days)", "Secondhand Smoke", "decrease",
     q2013("anyone smoked in your presence, at any outdoor public place", complement_of_zero=True),
     q2022("exposed to tobacco smoke at outdoor public places")),
    ("Saw smoking on school property (30 days)", "Secondhand Smoke", "decrease",
     q2013("see anyone smoke inside the school building", "Yes"),
     q2022("smoking inside the school building or outside on school property")),
    ("Believe secondhand smoke is harmful (definitely yes)", "Knowledge & Attitudes", "increase",
     q2013("other people's tobacco smoking is harmful", "Definitely yes"),
     q2022("tobacco smoking is harmful to them")),
    ("In favor of banning smoking — enclosed places", "Knowledge & Attitudes", "increase",
     q2013("banning smoking inside enclosed public places", "Yes"),
     q2022("favor of prohibiting smoking in enclosed public places")),
    ("In favor of banning smoking — outdoor places", "Knowledge & Attitudes", "increase",
     q2013("banning smoking at outdoor public places", "Yes"),
     q2022("favor of prohibiting smoking at outdoor public places")),
    ("Saw/heard anti-tobacco media messages (30 days)", "Media & Marketing", "increase",
     q2013("anti-tobacco media messages on television", "Yes"),
     q2022("saw or heard anti-tobacco messages in the media")),
    ("Taught about dangers of tobacco in class (12 months)", "Media & Marketing", "increase",
     q2013("taught in any of your classes about the dangers of tobacco use", "Yes"),
     q2022("taught about the dangers of tobacco use in class")),
    ("Saw tobacco use on TV/videos/movies (30 days)", "Media & Marketing", "decrease",
     q2013("see any people using tobacco when you watched TV", "Yes"),
     q2022("saw someone using tobacco on television, videos, or movies in the past 30 days")),
    ("Had something with a tobacco brand logo", "Media & Marketing", "decrease",
     q2013("with a tobacco product brand logo on it", "Yes"),
     q2022("had something with a tobacco product brand logo on it")),
    ("Offered free tobacco product by company rep", "Media & Marketing", "decrease",
     q2013("offered you a free tobacco product", "Yes"),
     q2022("ever offered a free tobacco product from a tobacco company representative")),
    ("Think peers who smoke have more friends", "Knowledge & Attitudes", "decrease",
     q2013("young people who smoke tobacco have more or less friends", "More friends"),
     q2022("think that young people who smoke have more friends")),
    ("Think peers who smoke look more attractive", "Knowledge & Attitudes", "decrease",
     q2013("makes young people look more or less attractive", "More attractive"),
     q2022("think that young people who smoke are more attractive")),
]

rows = []
for label, category, direction, v13, v22 in INDICATORS:
    if v13 is None or v22 is None:
        continue
    rows.append({
        "Indicator": label, "Category": category, "Direction": direction,
        "2013 Value": round(v13, 1), "2022 Value": round(v22, 1),
        "Delta": round(v22 - v13, 2),
    })

overall = pd.DataFrame(rows)

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
    scale = max(abs(row["2013 Value"]), abs(row["2022 Value"]), 1)
    rel_change = abs(row["Delta"]) / scale
    if rel_change < 0.02:
        return "Similar", AMBER
    good_sign = -1 if row["Direction"] == "decrease" else 1
    if row["Delta"] * good_sign > 0:
        return "Better", GREEN
    return "Worse", RED


filtered = filtered.copy()
filtered[["Status", "StatusColor"]] = filtered.apply(lambda r: pd.Series(rag_status(r)), axis=1)
filtered["Arrow"] = filtered["Delta"].apply(lambda d: "▲" if d > 0 else ("▼" if d < 0 else "▶"))

filter_status(len(overall), len(filtered), n_active_filters, noun="indicators")

# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY — one sentence stating the overall youth result before
# the KPI row, chart, and detailed scorecard below.
# ---------------------------------------------------------------------------
n_better = int((filtered["Status"] == "Better").sum())
n_worse = int((filtered["Status"] == "Worse").sum())
if len(filtered):
    filtered_scaled = filtered.copy()
    filtered_scaled["Scale"] = filtered_scaled[["2013 Value", "2022 Value"]].abs().max(axis=1).clip(lower=1)
    filtered_scaled["RelChange"] = filtered_scaled["Delta"].abs() / filtered_scaled["Scale"]
    worst = filtered_scaled[filtered_scaled["Status"] == "Worse"].sort_values("RelChange", ascending=False)
    worst_note = f" The biggest concern: **{worst.iloc[0]['Indicator']}**." if len(worst) else ""
    st.markdown(
        f"""
        <div style="
            background:rgba(193,18,31,0.06);
            border-left:4px solid {THEME['primary']};
            border-radius:8px;
            padding:0.9rem 1.1rem;
            margin-bottom:1rem;
            font-size:1.0rem;
            line-height:1.5;
        ">
            Of <b>{len(filtered)}</b> youth indicators tracked since 2013, <b>{n_better} improved</b>
            and <b>{n_worse} got worse</b> by 2022.{worst_note}
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
# SPARKLINE (2-point line — honest shape of the data: only two survey
# years exist for youth, 2013 and 2022, not an annual series)
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


st.divider()

# ---------------------------------------------------------------------------
# SLOPE CHART — the same "did it go up or down" view used on the adult
# Trend page, applied to youth data for the first time. Doubles as the
# fastest way to see all 18 indicators' direction at a glance before
# reading the detailed scorecard below.
# ---------------------------------------------------------------------------
st.subheader("2013 → 2022, at a glance")
st.caption(
    "Each line is one indicator, running from its 2013 value to its 2022 value. "
    "Color shows direction only (amber = rose, green = fell) — not whether that's good or "
    "bad for that indicator; see the 🟢/🟡/🔴 Status column below for that judgement."
)
if len(filtered):
    slope_df = filtered[["Indicator", "2013 Value", "2022 Value"]].copy()
    fig_slope = slope_chart(
        slope_df, label_col="Indicator", left_col="2013 Value", right_col="2022 Value",
        left_title="2013", right_title="2022",
    )
    chart_or_table(fig_slope, slope_df, key="youth_slope")

st.divider()

# ---------------------------------------------------------------------------
# MORE VISUALS — additional ways to read the same 2013 vs 2022 comparison:
# a real line chart per category, a change-magnitude bar, top movers in
# each direction, a 2013-vs-2022 scatter, and a share-of-indicators donut.
# ---------------------------------------------------------------------------
if len(filtered):
    st.subheader("Category trend — 2013 → 2022 (average %)")
    st.caption(
        "One line per category, averaging all its indicators — the clearest read on "
        "which topics moved the most between the two youth surveys."
    )
    cat_avg = (
        filtered.groupby("Category")[["2013 Value", "2022 Value"]].mean().round(1)
        .reset_index().melt(id_vars="Category", value_vars=["2013 Value", "2022 Value"],
                             var_name="Year", value_name="Average %")
    )
    cat_avg["Year"] = cat_avg["Year"].str.replace(" Value", "", regex=False)
    fig_line = px.line(
        cat_avg, x="Year", y="Average %", color="Category", markers=True,
        color_discrete_sequence=COLORWAY, text="Average %",
    )
    fig_line.update_traces(textposition="top center", texttemplate="%{text:.1f}", line=dict(width=3),
                            marker=dict(size=9))
    fig_line.update_layout(height=420, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    chart_or_table(fig_line, cat_avg, key="youth_cat_line")

    left_m, right_m = st.columns(2)
    with left_m:
        st.subheader("Change 2013 → 2022 (percentage points)")
        change_df = filtered.copy().sort_values("Delta")
        change_df["Direction"] = change_df["Delta"].apply(lambda v: "Increase" if v >= 0 else "Decrease")
        fig_change = hbar(change_df, label_col="Indicator", value_col="Delta", color_col="Direction",
                           colorway=[COLORWAY[3], COLORWAY[0]], text_auto=".1f")
        chart_or_table(fig_change, change_df, key="youth_change")

    with right_m:
        st.subheader("Share of indicators — improved vs worsened")
        share_counts = filtered["Status"].value_counts().reset_index()
        share_counts.columns = ["Status", "Count"]
        fig_share = themed_pie(share_counts, names_col="Status", values_col="Count", colorway=COLORWAY)
        chart_or_table(fig_share, share_counts, key="youth_share")

    left_m2, right_m2 = st.columns(2)
    with left_m2:
        st.subheader("Top 5 most improved")
        improved = filtered[filtered["Status"] == "Better"].copy()
        improved["AbsChange"] = improved["Delta"].abs()
        improved = improved.sort_values("AbsChange", ascending=False).head(5)
        if len(improved):
            fig_up = hbar(improved, label_col="Indicator", value_col="Delta", colorway=[COLORWAY[0]],
                          text_auto=".1f")
            chart_or_table(fig_up, improved, key="youth_top_improved")
        else:
            st.info("No indicators currently marked 'Better' in the filtered view.")

    with right_m2:
        st.subheader("Top 5 most concerning")
        worsened = filtered[filtered["Status"] == "Worse"].copy()
        worsened["AbsChange"] = worsened["Delta"].abs()
        worsened = worsened.sort_values("AbsChange", ascending=False).head(5)
        if len(worsened):
            fig_down = hbar(worsened, label_col="Indicator", value_col="Delta", colorway=[COLORWAY[6]],
                            text_auto=".1f")
            chart_or_table(fig_down, worsened, key="youth_top_worsened")
        else:
            st.info("No indicators currently marked 'Worse' in the filtered view.")

    st.subheader("2013 value vs 2022 value — every indicator")
    st.caption(
        "Points below the dashed line moved down since 2013; points above it moved up. "
        "Hover any point for the exact indicator."
    )
    fig_scatter = px.scatter(
        filtered, x="2013 Value", y="2022 Value", color="Category",
        color_discrete_sequence=COLORWAY, hover_name="Indicator", size_max=10,
    )
    max_val = max(filtered["2013 Value"].max(), filtered["2022 Value"].max())
    fig_scatter.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val], mode="lines",
        line=dict(dash="dash", color="gray"), name="No change",
    ))
    fig_scatter.update_traces(marker=dict(size=11))
    chart_or_table(fig_scatter, filtered[["Indicator", "Category", "2013 Value", "2022 Value"]], key="youth_scatter")

st.divider()

# ---------------------------------------------------------------------------
# SCORECARD TABLE
# ---------------------------------------------------------------------------
st.subheader("Scorecard")

rows_html = ""
for _, r in filtered.sort_values("Category").iterrows():
    spark = sparkline_svg(r["2013 Value"], r["2022 Value"], r["StatusColor"])
    rows_html += f"""
    <tr>
        <td style="padding:10px 12px; border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600; color:#1f2937;">{r['Indicator']}</div>
            <div style="font-size:0.75rem; color:#6b7280;">{r['Category']}</div>
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['2013 Value']:.1f} %
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['2022 Value']:.1f} %
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb;">
            {spark}
        </td>
        <td style="padding:10px 12px; text-align:center; border-bottom:1px solid #e5e7eb; white-space:nowrap;">
            {r['Delta']:+.1f} %
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
            <th style="padding:10px 12px;">2013</th>
            <th style="padding:10px 12px;">2022</th>
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
    "**Status** compares the 2022 value to 2013 for that same indicator (🟢 moved in the healthy "
    "direction, 🟡 changed less than ~2%, 🔴 moved the wrong way). **Direction** is the raw trend "
    "arrow (▲ up / ▼ down), independent of whether that's good or bad for that indicator. Every "
    "value is looked up live from the source survey files, not hardcoded."
)

page_footer("Built from GYTS 2013 (aggregated) and GYTS 2022 (derived indicators)")
