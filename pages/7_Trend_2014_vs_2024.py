import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import load_comparison, load_gyts_2022_derived
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, hbar, themed_pie, slope_chart,
    page_footer, filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="Trend | 2014 vs 2024", page_icon="🔀", layout="wide")
inject_responsive_css()

THEME = apply_theme("trend")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

st.title("🔀 Trend — GATS 2014 vs 2024")
st.caption(f"What changed in 10 years? Side-by-side before/after comparison across indicators. Theme: {THEME['name']}")

df = load_comparison()
df["Change (pts)"] = (df["2024 Value"] - df["2014 Value"]).round(1)

# ---------------------------------------------------------------------------
# DIRECTION JUDGEMENT — same semantics as the KPI Scorecard page: "decrease"
# means a lower 2024 value is the healthy outcome, "increase" means higher
# is better, "neutral" indicators (cost/spend) are excluded from any
# good/bad call. Used for the Worst-first sort, the callout cards, and the
# Net Progress Score below.
# ---------------------------------------------------------------------------
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


def rag_status(row):
    """Better / Similar / Worse, judged the same way as the KPI Scorecard."""
    direction = DIRECTION_MAP.get(row["Indicator"], "neutral")
    if direction == "neutral":
        return "Context"
    scale = max(abs(row["2014 Value"]), abs(row["2024 Value"]), 1)
    rel_change = abs(row["Change (pts)"]) / scale
    if rel_change < 0.02:
        return "Similar"
    good_sign = -1 if direction == "decrease" else 1
    return "Better" if row["Change (pts)"] * good_sign > 0 else "Worse"

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()
groups = sorted(df["Group"].dropna().unique().tolist())
group_sel = st.sidebar.multiselect("Group", groups, default=groups)
indicators = sorted(df["Indicator"].dropna().unique().tolist())
indicator_sel = st.sidebar.multiselect("Indicator", indicators, default=indicators)

base_filtered = df[df["Group"].isin(group_sel) & df["Indicator"].isin(indicator_sel)].copy()

n_active_filters = count_active(
    sorted(group_sel) != sorted(groups),
    sorted(indicator_sel) != sorted(indicators),
)
filter_status(len(indicators), len(indicator_sel), n_active_filters, noun="indicators")

# PKR-value indicators (cost/spend) use a totally different unit than every
# other indicator here (thousands vs percentage points 0-100). Mixing them
# into the same "biggest |change|" ranking or the same chart axis as
# percentage indicators either squishes the percentage lines flat or
# crowds out real percentage indicators from the Top-N selection — so they
# get their own dedicated section further down instead.
PKR_INDICATORS = [ind for ind, d in DIRECTION_MAP.items() if d == "neutral"]
pct_filtered = base_filtered[~base_filtered["Indicator"].isin(PKR_INDICATORS)].copy()

# The core ask: let the user control HOW MANY indicators are plotted, so the
# x-axis doesn't collapse into unreadable overlapping labels.
n_show = top_n_control(
    "How many indicators to display",
    pct_filtered["Indicator"].nunique() if len(pct_filtered) else 1,
    key="trend_n",
    default=min(5, pct_filtered["Indicator"].nunique() if len(pct_filtered) else 1),
)
sort_by = st.sidebar.radio(
    "Choose which indicators", ["Largest |change|", "Worst first", "Alphabetical"], index=0
)

if sort_by == "Largest |change|":
    keep_indicators = (
        pct_filtered.groupby("Indicator")["Change (pts)"].apply(lambda s: s.abs().max())
        .sort_values(ascending=False).head(n_show).index.tolist()
    )
elif sort_by == "Worst first":
    # Rank by how far each indicator moved in the UNHEALTHY direction (a
    # decrease-type indicator going up, or an increase-type one going down).
    def worse_score(r):
        direction = DIRECTION_MAP.get(r["Indicator"], "neutral")
        sign = -1 if direction == "decrease" else 1
        return r["Change (pts)"] * sign

    scored = pct_filtered.copy()
    scored["WorseScore"] = scored.apply(worse_score, axis=1)
    keep_indicators = (
        scored.groupby("Indicator")["WorseScore"].max()
        .sort_values(ascending=False).head(n_show).index.tolist()
    )
else:
    keep_indicators = sorted(pct_filtered["Indicator"].unique().tolist())[:n_show]

filtered = pct_filtered[pct_filtered["Indicator"].isin(keep_indicators)].copy()

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
overall = pct_filtered[pct_filtered["Group"].str.strip().str.lower() == "overall"]
overall_pkr = base_filtered[
    (base_filtered["Group"].str.strip().str.lower() == "overall")
    & (base_filtered["Indicator"].isin(PKR_INDICATORS))
]
biggest_up = overall.loc[overall["Change (pts)"].idxmax()] if len(overall) else None
biggest_down = overall.loc[overall["Change (pts)"].idxmin()] if len(overall) else None

# Net Progress Score: (# indicators that moved the healthy way) minus
# (# that moved the unhealthy way), among Overall indicators that have a
# real good/bad direction (cost/spend indicators are excluded).
scored_overall = overall.copy()
scored_overall["Status"] = scored_overall.apply(rag_status, axis=1)
judged = scored_overall[scored_overall["Status"] != "Context"]
net_progress = int((judged["Status"] == "Better").sum() - (judged["Status"] == "Worse").sum())

# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY — one sentence stating the overall Net Progress result
# before the detailed KPI row and charts below.
# ---------------------------------------------------------------------------
if len(judged):
    n_better, n_worse = (judged["Status"] == "Better").sum(), (judged["Status"] == "Worse").sum()
    st.markdown(
        f"""
        <div style="
            background:rgba(27,67,50,0.08);
            border-left:4px solid {THEME['primary']};
            border-radius:8px;
            padding:0.9rem 1.1rem;
            margin-bottom:1rem;
            font-size:1.0rem;
            line-height:1.5;
        ">
            Net Progress since 2014: <b>{net_progress:+d}</b> — {n_better} indicators improved
            vs {n_worse} that got worse, out of {len(judged)} judged (current filters).
        </div>
        """,
        unsafe_allow_html=True,
    )

kpi_row(
    [
        {"label": "Indicators available", "value": f"{base_filtered['Indicator'].nunique()}"},
        {"label": "Indicators shown", "value": f"{len(keep_indicators)}"},
        {"label": "Biggest increase", "value": f"+{biggest_up['Change (pts)']:.1f} pts" if biggest_up is not None else "—",
         "sub": biggest_up["Indicator"][:40] if biggest_up is not None else ""},
        {"label": "Biggest decrease", "value": f"{biggest_down['Change (pts)']:.1f} pts" if biggest_down is not None else "—",
         "sub": biggest_down["Indicator"][:40] if biggest_down is not None else ""},
        {"label": "Net Progress Score", "value": f"{net_progress:+d}",
         "sub": f"{(judged['Status'] == 'Better').sum()} better vs {(judged['Status'] == 'Worse').sum()} worse"},
    ],
    accent=ACCENT,
)

# ---------------------------------------------------------------------------
# MOST IMPROVED / MOST CONCERNING — the two headline call-outs. Ranked by
# how far each indicator moved relative to its own scale, same yardstick
# the KPI Scorecard page uses for Better/Worse.
# ---------------------------------------------------------------------------
if len(judged):
    judged = judged.copy()
    judged["Scale"] = judged[["2014 Value", "2024 Value"]].abs().max(axis=1).clip(lower=1)
    judged["RelChange"] = (judged["Change (pts)"].abs() / judged["Scale"])

    better = judged[judged["Status"] == "Better"].sort_values("RelChange", ascending=False)
    worse = judged[judged["Status"] == "Worse"].sort_values("RelChange", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        if len(better):
            r = better.iloc[0]
            st.success(
                f"**🟢 Most improved: {r['Indicator']}**  \n"
                f"{r['2014 Value']:.1f} → {r['2024 Value']:.1f}  ({r['Change (pts)']:+.1f} pts)"
            )
        else:
            st.info("No clearly improved indicators in the current filter.")
    with c2:
        if len(worse):
            r = worse.iloc[0]
            st.error(
                f"**🔴 Most concerning: {r['Indicator']}**  \n"
                f"{r['2014 Value']:.1f} → {r['2024 Value']:.1f}  ({r['Change (pts)']:+.1f} pts)"
            )
        else:
            st.info("No clearly worsened indicators in the current filter.")

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS
# ---------------------------------------------------------------------------
st.subheader("1 · Before / after — slope chart")
st.caption(
    "Each line is one indicator, running from its 2014 value to its 2024 value. "
    "Color shows direction only (amber = rose, green = fell) — not whether that's good or "
    "bad for that particular indicator; see the callouts above for that judgement."
)
slope_df = overall[overall["Indicator"].isin(keep_indicators)][["Indicator", "2014 Value", "2024 Value"]].copy()
fig1 = slope_chart(
    slope_df, label_col="Indicator", left_col="2014 Value", right_col="2024 Value",
    left_title="2014", right_title="2024",
)
chart_or_table(fig1, slope_df, key="c1")

st.subheader("2 · Change over 10 years (percentage points)")
change_df = filtered.copy()
change_df["Indicator (Group)"] = change_df["Indicator"] + " (" + change_df["Group"] + ")"
change_df = change_df.sort_values("Change (pts)", ascending=False)
change_df["Direction"] = change_df["Change (pts)"].apply(lambda v: "Increase" if v >= 0 else "Decrease")
fig2 = hbar(change_df, label_col="Indicator (Group)", value_col="Change (pts)", color_col="Direction",
            colorway=[COLORWAY[3], COLORWAY[0]], text_auto=".1f")
chart_or_table(fig2, filtered, key="c2")

left, right = st.columns(2)
with left:
    st.subheader(f"3 · Top {n_show} biggest increases (Overall)")
    up10 = overall.sort_values("Change (pts)", ascending=False).head(n_show)
    fig3 = hbar(up10, label_col="Indicator", value_col="Change (pts)", colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig3, up10, key="c3")

with right:
    st.subheader(f"4 · Top {n_show} biggest decreases (Overall)")
    down10 = overall.sort_values("Change (pts)", ascending=True).head(n_show)
    fig4 = hbar(down10, label_col="Indicator", value_col="Change (pts)", colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig4, down10, key="c4")

left2, right2 = st.columns(2)
with left2:
    st.subheader("5 · 2014 — Overall vs Male vs Female")
    y2014 = base_filtered[base_filtered["Indicator"].isin(keep_indicators)]
    fig5 = hbar(y2014, label_col="Indicator", value_col="2014 Value", color_col="Group",
                barmode="group", colorway=COLORWAY)
    chart_or_table(fig5, y2014, key="c5")

with right2:
    st.subheader("6 · 2024 — Overall vs Male vs Female")
    fig6 = hbar(y2014, label_col="Indicator", value_col="2024 Value", color_col="Group",
                barmode="group", colorway=COLORWAY)
    chart_or_table(fig6, y2014, key="c6")

left3, right3 = st.columns(2)
with left3:
    st.subheader("7 · Share of indicators that rose vs fell")
    direction = overall.copy()
    direction["Direction"] = direction["Change (pts)"].apply(lambda v: "Increased" if v > 0 else ("Decreased" if v < 0 else "No change"))
    dir_counts = direction["Direction"].value_counts().reset_index()
    dir_counts.columns = ["Direction", "Count"]
    fig7 = themed_pie(dir_counts, names_col="Direction", values_col="Count", colorway=COLORWAY)
    chart_or_table(fig7, dir_counts, key="c7")

with right3:
    st.subheader("8 · 2014 value vs 2024 value")
    fig8 = px.scatter(filtered, x="2014 Value", y="2024 Value", color="Group", color_discrete_sequence=COLORWAY,
                       hover_name="Indicator")
    max_val = max(filtered["2014 Value"].max(), filtered["2024 Value"].max()) if len(filtered) else 1
    fig8.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines",
                               line=dict(dash="dash", color="gray"), name="No change"))
    chart_or_table(fig8, filtered, key="c8")

st.subheader("9 · Gender gap change — 2014 vs 2024")
st.caption(
    "Only indicators with a separate Male and Female breakdown in the source data can appear here — "
    "most indicators in this survey are Overall-only."
)
gender_pool = base_filtered[base_filtered["Group"].isin(["Male", "Female"]) & base_filtered["Indicator"].isin(indicator_sel)]
male = gender_pool[gender_pool["Group"] == "Male"].set_index("Indicator")["Change (pts)"]
female = gender_pool[gender_pool["Group"] == "Female"].set_index("Indicator")["Change (pts)"]
gap_df_full = pd.DataFrame({"Male Change": male, "Female Change": female}).dropna().reset_index()

if len(gap_df_full):
    gap_n = min(n_show, len(gap_df_full))
    gap_rank = gap_df_full[["Male Change", "Female Change"]].abs().max(axis=1)
    gap_keep = gap_df_full.loc[gap_rank.sort_values(ascending=False).head(gap_n).index, "Indicator"].tolist()
    gap_df = gap_df_full[gap_df_full["Indicator"].isin(gap_keep)]
    gap_melted = gap_df.melt(id_vars="Indicator", var_name="Group", value_name="Change (pts)")
    fig9 = hbar(gap_melted, label_col="Indicator", value_col="Change (pts)", color_col="Group",
                barmode="group", colorway=COLORWAY)
    chart_or_table(fig9, gap_df, key="c9")
else:
    st.info(
        "No indicators in the current Group/Indicator filters have both a Male and a Female "
        "value — only 'Current tobacco use' and 'Current tobacco smoking' carry a gender "
        "breakdown in this dataset, so make sure both are included in the Indicator filter."
    )

st.subheader("10 · Full comparison table")
st.dataframe(filtered, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# COST & SPENDING (PKR) — kept separate from every chart above on purpose:
# these 2 indicators are measured in PKR (thousands), not percentage points,
# so plotting them on the same axis as the rest either flattens the
# percentage lines or crowds them out of the Top-N ranking entirely.
# ---------------------------------------------------------------------------
if len(overall_pkr):
    st.subheader("Cost & spending (PKR) — kept on its own scale")
    st.caption(
        "These 2 indicators are measured in Pakistani Rupees, not percentage points, so they're "
        "shown separately rather than sharing an axis with the rest of this page."
    )
    pkr_slope = overall_pkr[["Indicator", "2014 Value", "2024 Value"]].copy()
    fig_pkr = slope_chart(
        pkr_slope, label_col="Indicator", left_col="2014 Value", right_col="2024 Value",
        left_title="2014", right_title="2024", label_width=26,
    )
    chart_or_table(fig_pkr, pkr_slope, key="c_pkr")

st.divider()

# ---------------------------------------------------------------------------
# 11 · YOUTH (GYTS 2022) vs ADULT (GATS 2024) — connects the youth survey
# story to the adult one wherever a genuinely comparable theme exists in
# both. Values are looked up live from the underlying data (not hardcoded)
# so this stays correct if the source CSVs are ever refreshed.
# ---------------------------------------------------------------------------
st.subheader("11 · Youth (GYTS 2022) vs Adult (GATS 2024) — shared themes")
st.caption(
    "Where the youth and adult surveys asked comparable questions, shown side by side — "
    "the two disconnected surveys read together as one generational picture."
)

gyts_derived = load_gyts_2022_derived()


def adult_value(indicator_name: str):
    row = overall[overall["Indicator"] == indicator_name]
    return float(row["2024 Value"].iloc[0]) if len(row) else None


def youth_value(keyword: str):
    match = gyts_derived[gyts_derived["Indicator Description"].str.contains(keyword, case=False, na=False, regex=False)]
    return float(match["Weighted Percent"].iloc[0]) if len(match) else None


YOUTH_ADULT_THEMES = [
    ("Current any tobacco use", "Current tobacco use", "currently use any tobacco products"),
    ("Current tobacco smoking", "Current tobacco smoking", "currently smoke any tobacco products"),
    ("Secondhand smoke exposure — Home (7 days)", "SHS exposure: Home", "exposed to tobacco smoke at home in the past 7 days"),
    ("Secondhand smoke exposure — School", "SHS exposure: Schools", "smoking inside the school building or outside on school property"),
    ("Noticed tobacco ads/promos in stores", "Noticed tobacco ads/promos in stores", "tobacco marketing at points of sale in the past 30 days"),
    ("Noticed health warnings on cigarette packages", "Noticed health warnings on packages", "noticed health warnings on cigarette packages in the past 30 days"),
    ("Considered quitting because of warnings", "Considered quitting due to warnings", "thought about quitting smoking in the past 30 days because of health warnings"),
]

ya_rows = []
for theme, adult_ind, youth_kw in YOUTH_ADULT_THEMES:
    a_val, y_val = adult_value(adult_ind), youth_value(youth_kw)
    if a_val is not None and y_val is not None:
        ya_rows.append({"Theme": theme, "Adult — GATS 2024 (%)": a_val, "Youth — GYTS 2022 (%)": y_val})

ya_df = pd.DataFrame(ya_rows)
if len(ya_df):
    ya_melted = ya_df.melt(id_vars="Theme", var_name="Survey", value_name="Value")
    fig11 = hbar(ya_melted, label_col="Theme", value_col="Value", color_col="Survey", barmode="group",
                 colorway=[COLORWAY[0], COLORWAY[2]])
    chart_or_table(fig11, ya_df, key="c11")
else:
    st.info("No matching youth/adult themes found in the current data.")

page_footer("Trend built from the GATS 2014 vs 2024 comparison dataset, cross-referenced with GYTS 2022")
