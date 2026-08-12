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
WEIGHT_COL = "FinalWgt"  # <-- required for every % on this page

# ---------------------------------------------------------------------------
# Weighted-statistics helpers
# GYTS uses a school-based cluster sample design, so every respondent carries
# a sample weight (FinalWgt). Also critical: pandas' `~series.isin([...])`
# treats missing (NaN) values as NOT in the list, so its negation counts
# missing/non-response rows as a "positive" match — silently inflating rates
# whenever a question has non-response. Every helper below explicitly drops
# missing values from the denominator before computing a rate.
# ---------------------------------------------------------------------------

def weighted_pct(frame, value_col, positive_values, weight_col=WEIGHT_COL):
    """Weighted % of value_col in positive_values, among rows where value_col
    is not missing. `positive_values` can be a list of exact values, or a
    callable(series) -> boolean mask for more complex conditions."""
    valid = frame[value_col].notna()
    d = frame.loc[valid]
    if len(d) == 0:
        return 0.0
    w = d[weight_col].astype(float)
    total_w = w.sum()
    if total_w == 0:
        return 0.0
    if callable(positive_values):
        pos = positive_values(d[value_col])
    else:
        pos = d[value_col].isin(positive_values)
    return 100 * w[pos].sum() / total_w


def weighted_value_counts_pct(frame, value_col, weight_col=WEIGHT_COL):
    """Weighted % distribution across all observed (non-missing) categories."""
    d = frame.dropna(subset=[value_col])
    if len(d) == 0:
        return pd.DataFrame(columns=[value_col, "Percent"])
    total_w = d[weight_col].astype(float).sum()
    out = d.groupby(value_col)[weight_col].sum().reset_index(name="Percent")
    out["Percent"] = (out["Percent"] / total_w * 100).round(1)
    return out


def weighted_cross_pct(frame, group_col, value_col, weight_col=WEIGHT_COL):
    """Weighted % of value_col WITHIN each group_col category (each group
    sums to 100)."""
    d = frame.dropna(subset=[group_col, value_col])
    if len(d) == 0:
        return pd.DataFrame(columns=[group_col, value_col, "Percent"])
    out = d.groupby([group_col, value_col])[weight_col].sum().reset_index(name="w")
    totals = out.groupby(group_col)["w"].transform("sum")
    out["Percent"] = (out["w"] / totals * 100).round(1)
    return out.drop(columns="w")


st.title("🎓 Youth — GYTS 2022")
st.caption(f"Row-level data · 9,783 students · Survey-weighted · Custom filters by age, gender, and grade · Theme: {THEME['name']}")

df = load_gyts_2022()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------
filter_header()

sex_opts = sorted(df[SEX_COL].dropna().unique().tolist())
age_opts = df[AGE_COL].dropna().unique().tolist()
grade_opts = sorted(df[GRADE_COL].dropna().unique().tolist())

sex_sel = st.sidebar.multiselect("Gender", sex_opts, default=sex_opts)
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
# KPI ROW  (all weighted, missing responses excluded from denominators)
# ---------------------------------------------------------------------------
ever_tried_rate = weighted_pct(filtered, TRIED_COL, ["Yes"])
current_smoker_rate = weighted_pct(filtered, CURRENT_COL, lambda s: s != "0 days")
parent_smoker_rate = weighted_pct(filtered, PARENT_COL, ["Father only", "Mother only", "Both"])

kpi_row(
    [
        {"label": "Students (filtered)", "value": f"{len(filtered):,}"},
        {"label": "Ever tried cigarettes (weighted)", "value": f"{ever_tried_rate:.1f}%"},
        {"label": "Currently smoke, 30 days (weighted)", "value": f"{current_smoker_rate:.1f}%"},
        {"label": "Household has a smoking parent (weighted)", "value": f"{parent_smoker_rate:.1f}%"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 10 CHARTS  (all weighted)
# ---------------------------------------------------------------------------
left, right = st.columns(2)

with left:
    st.subheader("1 · Ever tried a cigarette — by gender")
    cross = weighted_cross_pct(filtered, SEX_COL, TRIED_COL)
    fig = px.bar(cross, x=SEX_COL, y="Percent", color=TRIED_COL, barmode="group",
                 color_discrete_sequence=COLORWAY, labels={SEX_COL: "Gender", TRIED_COL: "Ever Tried Cigarette",
                                                            "Percent": "Weighted Percent (%)"},
                 text_auto=".1f")
    fig.update_traces(textposition="outside", cliponaxis=False)
    chart_or_table(fig, cross, key="c1")

with right:
    st.subheader("2 · Age distribution")
    age_pct = weighted_value_counts_pct(filtered, AGE_COL)
    age_pct.columns = ["Age", "Percent"]
    fig2 = px.bar(age_pct.sort_values("Age"), x="Age", y="Percent", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig2.update_traces(textposition="outside", cliponaxis=False)
    fig2.update_layout(showlegend=False)
    chart_or_table(fig2, age_pct, key="c2")

left2, right2 = st.columns(2)
with left2:
    st.subheader("3 · Grade distribution")
    grade_pct = weighted_value_counts_pct(filtered, GRADE_COL)
    grade_pct.columns = ["Grade", "Percent"]
    fig3 = px.bar(grade_pct.sort_values("Grade"), x="Grade", y="Percent", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig3.update_traces(textposition="outside", cliponaxis=False)
    fig3.update_layout(showlegend=False)
    chart_or_table(fig3, grade_pct, key="c3")

with right2:
    st.subheader("4 · Smoking frequency (past 30 days)")
    freq_pct = weighted_value_counts_pct(filtered, CURRENT_COL)
    freq_pct.columns = ["Days Smoked", "Percent"]
    fig4 = px.bar(freq_pct, x="Days Smoked", y="Percent", color="Days Smoked", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig4.update_traces(textposition="outside", cliponaxis=False, textfont=dict(size=16, color="#1f2937"))
    fig4.update_layout(showlegend=False, uniformtext_minsize=14, uniformtext_mode="show", height=430,
                        margin=dict(t=40))
    chart_or_table(fig4, freq_pct, key="c4")

left3, right3 = st.columns(2)
with left3:
    st.subheader("5 · Noticed health warnings on packs")
    warn_pct = weighted_value_counts_pct(filtered, WARNING_COL)
    warn_pct.columns = ["Response", "Percent"]
    fig5 = themed_pie(warn_pct, names_col="Response", values_col="Percent", colorway=COLORWAY)
    chart_or_table(fig5, warn_pct, key="c5")

with right3:
    st.subheader("6 · Advertisement / promotion exposure")
    ad_pct = weighted_value_counts_pct(filtered, AD_COL)
    ad_pct.columns = ["Response", "Percent"]
    fig6 = px.bar(ad_pct, x="Response", y="Percent", color="Response", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig6.update_traces(textposition="outside", cliponaxis=False)
    fig6.update_layout(showlegend=False)
    chart_or_table(fig6, ad_pct, key="c6")

left4, right4 = st.columns(2)
with left4:
    st.subheader("7 · Saw smoking inside school")
    school_pct = weighted_value_counts_pct(filtered, SCHOOL_COL)
    school_pct.columns = ["Response", "Percent"]
    fig7 = px.bar(school_pct, x="Response", y="Percent", color="Response", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig7.update_traces(textposition="outside", cliponaxis=False)
    fig7.update_layout(showlegend=False)
    chart_or_table(fig7, school_pct, key="c7")

with right4:
    st.subheader("8 · Parents who smoke tobacco")
    parent_pct = weighted_value_counts_pct(filtered, PARENT_COL)
    parent_pct.columns = ["Response", "Percent"]
    fig8 = px.bar(parent_pct, x="Response", y="Percent", color="Response", color_discrete_sequence=COLORWAY,
                  text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
    fig8.update_traces(textposition="outside", cliponaxis=False)
    fig8.update_layout(showlegend=False)
    chart_or_table(fig8, parent_pct, key="c8")

st.subheader("9 · Closest friends who smoke tobacco")
friend_pct = weighted_value_counts_pct(filtered, FRIEND_COL)
friend_pct.columns = ["Response", "Percent"]
fig9 = px.bar(friend_pct, x="Response", y="Percent", color="Response", color_discrete_sequence=COLORWAY,
                text_auto=".1f", labels={"Percent": "Weighted Percent (%)"})
fig9.update_traces(textposition="outside", cliponaxis=False)
fig9.update_layout(showlegend=False)
chart_or_table(fig9, friend_pct, key="c9")

st.subheader("10 · Composition — gender × ever tried")
comp = weighted_cross_pct(filtered, SEX_COL, TRIED_COL)
fig10 = px.bar(comp, x=SEX_COL, y="Percent", color=TRIED_COL, barmode="stack", color_discrete_sequence=COLORWAY,
               labels={SEX_COL: "Gender", "Percent": "Weighted Percent (%)"}, text_auto=".1f")
fig10.update_traces(textposition="inside")
chart_or_table(fig10, comp, key="c10")

with st.expander("View filtered raw data"):
    st.dataframe(filtered, use_container_width=True)

page_footer("GYTS 2022 — row-level dataset, survey-weighted")
