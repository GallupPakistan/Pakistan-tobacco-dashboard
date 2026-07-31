import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_gyts_2022_derived
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, hbar, themed_pie, page_footer,
    filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="GYTS 2022 | KPI Cards", page_icon="⭐", layout="wide")
inject_responsive_css()

THEME = apply_theme("kpi_2022")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

st.title("⭐ GYTS 2022 — Official Derived Indicators")
st.caption(
    "78 official CDC-calculated percentages for GYTS 2022 — ready-made KPI cards, "
    f"no additional computation needed. Theme: {THEME['name']}"
)

df = load_gyts_2022_derived().copy()

# Split "CATEGORY: description" into two clean fields.
# A few indicators have no "CATEGORY:" prefix at all — without this guard,
# each of those long descriptions became its own one-off "category",
# which is what was flooding the category charts/filters with giant labels.
split_cols = df["Indicator Description"].str.split(":", n=1, expand=True)
has_category = split_cols[1].notna() if split_cols.shape[1] > 1 else pd.Series(False, index=df.index)
df["Category"] = split_cols[0].str.strip().str.title()
df.loc[~has_category, "Category"] = "Other"
df["Short Description"] = split_cols[1].fillna(df["Indicator Description"]).str.strip()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
min_n_default = int(df["Unweighted N"].min())
filter_header()
search = st.sidebar.text_input("Search indicator description")
min_n = st.sidebar.slider(
    "Minimum unweighted N",
    int(df["Unweighted N"].min()),
    int(df["Unweighted N"].max()),
    min_n_default,
)
cat_opts = sorted(df["Category"].dropna().unique().tolist())
cat_sel = st.sidebar.multiselect("Category", cat_opts, default=cat_opts)
n_cards = top_n_control("How many KPI cards to show", len(df), key="kpi_n", default=min(24, len(df)))

filtered = df[(df["Unweighted N"] >= min_n) & (df["Category"].isin(cat_sel))]
if search:
    filtered = filtered[filtered["Indicator Description"].str.contains(search, case=False, na=False)]

# Long indicator names make wide charts unreadable — default every
# long-label chart below to the top 5, with this slider to expand up to all.
n_labels = top_n_control(
    "How many items to show on long-label charts",
    max(len(filtered), 1),
    key="kpi_labels_n",
    default=5,
)

n_active_filters = count_active(
    bool(search),
    min_n != min_n_default,
    sorted(cat_sel) != sorted(cat_opts),
)
filter_status(len(df), min(len(filtered), n_cards), n_active_filters, noun="indicators")

# ---------------------------------------------------------------------------
# TOP KPI SUMMARY ROW
# ---------------------------------------------------------------------------
kpi_row(
    [
        {"label": "Indicators matching filters", "value": f"{len(filtered)}"},
        {"label": "Average Weighted %", "value": f"{filtered['Weighted Percent'].mean():.1f}%" if len(filtered) else "—"},
        {"label": "Highest %", "value": f"{filtered['Weighted Percent'].max():.1f}%" if len(filtered) else "—"},
        {"label": "Lowest %", "value": f"{filtered['Weighted Percent'].min():.1f}%" if len(filtered) else "—"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# CATEGORIZED KPI CARDS (the core "KPI format" ask)
# ---------------------------------------------------------------------------
CATEGORY_COLORS = {cat: COLORWAY[i % len(COLORWAY)] for i, cat in enumerate(cat_opts)}
CATEGORY_ICONS = {
    "Tobacco Use": "🚬", "Cessation": "🚭", "Secondhand Smoke": "💨",
    "Knowledge And Attitudes": "🧠", "Media": "📺", "Economics": "💰",
}

st.subheader("KPI cards by category")
cards_df = filtered.sort_values("Weighted Percent", ascending=False).head(n_cards)
for cat in cat_sel:
    cat_cards = cards_df[cards_df["Category"] == cat]
    if cat_cards.empty:
        continue
    icon = CATEGORY_ICONS.get(cat, "📊")
    color = CATEGORY_COLORS.get(cat, ACCENT)
    st.markdown(f"#### {icon} {cat}")
    cols_per_row = 3
    rows = [cat_cards.iloc[i:i + cols_per_row] for i in range(0, len(cat_cards), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for col, (_, rec) in zip(cols, row.iterrows()):
            with col:
                st.markdown(
                    f"""
                    <div style="border-top:4px solid {color}; background:rgba(127,127,127,0.06);
                                border-radius:8px; padding:12px 14px; margin-bottom:10px;">
                        <div style="font-size:0.78rem; opacity:0.75; min-height:34px;">
                            {rec['Short Description'][:90]}{'...' if len(rec['Short Description']) > 90 else ''}
                        </div>
                        <div style="font-size:1.5rem; font-weight:700; color:{color};">
                            {rec['Weighted Percent']}%
                        </div>
                        <div style="font-size:0.7rem; opacity:0.55;">Unweighted N = {rec['Unweighted N']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS
# ---------------------------------------------------------------------------
st.subheader("Charts")

left, right = st.columns(2)
with left:
    st.markdown("**1 · Average Weighted % by category**")
    cat_avg = filtered.groupby("Category")["Weighted Percent"].mean().reset_index()
    fig1 = px.bar(cat_avg, x="Category", y="Weighted Percent", color="Category", color_discrete_sequence=COLORWAY, text_auto=".1f")
    fig1.update_layout(showlegend=False, xaxis_tickangle=-20)
    chart_or_table(fig1, cat_avg, key="c1")

with right:
    st.markdown("**2 · Indicator count per category**")
    cat_counts = filtered["Category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    fig2 = themed_pie(cat_counts, names_col="Category", values_col="Count", colorway=COLORWAY)
    chart_or_table(fig2, cat_counts, key="c2")

left2, right2 = st.columns(2)
with left2:
    st.markdown(f"**3 · Top {n_labels} indicators by %**")
    top10 = filtered.sort_values("Weighted Percent", ascending=False).head(n_labels)
    fig3 = hbar(top10, label_col="Short Description", value_col="Weighted Percent", color_col="Category",
                colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig3, top10, key="c3")

with right2:
    st.markdown(f"**4 · Bottom {n_labels} indicators by %**")
    bottom10 = filtered.sort_values("Weighted Percent", ascending=True).head(n_labels)
    fig4 = hbar(bottom10, label_col="Short Description", value_col="Weighted Percent", color_col="Category",
                colorway=COLORWAY, text_auto=".1f")
    chart_or_table(fig4, bottom10, key="c4")

st.markdown("**5 · Distribution of Weighted Percent values**")
fig5 = px.histogram(filtered, x="Weighted Percent", nbins=20, color_discrete_sequence=[COLORWAY[2]])
chart_or_table(fig5, filtered[["Indicator Description", "Weighted Percent"]], key="c5")

chart_num = 6
per_cat_cols = st.columns(2)
idx = 0
for cat in ["Tobacco Use", "Cessation", "Secondhand Smoke", "Knowledge And Attitudes"]:
    cat_df = filtered[filtered["Category"] == cat]
    if cat_df.empty:
        continue
    with per_cat_cols[idx % 2]:
        st.markdown(f"**{chart_num} · {cat} indicators (top {n_labels})**")
        cat_df_limited = cat_df.sort_values("Weighted Percent", ascending=False).head(n_labels)
        figc = hbar(cat_df_limited, label_col="Short Description", value_col="Weighted Percent",
                    colorway=COLORWAY, text_auto=".1f")
        chart_or_table(figc, cat_df_limited, key=f"cat_{cat}")
    chart_num += 1
    idx += 1

st.markdown(f"**{chart_num} · Reliability check — sample size vs percentage**")
fig10 = px.scatter(filtered, x="Unweighted N", y="Weighted Percent", color="Category",
                    color_discrete_sequence=COLORWAY, hover_data=["Short Description"])
chart_or_table(fig10, filtered[["Short Description", "Unweighted N", "Weighted Percent"]], key="c10")

st.divider()
with st.expander("View full table"):
    st.dataframe(df, use_container_width=True, height=400)

page_footer("GYTS 2022 — CDC-derived indicators")
