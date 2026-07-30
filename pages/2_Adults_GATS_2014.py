import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_gats_2014
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, pakistan_urban_rural_map,
    hbar, themed_pie, page_footer, filter_header, filter_status, count_active,
    inject_responsive_css,
)

st.set_page_config(page_title="GATS 2014 | Adults", page_icon="📊", layout="wide")
inject_responsive_css()

THEME = apply_theme("gats_2014")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

RESIDENCE_COL = "Urban/Rural Residence [residence]"
GENDER_COL = "Gender [A01]"
AGE_COL = "How old are you? [A03]"
SMOKE_COL = "Do you *currently* smoke tobacco on a daily basis, less than daily, or not at... [B01]"
EDU_COL = "What is the highest level of education you have completed? [A04]"
WARNING_COL = "In the last 30 days, did you notice any health warnings on cigarette packages? [G202]"
AD_COL = "In the last 30 days, have you noticed any advertisements or signs promoting the... [G204a1]"

SMOKER_VALUES = ["DAILY", "LESS THAN DAILY"]

# Short, human-readable labels for axis titles/legends instead of the raw
# "question text [CODE]" column names.
SHORT_LABELS = {
    RESIDENCE_COL: "Region",
    GENDER_COL: "Gender",
    AGE_COL: "Age",
    SMOKE_COL: "Smoking Status",
    EDU_COL: "Education Level",
    WARNING_COL: "Saw Health Warning",
    AD_COL: "Saw Tobacco Ad",
}

st.title("📊 Adults — GATS 2014")
st.caption(f"Row-level data · 7,831 respondents · Custom filters by age, gender, and region · Theme: {THEME['name']}")

df = load_gats_2014()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()

residence_opts = sorted(df[RESIDENCE_COL].dropna().unique().tolist())
gender_opts = sorted(df[GENDER_COL].dropna().unique().tolist())

residence_sel = st.sidebar.multiselect("Region (Urban/Rural)", residence_opts, default=residence_opts)
gender_sel = st.sidebar.multiselect("Gender", gender_opts, default=gender_opts)

age_min, age_max = int(df[AGE_COL].min(skipna=True)), int(df[AGE_COL].max(skipna=True))
age_range = st.sidebar.slider("Age range", age_min, age_max, (age_min, age_max))

edu_opts = sorted(df[EDU_COL].dropna().unique().tolist())
n_edu = top_n_control("How many education levels to show", len(edu_opts), key="edu_n", default=min(5, len(edu_opts)))

filtered = df[
    df[RESIDENCE_COL].isin(residence_sel)
    & df[GENDER_COL].isin(gender_sel)
    & df[AGE_COL].between(age_range[0], age_range[1])
]
st.sidebar.markdown(f"**{len(filtered):,}** respondents match your filters")

n_active_filters = count_active(
    sorted(residence_sel) != sorted(residence_opts),
    sorted(gender_sel) != sorted(gender_opts),
    age_range != (age_min, age_max),
)
filter_status(len(df), len(filtered), n_active_filters, noun="respondents")

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
smoke_rate = (
    filtered[SMOKE_COL].isin(SMOKER_VALUES).sum() / len(filtered) * 100 if len(filtered) else 0
)
urban_rate = (
    filtered[filtered[RESIDENCE_COL] == "Urban"][SMOKE_COL].isin(SMOKER_VALUES).mean() * 100
    if (filtered[RESIDENCE_COL] == "Urban").any() else 0
)
rural_rate = (
    filtered[filtered[RESIDENCE_COL] == "Rural"][SMOKE_COL].isin(SMOKER_VALUES).mean() * 100
    if (filtered[RESIDENCE_COL] == "Rural").any() else 0
)

kpi_row(
    [
        {"label": "Respondents (filtered)", "value": f"{len(filtered):,}"},
        {"label": "Current tobacco smokers", "value": f"{smoke_rate:.1f}%"},
        {"label": "Average age", "value": f"{filtered[AGE_COL].mean():.1f}" if len(filtered) else "—"},
        {"label": "🏙️ Urban vs 🌾 Rural gap", "value": f"{abs(urban_rate - rural_rate):.1f} pts",
         "sub": f"{urban_rate:.1f}% vs {rural_rate:.1f}%"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("1 · Smoking status breakdown")
    status_counts = filtered[SMOKE_COL].value_counts(dropna=True).reset_index()
    status_counts.columns = ["Smoking Status", "Count"]
    fig = themed_pie(status_counts, names_col="Smoking Status", values_col="Count", colorway=COLORWAY)
    chart_or_table(fig, status_counts, key="c1")

with right:
    st.subheader("2 · Smoking status by gender")
    cross = (
        filtered.groupby([GENDER_COL, SMOKE_COL]).size().reset_index(name="Count")
        if len(filtered) else pd.DataFrame(columns=[GENDER_COL, SMOKE_COL, "Count"])
    )
    fig2 = px.bar(cross, x=GENDER_COL, y="Count", color=SMOKE_COL, barmode="group",
                  color_discrete_sequence=COLORWAY, labels=SHORT_LABELS)
    chart_or_table(fig2, cross, key="c2")

st.subheader("3 · Smoking prevalence by region")
region_rate = (
    filtered.groupby(RESIDENCE_COL)[SMOKE_COL]
    .apply(lambda s: (s.isin(SMOKER_VALUES).sum() / len(s) * 100) if len(s) else 0)
    .reset_index(name="Current Smoker %")
)
fig3 = px.bar(region_rate, x=RESIDENCE_COL, y="Current Smoker %", color=RESIDENCE_COL,
              color_discrete_sequence=COLORWAY, text_auto=".1f", labels=SHORT_LABELS)
fig3.update_layout(showlegend=False)
chart_or_table(fig3, region_rate, key="c3")

st.subheader("4 · 🗺️ Urban vs Rural — Pakistan map")
st.caption("Two representative points (not geocoded respondents) sized by current-smoker rate. Scroll to zoom, drag to pan.")
map_fig = pakistan_urban_rural_map(urban_rate, rural_rate, "Current smoker rate", ACCENT)
st.plotly_chart(map_fig, use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    st.subheader("5 · Age distribution")
    fig5 = px.histogram(filtered, x=AGE_COL, nbins=30, color_discrete_sequence=[COLORWAY[1]], labels=SHORT_LABELS)
    chart_or_table(fig5, filtered[[AGE_COL]].dropna(), key="c5")

with right2:
    st.subheader("6 · Smoker % by education level")
    edu_order = sorted(edu_opts)[:n_edu]
    edu_rate = (
        filtered[filtered[EDU_COL].isin(edu_order)]
        .groupby(EDU_COL)[SMOKE_COL]
        .apply(lambda s: (s.isin(SMOKER_VALUES).sum() / len(s) * 100) if len(s) else 0)
        .reset_index(name="Current Smoker %")
    )
    fig6 = hbar(edu_rate, label_col=EDU_COL, value_col="Current Smoker %", colorway=COLORWAY, label_width=22)
    chart_or_table(fig6, edu_rate, key="c6")

left3, right3 = st.columns(2)
with left3:
    st.subheader("7 · Noticed health warnings on packs")
    warn_counts = filtered[WARNING_COL].dropna().astype(str).value_counts().reset_index()
    warn_counts.columns = ["Response", "Count"]
    fig7 = px.bar(warn_counts, x="Response", y="Count", color="Response",
                  color_discrete_sequence=COLORWAY)
    fig7.update_layout(showlegend=False)
    chart_or_table(fig7, warn_counts, key="c7")

with right3:
    st.subheader("8 · Noticed tobacco advertisements")
    ad_counts = filtered[AD_COL].dropna().astype(str).value_counts().reset_index()
    ad_counts.columns = ["Response", "Count"]
    fig8 = px.bar(ad_counts, x="Response", y="Count", color="Response",
                  color_discrete_sequence=COLORWAY)
    fig8.update_layout(showlegend=False)
    chart_or_table(fig8, ad_counts, key="c8")

st.subheader("9 · Age spread by smoking status")
box_df = filtered[filtered[SMOKE_COL].notna()]
fig9 = px.box(box_df, x=SMOKE_COL, y=AGE_COL, color=SMOKE_COL, color_discrete_sequence=COLORWAY, labels=SHORT_LABELS)
fig9.update_layout(showlegend=False)
chart_or_table(fig9, box_df[[SMOKE_COL, AGE_COL]], key="c9")

st.subheader("10 · Population composition — gender × region")
comp = filtered.groupby([RESIDENCE_COL, GENDER_COL]).size().reset_index(name="Count")
fig10 = px.bar(comp, x=RESIDENCE_COL, y="Count", color=GENDER_COL, barmode="stack",
               color_discrete_sequence=COLORWAY, labels=SHORT_LABELS)
chart_or_table(fig10, comp, key="c10")

with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)

page_footer("GATS 2014 — row-level dataset")
