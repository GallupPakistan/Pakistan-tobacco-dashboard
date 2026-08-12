import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_comparison
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, hbar, themed_pie, page_footer,
    filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="Adults Compare | 2014 vs 2024", page_icon="🆚", layout="wide")
inject_responsive_css()

THEME = apply_theme("trend")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

st.title("🆚 Adults — GATS 2014 vs 2024, side by side")
st.caption(
    "Sits right after the two individual Adult Survey pages — the same indicators and "
    f"chart styles from GATS 2014 and GATS 2024, drawn together for a direct before/after read. Theme: {THEME['name']}"
)

df = load_comparison()
df["Change (pts)"] = (df["2024 Value"] - df["2014 Value"]).round(1)

# ---------------------------------------------------------------------------
# DIRECTION AWARENESS
# "Lower is better" is NOT true for every indicator here — a drop in
# "Quit attempts", "Advised to quit by healthcare provider", "Considered
# quitting due to warnings", or "Noticed health warnings on packages" is a
# DECLINE, not an improvement. Without this map, idxmin() on raw Change(pts)
# will mislabel any of those as the "biggest improvement" whenever a user
# filters down to a set of indicators dominated by them.
# ---------------------------------------------------------------------------
GOOD_DIRECTION = {
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
}

def improvement_score(row):
    """Positive score = moved in the healthy direction; negative = moved the wrong way.
    Indicators with no known direction (e.g. price/expenditure) return None and are excluded."""
    direction = GOOD_DIRECTION.get(row["Indicator"])
    if direction is None:
        return None
    sign = -1 if direction == "decrease" else 1
    return row["Change (pts)"] * sign

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()
indicators = sorted(df["Indicator"].dropna().unique().tolist())
indicator_sel = st.sidebar.multiselect("Indicator", indicators, default=indicators)
n_show = top_n_control("How many indicators to display", len(indicator_sel) or 1, key="cmp_n",
                        default=min(6, len(indicator_sel) or 1))

filtered = df[df["Indicator"].isin(indicator_sel)].copy()

n_active_filters = count_active(sorted(indicator_sel) != sorted(indicators))
filter_status(len(indicators), len(indicator_sel), n_active_filters, noun="indicators")

overall = filtered[filtered["Group"].str.strip().str.lower() == "overall"].copy()
PKR_INDICATORS = [i for i in indicators if "PKR" in i or "cost" in i.lower() or "expenditure" in i.lower()]
overall_pct = overall[~overall["Indicator"].isin(PKR_INDICATORS)].copy()
overall_pct["Improvement Score"] = overall_pct.apply(improvement_score, axis=1)
overall_directional = overall_pct.dropna(subset=["Improvement Score"])

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
smoke_row = df[(df["Group"] == "Overall") & (df["Indicator"] == "Current tobacco use")]
smoke_2014 = float(smoke_row["2014 Value"].iloc[0]) if len(smoke_row) else None
smoke_2024 = float(smoke_row["2024 Value"].iloc[0]) if len(smoke_row) else None

# "Biggest improvement" now ranks by Improvement Score (direction-aware),
# not raw Change(pts) — so it can never mislabel a decline as progress.
biggest_drop = (
    overall_directional.loc[overall_directional["Improvement Score"].idxmax()]
    if len(overall_directional) else None
)

kpi_row(
    [
        {"label": "Current tobacco use — 2014", "value": f"{smoke_2014:.1f}%" if smoke_2014 is not None else "—"},
        {"label": "Current tobacco use — 2024", "value": f"{smoke_2024:.1f}%" if smoke_2024 is not None else "—"},
        {"label": "Change", "value": f"{smoke_2024 - smoke_2014:+.1f} pts" if smoke_2014 is not None and smoke_2024 is not None else "—"},
        {"label": "Biggest improvement", "value": f"{biggest_drop['Change (pts)']:+.1f} pts" if biggest_drop is not None else "—",
         "sub": biggest_drop["Indicator"][:40] if biggest_drop is not None else ""},
    ],
    accent=ACCENT,
)

if len(overall_pct) != len(overall_directional):
    st.caption(
        f"ℹ️ {len(overall_pct) - len(overall_directional)} indicator(s) in the current filter have no defined "
        "'improvement direction' (e.g. price/expenditure figures) and are excluded from the improvement ranking above."
    )

st.divider()

# ---------------------------------------------------------------------------
# 1 · DONUT PAIR — same chart type as GATS 2014's "Smoking status breakdown"
# pie, drawn for both years so the shrink in the smoker share is visible at
# a glance.
# ---------------------------------------------------------------------------
st.subheader("1 · Current tobacco use — 2014 vs 2024")
left, right = st.columns(2)
if smoke_2014 is not None and smoke_2024 is not None:
    pie_2014 = pd.DataFrame({"Status": ["Tobacco user", "Non-user"], "Percent": [smoke_2014, 100 - smoke_2014]})
    pie_2024 = pd.DataFrame({"Status": ["Tobacco user", "Non-user"], "Percent": [smoke_2024, 100 - smoke_2024]})
    with left:
        st.caption("GATS 2014")
        fig_p1 = themed_pie(pie_2014, names_col="Status", values_col="Percent", colorway=COLORWAY)
        chart_or_table(fig_p1, pie_2014, key="p2014")
    with right:
        st.caption("GATS 2024")
        fig_p2 = themed_pie(pie_2024, names_col="Status", values_col="Percent", colorway=COLORWAY)
        chart_or_table(fig_p2, pie_2024, key="p2024")
else:
    st.info("'Current tobacco use' is filtered out — add it back to the Indicator filter to see this chart.")

# ---------------------------------------------------------------------------
# 2 · MEN vs WOMEN, 2014 vs 2024 — same grouped-bar style as the GATS 2024
# "Men vs Women" chart, but with both years side by side.
# ---------------------------------------------------------------------------
st.subheader("2 · Men vs Women — 2014 vs 2024")
st.caption(
    "Only indicators with a Male/Female breakdown in the source data can appear here — "
    "'Current tobacco use' and 'Current tobacco smoking' are the two available."
)
gender_pool = df[df["Group"].isin(["Male", "Female"]) & df["Indicator"].isin(indicator_sel)].copy()
if len(gender_pool):
    g14 = gender_pool[["Indicator", "Group", "2014 Value"]].rename(columns={"2014 Value": "Percent"})
    g14["Series"] = "2014 — " + g14["Group"]
    g24 = gender_pool[["Indicator", "Group", "2024 Value"]].rename(columns={"2024 Value": "Percent"})
    g24["Series"] = "2024 — " + g24["Group"]
    gender_melted = pd.concat([g14, g24], ignore_index=True)
    fig_gender = hbar(gender_melted, label_col="Indicator", value_col="Percent", color_col="Series",
                       barmode="group", colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig_gender, gender_melted, key="gendercmp")
else:
    st.info("No indicators in the current filter have a Male/Female breakdown.")

# ---------------------------------------------------------------------------
# 3 · TOP-N INDICATORS, OVERALL 2014 vs 2024 — hbar with value labels, the
# same "long-label horizontal bar" style used throughout both source pages.
# ---------------------------------------------------------------------------
st.subheader(f"3 · Top {n_show} indicators — Overall, 2014 vs 2024")
top_ind = (
    overall_pct.groupby("Indicator")["Change (pts)"].apply(lambda s: s.abs().max())
    .sort_values(ascending=False).head(n_show).index.tolist()
)
top_df = overall_pct[overall_pct["Indicator"].isin(top_ind)]
top_melted = top_df.melt(id_vars="Indicator", value_vars=["2014 Value", "2024 Value"],
                          var_name="Year", value_name="Percent")
fig3 = hbar(top_melted, label_col="Indicator", value_col="Percent", color_col="Year",
            barmode="group", colorway=[COLORWAY[3], COLORWAY[0]], text_auto=".1f")
chart_or_table(fig3, top_df, key="c3")

# ---------------------------------------------------------------------------
# 4 · CHANGE MAGNITUDE — mirrors the "Smoker % by education level" hbar
# style from GATS 2014: one bar per category, sorted, with value labels.
# This chart intentionally shows raw magnitude of change (not "improvement"),
# so no direction-awareness is needed here — it's purely "how much moved".
# ---------------------------------------------------------------------------
st.subheader(f"4 · Biggest movers (Overall) — change in percentage points")
st.caption("Shows magnitude of change only — a bar here doesn't imply 'better' or 'worse', just 'moved a lot'.")
change_top = overall_pct.reindex(overall_pct["Change (pts)"].abs().sort_values(ascending=False).index).head(n_show)
change_top = change_top.sort_values("Change (pts)")
fig4 = hbar(change_top, label_col="Indicator", value_col="Change (pts)", colorway=COLORWAY, text_auto=".1f")
chart_or_table(fig4, change_top, key="c4")

st.divider()
st.subheader("Full comparison table")
st.dataframe(filtered, use_container_width=True)

page_footer("GATS 2014 vs 2024 — built from the two Adult Survey pages, same chart styles, side by side")
