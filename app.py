"""
GTSS Pakistan — Tobacco Survey Dashboard
Entry point. This file only wires up navigation — no page content lives here.
All page content lives in pages/*.py.

Filenames use a plain numeric prefix only (1_, 2_, ...) to control order —
no emoji in the filename, so the folder zips/compresses without issue.
Each page's icon is set here via icon=, and independently inside that
page's own st.set_page_config(page_icon=...) for the browser tab.

Pages are grouped into labeled sections (Overview / Adult Surveys / Youth
Surveys / Comparisons) so the sidebar reads as 4 organized groups instead
of one flat list of 9 pages.

Run with:  streamlit run app.py
"""

import streamlit as st

overview = st.Page("pages/1_Overview.py", title="Overview", icon="🏠", default=True)
gats_2014 = st.Page("pages/2_Adults_GATS_2014.py", title="Adults GATS 2014", icon="📊")
gats_2024 = st.Page("pages/5_Adults_GATS_2024.py", title="Adults GATS 2024", icon="🚬")
gyts_2022 = st.Page("pages/3_Youth_GYTS_2022.py", title="Youth GYTS 2022", icon="🎓")
gyts_2013 = st.Page("pages/4_Youth_GYTS_2013.py", title="Youth GYTS 2013", icon="📈")
kpi_cards = st.Page("pages/6_KPI_Cards_GYTS_2022.py", title="KPI Cards GYTS 2022", icon="⭐")
trend = st.Page("pages/7_Trend_2014_vs_2024.py", title="Trend 2014 vs 2024", icon="🔀")
scorecard = st.Page("pages/8_KPI_Scorecard.py", title="KPI Scorecard", icon="📋")
youth_trend = st.Page("pages/9_Youth_Trend_2013_vs_2022.py", title="Youth Trend 2013 vs 2022", icon="🧒")
methodology = st.Page("pages/10_Methodology.py", title="Methodology & Definitions", icon="📚")

pg = st.navigation(
    {
        "": [overview],
        "Adult Surveys": [gats_2014, gats_2024],
        "Youth Surveys": [gyts_2022, gyts_2013, kpi_cards, youth_trend],
        "Comparisons": [trend, scorecard, methodology],
    }
)
pg.run()
