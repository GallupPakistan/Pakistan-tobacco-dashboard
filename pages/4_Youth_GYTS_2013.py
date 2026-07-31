import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_loader import load_gyts_2013
from utils.theme import (
    apply_theme, kpi_row, chart_or_table, top_n_control, page_footer,
    filter_header, inject_responsive_css,
)

st.set_page_config(page_title="GYTS 2013 | Youth", page_icon="📈", layout="wide")
inject_responsive_css()

THEME = apply_theme("gyts_2013")
COLORWAY = THEME["colorway"]
ACCENT = THEME["accent"]

st.title("📈 Youth — GYTS 2013 (Aggregated)")
st.caption(
    "Only percentage-level data is available for this round — row-level microdata "
    f"was not obtained, so this page shows fixed snapshots rather than live filters. Theme: {THEME['name']}"
)

df = load_gyts_2013()

# Questions whose answer options have a natural ascending order (age, grade)
# rather than being ranked by percentage. Sorting these by Weighted Percent
# instead scrambles the axis (e.g. 13, 14, 15, 12, 16, 17+, 11), so they get
# an explicit ascending order applied instead.
ANSWER_ORDER = {
    "How old are you?": [
        "11 years old or younger", "12 years old", "13 years old", "14 years old",
        "15 years old", "16 years old", "17 years old or older",
    ],
    "In what grade/form are you?": ["7th", "8th", "9th", "10th"],
}

def q_chart(question_text: str, chart_key: str, top_n: int | None = None):
    subset = df[df["Survey Question"] == question_text].copy()
    order = ANSWER_ORDER.get(question_text)
    if order:
        subset["Answer Option"] = pd.Categorical(subset["Answer Option"], categories=order, ordered=True)
        subset = subset.sort_values("Answer Option")
    else:
        subset = subset.sort_values("Weighted Percent", ascending=False)
    if top_n:
        subset = subset.head(top_n)
    fig = px.bar(subset, x="Answer Option", y="Weighted Percent", color="Answer Option",
                 text_auto=".1f", color_discrete_sequence=COLORWAY,
                 category_orders={"Answer Option": order} if order else None)
    # No legend here — color already repeats what's on the x-axis, and showing
    # both was crowding the plot and causing the rotated tick labels to overlap.
    fig.update_layout(showlegend=False, yaxis_title="Weighted Percent (%)",
                       xaxis_tickangle=-30, margin=dict(b=120))
    fig.update_xaxes(automargin=True)
    return fig, subset

# ---------------------------------------------------------------------------
# KPI ROW — headline figures pulled straight from key rows
# ---------------------------------------------------------------------------
def pct_for(question, answer):
    row = df[(df["Survey Question"] == question) & (df["Answer Option"] == answer)]
    return row["Weighted Percent"].iloc[0] if not row.empty else None

tried_pct = pct_for(
    "Have you ever tried or experimented with cigarette smoking, even one or two puffs? Original Analysis Unweighted Unweighted",
    "Yes",
)
school_pct = pct_for(
    "During the past 30 days, did you see anyone smoke inside the school building or outside on school property?",
    "Yes",
)

kpi_row(
    [
        {"label": "Survey questions available", "value": f"{df['Survey Question'].nunique()}"},
        {"label": "Ever tried a cigarette", "value": f"{tried_pct:.1f}%" if tried_pct is not None else "—"},
        {"label": "Saw smoking inside school", "value": f"{school_pct:.1f}%" if school_pct is not None else "—"},
        {"label": "Total data rows", "value": f"{len(df):,}"},
    ],
    accent=ACCENT,
)

st.divider()

# ---------------------------------------------------------------------------
# 1. INTERACTIVE — user picks any question, with a "how many answers" filter
# ---------------------------------------------------------------------------
st.subheader("1 · Explore any survey question")
filter_header(label="Chart 1 control")
questions = sorted(df["Survey Question"].dropna().unique().tolist())
question_sel = st.sidebar.selectbox("Survey question (chart 1)", questions)
n_answers = top_n_control(
    "How many answer options to show (chart 1)",
    df[df["Survey Question"] == question_sel]["Answer Option"].nunique(),
    key="q1_n",
    default=min(5, df[df["Survey Question"] == question_sel]["Answer Option"].nunique()),
)
st.caption(f"📝 Survey question: *{question_sel}*")
fig1, subset1 = q_chart(question_sel, "c1", top_n=n_answers)
chart_or_table(fig1, subset1, key="c1")

# ---------------------------------------------------------------------------
# 2-10. NINE FIXED, CURATED QUESTIONS
# ---------------------------------------------------------------------------
FIXED_QUESTIONS = [
    ("2 · Age distribution", "How old are you?"),
    ("3 · Gender distribution", "What is your sex?"),
    ("4 · Grade distribution", "In what grade/form are you?"),
    ("5 · Ever tried cigarette smoking",
     "Have you ever tried or experimented with cigarette smoking, even one or two puffs? Original Analysis Unweighted Unweighted"),
    ("6 · Smoking in past 30 days",
     "During the past 30 days, on how many days did you smoke cigarettes?"),
    ("7 · Anyone smoked at home (past 7 days)",
     "During the past 7 days, on how many days has anyone smoked inside your home, in your presence?"),
    ("8 · Saw smoking inside school",
     "During the past 30 days, did you see anyone smoke inside the school building or outside on school property?"),
    ("9 · Favor banning smoking in enclosed public places",
     "Are you in favor of banning smoking inside enclosed public places (such as schools, hospitals, airport lounges, shops, restaurants, shopping malls, movie theaters, public transport)?"),
    ("10 · Refused cigarette sale due to age",
     "During the past 30 days, did anyone refuse to sell you cigarettes because of your age?"),
]

pairs = [FIXED_QUESTIONS[i:i + 2] for i in range(0, len(FIXED_QUESTIONS), 2)]
for pair in pairs:
    cols = st.columns(len(pair))
    for col, (title, q) in zip(cols, pair):
        with col:
            st.subheader(title)
            if q in df["Survey Question"].values:
                # Show the exact survey question wording so the chart isn't
                # just a short paraphrase — the "Original Analysis Unweighted
                # Unweighted" suffix on one question is a dataset artifact,
                # not part of the actual wording, so it's trimmed for display.
                display_q = q.replace(" Original Analysis Unweighted Unweighted", "")
                st.caption(f"📝 {display_q}")
                fig, subset = q_chart(q, title)
                chart_or_table(fig, subset, key=title)
            else:
                st.info("Question not found in this dataset round.")

st.divider()
st.subheader("Browse full 2013 dataset")
st.dataframe(df, use_container_width=True, height=400)

page_footer("GYTS 2013 — aggregated official indicators")
