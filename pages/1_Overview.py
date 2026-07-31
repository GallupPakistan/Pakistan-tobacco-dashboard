"""
GTSS Pakistan — Tobacco Survey Dashboard
Overview page.
"""

import streamlit as st
from pathlib import Path

from utils.data_loader import load_comparison, load_gyts_2022_derived
from utils.styling import DARK_GREEN, MID_GREEN, PALE_GREEN, ACCENT
from utils.theme import page_footer, inject_responsive_css

st.set_page_config(
    page_title="GTSS Pakistan | Overview",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_responsive_css()

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

# ---------------------------------------------------------------------------
# GLOBAL SPACING FIXES — tighten up the default Streamlit block gaps so
# headings, dividers, and columns sit closer together and line up cleanly.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        hr { margin: 1.25rem 0 !important; }
        div[data-testid="column"] { display: flex; flex-direction: column; }
        /* Single combined heading — tight spacing, but line-height stays
           high enough that dots/ascenders (e.g. the "i" in Monitoring)
           never get clipped. */
        .hero-title {
            margin: 0 0 0.9rem 0 !important;
            padding: 0 !important;
            line-height: 1.3 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🚭 GTSS Pakistan")
    st.caption("Global Tobacco Survey — Pakistan")
    st.divider()
    st.markdown(
        """
        **Use the pages above** to explore each survey:

        - 📊 Adults — GATS 2014 *(row-level)*
        - 🎓 Youth — GYTS 2022 *(row-level)*
        - 📈 Youth — GYTS 2013 *(aggregated)*
        - 🚬 Adults — GATS 2024 *(aggregated)*
        - ⭐ KPI Cards — GYTS 2022 Derived
        - 🔀 Trend — 2014 vs 2024
        """
    )
    st.divider()
    st.caption("Data source: Global Tobacco Surveillance System (GTSS), Pakistan")

# ---------------------------------------------------------------------------
# HERO — text on the left, small boxed cover image on the right, vertically
# centered against the heading so the two columns line up.
# ---------------------------------------------------------------------------
hero_left, hero_right = st.columns([1.4, 1], gap="medium")

with hero_left:
    st.markdown(
        f"""
        <h1 class="hero-title">
            <span style="color:{DARK_GREEN};">Monitoring Tobacco Use</span><br>
            <span style="color:{MID_GREEN};">Improving Public Health</span>
        </h1>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
The **Global Tobacco Survey (GTS)** is the global standard used to monitor tobacco use
and track key tobacco-control indicators over time. In Pakistan, this program runs as
two linked surveys:

- **GATS (Global Adult Tobacco Survey)** — a nationally representative, household-based
  survey of adults aged 15 and older. Pakistan has rounds from **2014** and **2024**.
- **GYTS (Global Youth Tobacco Survey)** — a school-based survey of students, typically
  aged 13–15. Pakistan has rounds from **2013** and **2022**.

This dashboard brings together **six datasets** from those surveys — two full row-level
datasets (for live filtering by age, gender, and region) and four pre-aggregated /
official indicator datasets (for years where only summary percentages are public) — into
one place so trends in tobacco use, exposure, and awareness can be explored interactively.
        """
    )

with hero_right:
    cover_path = ASSETS_DIR / "cover.png"
    if cover_path.exists():
        st.image(str(cover_path), width=380)
        st.caption("GTSS Pakistan — Global Tobacco Survey")
    else:
        st.warning("Cover image not found in assets/cover.png")

st.divider()

# ---------------------------------------------------------------------------
# JUMP TO INSIGHTS — Overview's real job with 9 pages behind it isn't to be
# a static intro, it's triage: point at what's most urgent and deep-link
# straight to it. All three cards are computed live from the same data the
# Trend page uses, not hardcoded, so they stay correct if the source CSVs
# ever change.
# ---------------------------------------------------------------------------
st.markdown(f"<h3 style='color:{MID_GREEN}; margin-bottom:0.75rem;'>🧭 Jump to insights</h3>", unsafe_allow_html=True)

TREND_PAGE = "pages/11_Adults_Compare_2014_vs_2024.py"

_direction_map = {
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

_scored = load_comparison()
_scored = _scored[_scored["Group"].str.strip().str.lower() == "overall"].copy()
_scored["Change (pts)"] = (_scored["2024 Value"] - _scored["2014 Value"]).round(1)
_scored["Direction"] = _scored["Indicator"].map(_direction_map)
_scored = _scored.dropna(subset=["Direction"])
_scale = _scored[["2014 Value", "2024 Value"]].abs().max(axis=1).clip(lower=1)
_good_sign = _scored["Direction"].map({"decrease": -1, "increase": 1})
_scored["RelChange"] = (_scored["Change (pts)"] * _good_sign) / _scale

most_improved = _scored.sort_values("RelChange", ascending=False).iloc[0] if len(_scored) else None
most_concerning = _scored.sort_values("RelChange", ascending=True).iloc[0] if len(_scored) else None

# Youth (GYTS 2022) vs Adult (GATS 2024) — same paired themes shown in
# Trend page section 11, reused here to find the single largest gap.
_gyts_derived = load_gyts_2022_derived()
_adult_overall = load_comparison()
_adult_overall = _adult_overall[_adult_overall["Group"].str.strip().str.lower() == "overall"]

_youth_adult_themes = [
    ("Current any tobacco use", "Current tobacco use", "currently use any tobacco products"),
    ("Current tobacco smoking", "Current tobacco smoking", "currently smoke any tobacco products"),
    ("Secondhand smoke exposure — Home (7 days)", "SHS exposure: Home", "exposed to tobacco smoke at home in the past 7 days"),
    ("Secondhand smoke exposure — School", "SHS exposure: Schools", "smoking inside the school building or outside on school property"),
    ("Noticed tobacco ads/promos in stores", "Noticed tobacco ads/promos in stores", "tobacco marketing at points of sale in the past 30 days"),
    ("Noticed health warnings on cigarette packages", "Noticed health warnings on packages", "noticed health warnings on cigarette packages in the past 30 days"),
    ("Considered quitting because of warnings", "Considered quitting due to warnings", "thought about quitting smoking in the past 30 days because of health warnings"),
]

def _adult_val(indicator_name):
    row = _adult_overall[_adult_overall["Indicator"] == indicator_name]
    return float(row["2024 Value"].iloc[0]) if len(row) else None

def _youth_val(keyword):
    match = _gyts_derived[_gyts_derived["Indicator Description"].str.contains(keyword, case=False, na=False, regex=False)]
    return float(match["Weighted Percent"].iloc[0]) if len(match) else None

_ya_gaps = []
for theme, adult_ind, youth_kw in _youth_adult_themes:
    a_val, y_val = _adult_val(adult_ind), _youth_val(youth_kw)
    if a_val is not None and y_val is not None:
        _ya_gaps.append((theme, a_val, y_val, abs(a_val - y_val)))

biggest_gap = max(_ya_gaps, key=lambda t: t[3]) if _ya_gaps else None

insight_col1, insight_col2, insight_col3 = st.columns(3)

with insight_col1:
    with st.container(border=True):
        st.markdown("**📈 Most improved**")
        if most_improved is not None:
            st.markdown(
                f"**{most_improved['Indicator']}** moved "
                f"{abs(most_improved['Change (pts)']):.1f} pts in the healthy direction "
                f"since 2014 ({most_improved['2014 Value']:.1f}% → {most_improved['2024 Value']:.1f}%)."
            )
        else:
            st.markdown("No data available.")
        st.page_link(TREND_PAGE, label="Explore in Compare →", icon="🆚")

with insight_col2:
    with st.container(border=True):
        st.markdown("**⚠️ Most concerning**")
        if most_concerning is not None:
            st.markdown(
                f"**{most_concerning['Indicator']}** moved "
                f"{abs(most_concerning['Change (pts)']):.1f} pts the wrong way "
                f"since 2014 ({most_concerning['2014 Value']:.1f}% → {most_concerning['2024 Value']:.1f}%)."
            )
        else:
            st.markdown("No data available.")
        st.page_link(TREND_PAGE, label="Explore in Compare →", icon="🆚")

with insight_col3:
    with st.container(border=True):
        st.markdown("**🧒 Youth vs Adult gap**")
        if biggest_gap is not None:
            theme, a_val, y_val, gap = biggest_gap
            st.markdown(
                f"**{theme}** shows the widest gap: adults {a_val:.1f}% vs "
                f"youth {y_val:.1f}% ({gap:.1f} pts apart)."
            )
        else:
            st.markdown("No matching youth/adult themes found.")
        st.page_link(TREND_PAGE, label="Explore in Compare →", icon="🆚")

st.divider()

# ---------------------------------------------------------------------------
# WHY IT MATTERS — equal-height cards with emojis, laid out in a CSS grid so
# all four line up regardless of text length.
# ---------------------------------------------------------------------------
st.markdown(f"<h3 style='color:{MID_GREEN}; margin-bottom:0.75rem;'>Why it matters</h3>", unsafe_allow_html=True)

why_it_matters = [
    ("👥", "Representative Data", "Population-based data for all adults (15+ years)."),
    ("🚬", "Key Indicators", "Tobacco use, secondhand smoke exposure, cessation, and more."),
    ("🎯", "Informed Action", "Evidence to strengthen tobacco control policies and programs."),
    ("🌱", "Healthier Future", "Working together for a tobacco-free Pakistan."),
]

cards_html = "".join(
    f"""
    <div style="
        background:{PALE_GREEN};
        border-left:4px solid {ACCENT};
        border-radius:8px;
        padding:1rem 1.1rem;
        height:100%;
        box-sizing:border-box;
    ">
        <div style="font-size:1.6rem; line-height:1; margin-bottom:0.4rem;">{emoji}</div>
        <div style="font-weight:700; color:{DARK_GREEN}; margin-bottom:0.3rem;">{title}</div>
        <div style="font-size:0.85rem; color:{DARK_GREEN}; opacity:0.85; line-height:1.35;">{desc}</div>
    </div>
    """
    for emoji, title, desc in why_it_matters
)

st.markdown(
    f"""
    <div class="why-matters-grid" style="display:grid; grid-template-columns:repeat(4, 1fr); gap:1rem; align-items:stretch;">
        {cards_html}
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY — one auto-generated sentence that states the overall
# story before showing the raw numbers: is tobacco use trending down, and
# where's the biggest remaining concern. Computed live from the same
# comparison data used everywhere else, not hardcoded.
# ---------------------------------------------------------------------------
df_cmp = load_comparison()
overall_all = df_cmp[df_cmp["Group"].str.strip().str.lower() == "overall"].copy()
overall_all["Change (pts)"] = (overall_all["2024 Value"] - overall_all["2014 Value"]).round(1)

use_row = overall_all[overall_all["Indicator"].str.contains("Current tobacco use", case=False, na=False)]
biggest_increase = overall_all.loc[overall_all["Change (pts)"].idxmax()] if len(overall_all) else None

if len(use_row):
    u = use_row.iloc[0]
    use_delta = round(u["2024 Value"] - u["2014 Value"], 1)
    direction_word = "declined" if use_delta < 0 else ("risen" if use_delta > 0 else "held steady")
    summary_html = (
        f"Since 2014, overall tobacco use has <b>{direction_word} by {abs(use_delta):.1f} points</b> "
        f"(from {u['2014 Value']:.1f}% to {u['2024 Value']:.1f}%)"
    )
    if biggest_increase is not None:
        summary_html += (
            f", while <b>{biggest_increase['Indicator']}</b> shows the largest increase since 2014 "
            f"(+{biggest_increase['Change (pts)']:.1f} pts)."
        )
    else:
        summary_html += "."

    st.markdown(
        f"""
        <div style="
            background:{PALE_GREEN};
            border-left:4px solid {DARK_GREEN};
            border-radius:8px;
            padding:0.9rem 1.1rem;
            margin-bottom:1.2rem;
            font-size:1.02rem;
            color:{DARK_GREEN};
            line-height:1.5;
        ">
            {summary_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(f"<h3 style='color:{DARK_GREEN}; margin-bottom:0.75rem;'>Headline numbers: 2014 vs 2024</h3>", unsafe_allow_html=True)

overall = overall_all

# Prioritize a "current tobacco use" style row if present, else just use the first overall row
headline_row = overall[overall["Indicator"].str.contains("Current tobacco use", case=False, na=False)]
if headline_row.empty:
    headline_row = overall.head(1)

if not headline_row.empty:
    row = headline_row.iloc[0]
    v2014 = row["2014 Value"]
    v2024 = row["2024 Value"]
    delta = round(v2024 - v2014, 1)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(f"{row['Indicator']} — 2014", f"{v2014}%")
    with c2:
        st.metric(f"{row['Indicator']} — 2024", f"{v2024}%", delta=f"{delta} pts")
    with c3:
        st.metric("Datasets in this dashboard", "6")

st.caption(
    "Explore the full breakdown, filters, and charts for each survey year using the "
    "pages listed in the sidebar."
)

page_footer("Datasets: GATS 2014 & 2024, GYTS 2013 & 2022")
