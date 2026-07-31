import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_gats_2024
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, hbar, themed_pie, page_footer,
    filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="GATS 2024 | Adults", page_icon="🚬", layout="wide")
inject_responsive_css()

THEME = apply_theme("gats_2024")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

st.title("🚬 Adults — GATS 2024 (Key Indicators)")
st.caption(
    "The latest adult survey round. Row-level microdata is not yet public, so this "
    f"page presents the official pre-aggregated key indicators. Theme: {THEME['name']}"
)

df = load_gats_2024()

filter_header()
categories = sorted(df["Category"].dropna().unique().tolist())
category_sel = st.sidebar.multiselect("Category", categories, default=categories)
n_indicators = top_n_control("How many indicators to show (long-label charts)", len(df), key="g24_n", default=min(5, len(df)))

filtered = df[df["Category"].isin(category_sel)]

n_active_filters = count_active(sorted(category_sel) != sorted(categories))
filter_status(len(df), len(filtered), n_active_filters, noun="indicators")

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
overall_avg = filtered["Overall (%)"].mean() if len(filtered) else 0
gender_gap = (filtered["Men (%)"] - filtered["Women (%)"]).abs().mean() if len(filtered) else 0
top_row = filtered.sort_values("Overall (%)", ascending=False).iloc[0] if len(filtered) else None

kpi_row(
    [
        {"label": "Indicators shown", "value": f"{len(filtered)}"},
        {"label": "Average value (Overall)", "value": f"{overall_avg:.1f}%"},
        {"label": "Average gender gap", "value": f"{gender_gap:.1f} pts"},
        {"label": "Highest indicator", "value": f"{top_row['Overall (%)']:.1f}%" if top_row is not None else "—",
         "sub": top_row["Indicator"][:40] if top_row is not None else ""},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS
# ---------------------------------------------------------------------------
st.subheader("1 · Men vs Women")
st.caption(
    "Only indicators with a separate Men and Women figure in the source data can appear here — "
    "several indicators (e.g. Media, Knowledge/Attitudes, Economics) are Overall-only."
)
gendered = filtered[filtered["Men (%)"].notna() & filtered["Women (%)"].notna()]
limited = gendered.sort_values("Overall (%)", ascending=False).head(n_indicators)
if len(limited):
    melted = limited.melt(id_vars=["Category", "Indicator"], value_vars=["Men (%)", "Women (%)"],
                           var_name="Group", value_name="Percent")
    fig1 = hbar(melted, label_col="Indicator", value_col="Percent", color_col="Group",
                barmode="group", colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig1, limited, key="c1")
else:
    st.info("No indicators in the current Category filter have a Men/Women breakdown.")

# Charts 2-7: one per category
cat_chart_num = 2
cat_cols = st.columns(2)
col_idx = 0
for cat in ["Tobacco Use", "Secondhand Smoke", "Media", "Knowledge/Attitudes", "Cessation", "Economics"]:
    cat_df = filtered[filtered["Category"] == cat]
    if cat_df.empty:
        continue
    cat_has_gender = cat_df["Men (%)"].notna().any() and cat_df["Women (%)"].notna().any()
    with cat_cols[col_idx % 2]:
        st.subheader(f"{cat_chart_num} · {cat} (top {n_indicators})")
        if cat_has_gender:
            cat_df_gendered = cat_df[cat_df["Men (%)"].notna() & cat_df["Women (%)"].notna()]
            cat_df_limited = cat_df_gendered.sort_values("Overall (%)", ascending=False).head(n_indicators)
            cat_melted = cat_df_limited.melt(id_vars=["Indicator"], value_vars=["Men (%)", "Women (%)"],
                                              var_name="Group", value_name="Percent")
            fig = hbar(cat_melted, label_col="Indicator", value_col="Percent", color_col="Group",
                       barmode="group", colorway=COLORWAY, label_width=22, text_auto=".1f")
            fig.update_layout(showlegend=(col_idx == 0))
            chart_or_table(fig, cat_df_limited, key=f"cat_{cat}")
        else:
            # This category has no Men/Women split in the source data at all —
            # show the Overall figure instead of an empty chart.
            st.caption("No Men/Women breakdown for this category — showing Overall (%).")
            cat_df_limited = cat_df.sort_values("Overall (%)", ascending=False).head(n_indicators)
            fig = hbar(cat_df_limited, label_col="Indicator", value_col="Overall (%)",
                       colorway=COLORWAY, label_width=22, text_auto=".1f")
            chart_or_table(fig, cat_df_limited, key=f"cat_{cat}")
    cat_chart_num += 1
    col_idx += 1

st.subheader(f"{cat_chart_num} · Gender gap by indicator (Men − Women)")
gap_df = filtered.copy()
gap_df["Gender Gap (pts)"] = (gap_df["Men (%)"] - gap_df["Women (%)"]).round(1)
gap_df = gap_df.sort_values("Gender Gap (pts)", ascending=False).head(n_indicators)
fig_gap = hbar(gap_df, label_col="Indicator", value_col="Gender Gap (pts)", color_col="Category",
               colorway=COLORWAY)
chart_or_table(fig_gap, gap_df, key="gap")
cat_chart_num += 1

st.subheader(f"{cat_chart_num} · Indicator count by category")
cat_counts = filtered["Category"].value_counts().reset_index()
cat_counts.columns = ["Category", "Count"]
fig_cat = themed_pie(cat_counts, names_col="Category", values_col="Count", colorway=COLORWAY)
chart_or_table(fig_cat, cat_counts, key="catcount")
cat_chart_num += 1

st.subheader(f"{cat_chart_num} · Top {min(n_indicators, len(filtered))} indicators by overall %")
top10 = filtered.sort_values("Overall (%)", ascending=False).head(n_indicators)
fig_top = hbar(top10, label_col="Indicator", value_col="Overall (%)", color_col="Category",
               colorway=COLORWAY, text_auto=".1f")
chart_or_table(fig_top, top10, key="top10")

st.divider()
st.subheader("By category — full breakdown")
for cat in category_sel:
    with st.expander(cat):
        st.dataframe(filtered[filtered["Category"] == cat], use_container_width=True)

page_footer("GATS 2024 — aggregated official indicators")
