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
AGE_COL = "Age in Years [age]"
SMOKE_COL = "Do you *currently* smoke tobacco on a daily basis, less than daily, or not at... [B01]"
EDU_COL = "What is the highest level of education you have completed? [A04]"
WARNING_COL = "In the last 30 days, did you notice any health warnings on cigarette packages? [G202]"
AD_COL = "In the last 30 days, have you noticed any advertisements or signs promoting the... [G204a1]"
WEIGHT_COL = "Final Sample Weight [gatsweight]"  # <-- required for every % in this file

SMOKER_VALUES = ["DAILY", "LESS THAN DAILY"]
SMOKE_VALID_VALUES = ["DAILY", "LESS THAN DAILY", "NOT AT ALL"]  # excludes DON'T KNOW/REFUSED

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


# ---------------------------------------------------------------------------
# Weighted-statistics helpers
# GATS uses a multi-stage stratified sample design, so every respondent
# carries a sample weight (gatsweight). National/subgroup percentages MUST be
# computed as weighted percentages, not simple row counts/means, or they will
# not match the official published figures.
# ---------------------------------------------------------------------------

def weighted_pct(frame, value_col, positive_values, valid_values=None, weight_col=WEIGHT_COL):
    """Weighted % of `value_col` in `positive_values`, among rows where
    `value_col` is in `valid_values` (defaults to all non-null)."""
    if len(frame) == 0:
        return 0.0
    if valid_values is not None:
        valid = frame[value_col].isin(valid_values)
    else:
        valid = frame[value_col].notna()
    w = frame.loc[valid, weight_col].astype(float)
    total_w = w.sum()
    if total_w == 0:
        return 0.0
    pos = frame.loc[valid, value_col].isin(positive_values)
    return 100 * w[pos].sum() / total_w


def weighted_value_counts_pct(frame, value_col, weight_col=WEIGHT_COL):
    """Weighted % distribution across all observed categories of value_col."""
    d = frame.dropna(subset=[value_col]).copy()
    if len(d) == 0:
        return pd.DataFrame(columns=[value_col, "Weighted Percent"])
    total_w = d[weight_col].astype(float).sum()
    out = (
        d.groupby(value_col)[weight_col]
        .sum()
        .reset_index(name="Weighted Percent")
    )
    out["Weighted Percent"] = (out["Weighted Percent"] / total_w * 100).round(1)
    return out.sort_values("Weighted Percent", ascending=False)


def weighted_cross_pct(frame, group_col, value_col, weight_col=WEIGHT_COL):
    """Weighted % of value_col categories WITHIN each group_col category
    (each group's weighted percentages sum to 100)."""
    d = frame.dropna(subset=[group_col, value_col]).copy()
    if len(d) == 0:
        return pd.DataFrame(columns=[group_col, value_col, "Weighted Percent"])
    out = (
        d.groupby([group_col, value_col])[weight_col]
        .sum()
        .reset_index(name="w")
    )
    group_totals = out.groupby(group_col)["w"].transform("sum")
    out["Weighted Percent"] = (out["w"] / group_totals * 100).round(1)
    return out.drop(columns="w")


def weighted_rate_by_group(frame, group_col, value_col, positive_values, valid_values=None, weight_col=WEIGHT_COL):
    """Weighted % positive, computed separately per group_col category."""
    rows = []
    for g, sub in frame.groupby(group_col):
        rows.append({group_col: g, "Current Smoker %": weighted_pct(sub, value_col, positive_values, valid_values, weight_col)})
    return pd.DataFrame(rows)


def weighted_mean(frame, value_col, weight_col=WEIGHT_COL):
    d = frame.dropna(subset=[value_col, weight_col])
    if len(d) == 0:
        return float("nan")
    w = d[weight_col].astype(float)
    return (d[value_col].astype(float) * w).sum() / w.sum()


st.title("📊 Adults — GATS 2014")
st.caption(f"Row-level data · 7,831 respondents · Survey-weighted · Custom filters by age, gender, and region · Theme: {THEME['name']}")

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

if n_active_filters:
    st.info(
        "Note: percentages below are still weighted using each respondent's survey weight, "
        "but once you filter to a custom subgroup, results are no longer guaranteed to match "
        "an official published figure (official tables only publish specific subgroup combinations).",
        icon="ℹ️",
    )

# ---------------------------------------------------------------------------
# KPI ROW  (all weighted)
# ---------------------------------------------------------------------------
smoke_rate = weighted_pct(filtered, SMOKE_COL, SMOKER_VALUES, SMOKE_VALID_VALUES)
urban_rate = weighted_pct(filtered[filtered[RESIDENCE_COL] == "Urban"], SMOKE_COL, SMOKER_VALUES, SMOKE_VALID_VALUES)
rural_rate = weighted_pct(filtered[filtered[RESIDENCE_COL] == "Rural"], SMOKE_COL, SMOKER_VALUES, SMOKE_VALID_VALUES)
avg_age = weighted_mean(filtered, AGE_COL)

kpi_row(
    [
        {"label": "Respondents (filtered)", "value": f"{len(filtered):,}"},
        {"label": "Current tobacco smokers (weighted)", "value": f"{smoke_rate:.1f}%"},
        {"label": "Average age (weighted)", "value": f"{avg_age:.1f}" if len(filtered) else "—"},
        {"label": "🏙️ Urban vs 🌾 Rural gap", "value": f"{abs(urban_rate - rural_rate):.1f} pts",
         "sub": f"{urban_rate:.1f}% vs {rural_rate:.1f}%"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS  (all weighted)
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("1 · Smoking status breakdown")
    status_counts = weighted_value_counts_pct(filtered, SMOKE_COL)
    status_counts.columns = ["Smoking Status", "Weighted Percent"]
    fig = themed_pie(status_counts, names_col="Smoking Status", values_col="Weighted Percent", colorway=COLORWAY)
    chart_or_table(fig, status_counts, key="c1")

with right:
    st.subheader("2 · Smoking status by gender")
    cross = weighted_cross_pct(filtered, GENDER_COL, SMOKE_COL)
    fig2 = px.bar(cross, x=GENDER_COL, y="Weighted Percent", color=SMOKE_COL, barmode="group",
                  color_discrete_sequence=COLORWAY, labels=SHORT_LABELS, text_auto=".1f")
    fig2.update_traces(textposition="outside", cliponaxis=False)
    chart_or_table(fig2, cross, key="c2")

st.subheader("3 · Smoking prevalence by region")
region_rate = weighted_rate_by_group(filtered, RESIDENCE_COL, SMOKE_COL, SMOKER_VALUES, SMOKE_VALID_VALUES)
fig3 = px.bar(region_rate, x=RESIDENCE_COL, y="Current Smoker %", color=RESIDENCE_COL,
              color_discrete_sequence=COLORWAY, text_auto=".1f", labels=SHORT_LABELS)
fig3.update_layout(showlegend=False)
chart_or_table(fig3, region_rate, key="c3")

st.subheader("4 · 🗺️ Urban vs Rural — Pakistan map")
st.caption("Two representative points (not geocoded respondents) sized by current-smoker rate (weighted). Scroll to zoom, drag to pan.")
map_fig = pakistan_urban_rural_map(urban_rate, rural_rate, "Current smoker rate", ACCENT)
st.plotly_chart(map_fig, use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    st.subheader("5 · Age distribution")
    st.caption("Shown unweighted (sample counts) — this reflects who was surveyed, not the weighted population distribution.")
    fig5 = px.histogram(filtered, x=AGE_COL, nbins=30, color_discrete_sequence=[COLORWAY[1]], labels=SHORT_LABELS)
    chart_or_table(fig5, filtered[[AGE_COL]].dropna(), key="c5")

with right2:
    st.subheader("6 · Smoker % by education level")
    edu_order = sorted(edu_opts)[:n_edu]
    edu_rate = weighted_rate_by_group(
        filtered[filtered[EDU_COL].isin(edu_order)], EDU_COL, SMOKE_COL, SMOKER_VALUES, SMOKE_VALID_VALUES
    )
    edu_rate = edu_rate.rename(columns={EDU_COL: EDU_COL})
    fig6 = hbar(edu_rate, label_col=EDU_COL, value_col="Current Smoker %", colorway=COLORWAY, label_width=22,
                text_auto=".1f")
    chart_or_table(fig6, edu_rate, key="c6")

left3, right3 = st.columns(2)
with left3:
    st.subheader("7 · Noticed health warnings on packs")
    warn_pct = weighted_value_counts_pct(filtered, WARNING_COL)
    warn_pct.columns = ["Response", "Percent"]
    fig7 = px.bar(warn_pct, x="Response", y="Percent", color="Response",
                  color_discrete_sequence=COLORWAY, text_auto=".1f",
                  labels={"Percent": "Weighted Percent (%)"})
    fig7.update_layout(legend_title_text="Response")
    fig7.update_traces(textposition="outside", cliponaxis=False)
    chart_or_table(fig7, warn_pct, key="c7")

with right3:
    st.subheader("8 · Noticed tobacco advertisements")
    ad_pct = weighted_value_counts_pct(filtered, AD_COL)
    ad_pct.columns = ["Response", "Percent"]
    fig8 = px.bar(ad_pct, x="Response", y="Percent", color="Response",
                  color_discrete_sequence=COLORWAY, text_auto=".1f",
                  labels={"Percent": "Weighted Percent (%)"})
    fig8.update_layout(legend_title_text="Response")
    fig8.update_traces(textposition="outside", cliponaxis=False)
    chart_or_table(fig8, ad_pct, key="c8")

st.subheader("9 · Age spread by smoking status")
st.caption(
    "Box shows the middle 50% of ages (25th–75th percentile); the line inside each box is the median age; "
    "dots are outliers. Shown unweighted — weighting a box plot does not have a single standard definition, "
    "so treat this chart as descriptive of the sample, not a population estimate."
)
box_df = filtered[filtered[SMOKE_COL].notna()]
fig9 = px.box(box_df, x=SMOKE_COL, y=AGE_COL, color=SMOKE_COL, color_discrete_sequence=COLORWAY, labels=SHORT_LABELS)
fig9.update_layout(legend_title_text="Smoking Status")
medians = box_df.groupby(SMOKE_COL)[AGE_COL].median()
for status, med_age in medians.items():
    fig9.add_annotation(
        x=status, y=med_age, text=f"Median: {med_age:.0f}",
        showarrow=False, yshift=14, font=dict(size=11, color="#1B4332"),
        bgcolor="rgba(255,255,255,0.75)",
    )
chart_or_table(fig9, box_df[[SMOKE_COL, AGE_COL]], key="c9")

st.subheader("10 · Population composition — gender × region")
comp = (
    filtered.groupby([RESIDENCE_COL, GENDER_COL])[WEIGHT_COL]
    .sum()
    .reset_index(name="Weighted Population")
)
fig10 = px.bar(comp, x=RESIDENCE_COL, y="Weighted Population", color=GENDER_COL, barmode="stack",
               color_discrete_sequence=COLORWAY, labels=SHORT_LABELS, text_auto=".2s")
fig10.update_traces(textposition="inside")
chart_or_table(fig10, comp, key="c10")

with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)

page_footer("GATS 2014 — row-level dataset, survey-weighted")
