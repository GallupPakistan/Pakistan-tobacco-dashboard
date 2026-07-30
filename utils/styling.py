"""Shared color palette and small helpers so every page looks consistent."""

import streamlit as st

# Pulled from the GTSS Pakistan brand image (dark green / mint green)
DARK_GREEN = "#1B4332"
MID_GREEN = "#2D6A4F"
LIGHT_GREEN = "#74C69D"
PALE_GREEN = "#D8F3DC"
ACCENT = "#40916C"

CHART_COLORWAY = [DARK_GREEN, MID_GREEN, LIGHT_GREEN, ACCENT, "#95D5B2", "#081C15"]


def kpi_card(label: str, value: str, help_text: str = "") -> None:
    """Render a single KPI metric with consistent styling."""
    st.metric(label, value, help=help_text)


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()
