"""
GTSS Pakistan — Tobacco Survey Dashboard
Methodology / Definitions — consolidates the honesty notes and modeling
decisions that were previously scattered as inline captions across the
Trend, KPI Scorecard, and Youth Trend pages, so they live in one place
instead of getting in the way on the data pages themselves.
"""

import streamlit as st

from utils.theme import apply_theme, page_footer, inject_responsive_css

st.set_page_config(page_title="GTSS Pakistan | Methodology", page_icon="📚", layout="wide")
inject_responsive_css()

THEME = apply_theme("methodology")

st.title("📚 Methodology & Definitions")
st.caption("Comparisons → Methodology & Definitions")
st.markdown(
    "How the RAG statuses, sparklines, and cross-survey comparisons on this "
    "dashboard are actually built — so a claim on any page can be traced "
    "back to a rule here, not just a caption you have to hunt for."
)

st.divider()

# ---------------------------------------------------------------------------
# 1 · RAG STATUS (Better / Similar / Worse)
# ---------------------------------------------------------------------------
st.subheader("1 · RAG status: Better / Similar / Worse")
st.markdown(
    """
Every indicator with a "direction that matters" (e.g. tobacco use should
fall, quit attempts should rise) is scored the same way on the **Trend**,
**KPI Scorecard**, and **Youth Trend** pages:

1. Take the raw change between the two survey years (e.g. 2014 → 2024).
2. Scale it against the larger of the two values, to get a **relative
   change** — a 2-point move on a 5% baseline matters more than the same
   2-point move on a 40% baseline.
3. Classify it:
"""
)

rag_col1, rag_col2, rag_col3 = st.columns(3)
with rag_col1:
    with st.container(border=True):
        st.markdown("🟢 **Better**")
        st.markdown("Relative change ≥ 2%, moving in the healthy direction for that indicator.")
with rag_col2:
    with st.container(border=True):
        st.markdown("🟡 **Similar**")
        st.markdown("Relative change < 2% either way — treated as noise, not a real shift.")
with rag_col3:
    with st.container(border=True):
        st.markdown("🔴 **Worse**")
        st.markdown("Relative change ≥ 2%, moving the wrong direction for that indicator.")

st.markdown(
    """
The "healthy direction" is indicator-specific and set once in a direction
map — e.g. current tobacco use and secondhand-smoke exposure should
**decrease**; quit attempts, quit advice, and warning-label awareness
should **increase**. Cost/spending indicators (PKR) have no healthy
direction, so they're marked **⚪ Context** instead of scored — see
section 3.

**Why 2%, and not something stricter?** With only two survey years and no
national benchmark to compare against (this data *is* the national
benchmark), a small fixed threshold does the job of separating real
movement from rounding/sampling noise without needing a formal
significance test the two data points can't actually support.
"""
)

st.divider()

# ---------------------------------------------------------------------------
# 2 · SPARKLINES
# ---------------------------------------------------------------------------
st.subheader("2 · Sparklines — why they're 2-point lines")
st.markdown(
    """
The KPI Scorecard and Youth Trend pages show a small trend line next to
each indicator. It's deliberately a straight **2-point line** — connecting
the earlier survey year directly to the later one — rather than a smoothed
curve implying data in between.

That's an honesty choice, not a limitation of the charting: these are two
discrete survey waves (2014 and 2024 for adults; 2013 and 2022 for youth),
not an annual time series. A curved or interpolated sparkline would imply
we know what happened in the years in between, which we don't.
"""
)

st.divider()

# ---------------------------------------------------------------------------
# 3 · PKR (COST/SPENDING) INDICATORS KEPT SEPARATE
# ---------------------------------------------------------------------------
st.subheader("3 · Why cost & spending (PKR) indicators are kept on their own scale")
st.markdown(
    """
Two indicators — **average cost of 20 manufactured cigarettes** and
**average monthly cigarette expenditure** — are measured in PKR
(thousands), not percentage points on a 0–100 scale like every other
indicator on this dashboard.

Mixing them in would cause two problems:

- **Chart axes**: plotted alongside percentage indicators, PKR values
  either squish the percentage lines flat or get squished themselves.
- **Ranking**: a "biggest change" Top-N selection would let a large PKR
  swing crowd out real percentage-point movements it isn't comparable to.

So these two indicators get their own dedicated "Cost & spending" section
on the Trend page, on their own axis, and are excluded from every
percentage-based ranking, RAG status, and Top-N control elsewhere. They're
still shown with a 2014→2024 slope, just not judged Better/Worse.
"""
)

st.divider()

# ---------------------------------------------------------------------------
# 4 · YOUTH ↔ ADULT INDICATOR MATCHING
# ---------------------------------------------------------------------------
st.subheader("4 · Matching youth (GYTS) and adult (GATS) indicators")
st.markdown(
    """
GYTS (youth) and GATS (adult) are two separate surveys with their own
question wording — there's no shared indicator ID to join them on. Where
a genuinely comparable theme exists in both (e.g. "current tobacco use",
"secondhand smoke at home"), the dashboard pairs them by:

1. Picking the **exact indicator name** from the adult (GATS) comparison
   data for one side of the pair.
2. Matching it to a youth (GYTS) row by searching the youth indicator
   descriptions for a **keyword phrase** that captures the same question
   (e.g. *"exposed to tobacco smoke at home in the past 7 days"*).
3. Only pairing a theme when **both** sides resolve to a real value in the
   underlying data — themes are looked up live, not hardcoded, so this
   stays correct if the source CSVs are ever refreshed.

This keyword-matching approach is intentionally conservative: a handful of
well-matched themes (current use, secondhand smoke, marketing exposure,
warning-label awareness, quit intentions) rather than a forced 1:1 mapping
of every indicator, since most questions in one survey simply don't have
a counterpart in the other.
"""
)

page_footer("Consolidates methodology notes previously shown inline on the Trend, KPI Scorecard, and Youth Trend pages")
