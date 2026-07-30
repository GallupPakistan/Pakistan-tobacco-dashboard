import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_gyts_2022
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, themed_pie, page_footer,
    filter_header, filter_status, count_active, inject_responsive_css,
)

st.set_page_config(page_title="GYTS 2022 | Youth", page_icon="🎓", layout="wide")
inject_responsive_css()

THEME = apply_theme("gyts_2022")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

SEX_COL = "What is your sex? [CR2]"
AGE_COL = "How old are you? [CR1]"
GRADE_COL = "In what grade/form are you? [PKR3]"
TRIED_COL = "Have you ever tried or experimented with cigarette smoking, even one or two... [CR5]"
CURRENT_COL = "During the past 30 days, on how many days did you smoke cigarettes? [CR7]"
WARNING_COL = "During the past 30 days, did you see any health warnings on cigarette packages? [CR32]"
AD_COL = "During the past 30 days, did you see any advertisements or promotions for... [CR35]"
SCHOOL_COL = "During the past 30 days, did you see anyone smoke inside the school building or... [CR22]"
PARENT_COL = "Do your parents smoke tobacco? [OR45]"
FRIEND_COL = "Do any of your closest friends smoke tobacco? [OR46]"

st.title("🎓 Youth — GYTS 2022")
st.caption(f"Row-level data · 9,783 students · Custom filters by age, sex, and grade · Theme: {THEME['name']}")

df = load_gyts_2022()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()

sex_opts = sorted(df[SEX_COL].dropna().unique().tolist())
age_opts = df[AGE_COL].dropna().unique().tolist()
grade_opts = sorted(df[GRADE_COL].dropna().unique().tolist())

sex_sel = st.sidebar.multiselect("Sex", sex_opts, default=sex_opts)
grade_sel = st.sidebar.multiselect("Grade", grade_opts, default=grade_opts)
age_sel = st.sidebar.multiselect("Age", age_opts, default=age_opts)

filtered = df[df[SEX_COL].isin(sex_sel) & df[GRADE_COL].isin(grade_sel) & df[AGE_COL].isin(age_sel)]
st.sidebar.markdown(f"**{len(filtered):,}** students match your filters")

n_active_filters = count_active(
    sorted(sex_sel) != sorted(sex_opts),
    sorted(grade_sel, key=str) != sorted(grade_opts, key=str),
    sorted(age_sel, key=str) != sorted(age_opts, key=str),
)
filter_status(len(df), len(filtered), n_active_filters, noun="students")

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
ever_tried_rate = (filtered[TRIED_COL] == "Yes").sum() / len(filtered) * 100 if len(filtered) else 0
current_smoker_rate = (
    (~filtered[CURRENT_COL].isin(["0 days"])).sum() / len(filtered) * 100 if len(filtered) else 0
)
parent_smoker_rate = (
    filtered[PARENT_COL].isin(["Father only", "Mother only", "Both"]).sum() / filtered[PARENT_COL].notna().sum() * 100
    if filtered[PARENT_COL].notna().sum() else 0
)

kpi_row(
    [
        {"label": "Students (filtered)", "value": f"{len(filtered):,}"},
        {"label": "Ever tried cigarettes", "value": f"{ever_tried_rate:.1f}%"},
        {"label": "Currently smoke (30 days)", "value": f"{current_smoker_rate:.1f}%"},
        {"label": "Household has a smoking parent", "value": f"{parent_smoker_rate:.1f}%"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("1 · Ever tried a cigarette — by sex")
    cross = filtered.groupby([SEX_COL, TRIED_COL]).size().reset_index(name="Count")
    fig = px.bar(cross, x=SEX_COL, y="Count", color=TRIED_COL, barmode="group",
                 color_discrete_sequence=COLORWAY, labels={SEX_COL: "Sex", TRIED_COL: "Ever Tried Cigarette"})
    chart_or_table(fig, cross, key="c1")

with right:
    st.subheader("2 · Age distribution")
    age_counts = filtered[AGE_COL].value_counts().reset_index()
    age_counts.columns = ["Age", "Count"]
    fig2 = px.bar(age_counts.sort_values("Age"), x="Age", y="Count", color_discrete_sequence=COLORWAY)
    fig2.update_layout(showlegend=False)
    chart_or_table(fig2, age_counts, key="c2")

left2, right2 = st.columns(2)
with left2:
    st.subheader("3 · Grade distribution")
    grade_counts = filtered[GRADE_COL].value_counts().reset_index()
    grade_counts.columns = ["Grade", "Count"]
    fig3 = px.bar(grade_counts.sort_values("Grade"), x="Grade", y="Count", color_discrete_sequence=COLORWAY)
    fig3.update_layout(showlegend=False)
    chart_or_table(fig3, grade_counts, key="c3")

with right2:
    st.subheader("4 · Smoking frequency (past 30 days)")
    freq_counts = filtered[CURRENT_COL].value_counts().reset_index()
    freq_counts.columns = ["Days Smoked", "Count"]
    fig4 = px.bar(freq_counts, x="Days Smoked", y="Count", color="Days Smoked", color_discrete_sequence=COLORWAY)
    fig4.update_layout(showlegend=False)
    chart_or_table(fig4, freq_counts, key="c4")

left3, right3 = st.columns(2)
with left3:
    st.subheader("5 · Noticed health warnings on packs")
    warn_counts = filtered[WARNING_COL].dropna().value_counts().reset_index()
    warn_counts.columns = ["Response", "Count"]
    fig5 = themed_pie(warn_counts, names_col="Response", values_col="Count", colorway=COLORWAY)
    chart_or_table(fig5, warn_counts, key="c5")

with right3:
    st.subheader("6 · Advertisement / promotion exposure")
    ad_counts = filtered[AD_COL].dropna().value_counts().reset_index()
    ad_counts.columns = ["Response", "Count"]
    fig6 = px.bar(ad_counts, x="Response", y="Count", color="Response", color_discrete_sequence=COLORWAY)
    fig6.update_layout(showlegend=False)
    chart_or_table(fig6, ad_counts, key="c6")

left4, right4 = st.columns(2)
with left4:
    st.subheader("7 · Saw smoking inside school")
    school_counts = filtered[SCHOOL_COL].dropna().value_counts().reset_index()
    school_counts.columns = ["Response", "Count"]
    fig7 = px.bar(school_counts, x="Response", y="Count", color="Response", color_discrete_sequence=COLORWAY)
    fig7.update_layout(showlegend=False)
    chart_or_table(fig7, school_counts, key="c7")

with right4:
    st.subheader("8 · Parents who smoke tobacco")
    parent_counts = filtered[PARENT_COL].dropna().value_counts().reset_index()
    parent_counts.columns = ["Response", "Count"]
    fig8 = px.bar(parent_counts, x="Response", y="Count", color="Response", color_discrete_sequence=COLORWAY)
    fig8.update_layout(showlegend=False)
    chart_or_table(fig8, parent_counts, key="c8")

st.subheader("9 · Closest friends who smoke tobacco")
friend_counts = filtered[FRIEND_COL].dropna().value_counts().reset_index()
friend_counts.columns = ["Response", "Count"]
fig9 = px.bar(friend_counts, x="Response", y="Count", color="Response", color_discrete_sequence=COLORWAY)
fig9.update_layout(showlegend=False)
chart_or_table(fig9, friend_counts, key="c9")

st.subheader("10 · Composition — sex × ever tried")
comp = filtered.groupby([SEX_COL, TRIED_COL]).size().reset_index(name="Count")
fig10 = px.bar(comp, x=SEX_COL, y="Count", color=TRIED_COL, barmode="stack", color_discrete_sequence=COLORWAY)
chart_or_table(fig10, comp, key="c10")

with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)

page_footer("GYTS 2022 — row-level dataset")
