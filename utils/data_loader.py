"""
Central data-loading module for the Pakistan Tobacco Survey Dashboard.
Every page imports from here so each CSV is only ever read (and cached) once.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_data(show_spinner="Loading GATS 2014 adult data...")
def load_gats_2014() -> pd.DataFrame:
    """Row-level GATS 2014 adult survey data (7,831 respondents)."""
    return pd.read_csv(DATA_DIR / "gats_2014_LABELED.csv", low_memory=False)


@st.cache_data(show_spinner="Loading GYTS 2022 youth data...")
def load_gyts_2022() -> pd.DataFrame:
    """Row-level GYTS 2022 youth survey data (9,783 students)."""
    return pd.read_csv(DATA_DIR / "gyts_2022_LABELED.csv", low_memory=False)


@st.cache_data(show_spinner="Loading GYTS 2013 aggregated data...")
def load_gyts_2013() -> pd.DataFrame:
    """Pre-aggregated GYTS 2013 youth percentages (no row-level data available)."""
    return pd.read_csv(DATA_DIR / "gyts_2013_aggregated_LABELED.csv")


@st.cache_data(show_spinner="Loading GATS 2024 key indicators...")
def load_gats_2024() -> pd.DataFrame:
    """Pre-aggregated GATS 2024 adult key indicators (row-level not yet public)."""
    return pd.read_csv(DATA_DIR / "gats_2024_key_indicators_LABELED.csv")


@st.cache_data(show_spinner="Loading GYTS 2022 derived indicators...")
def load_gyts_2022_derived() -> pd.DataFrame:
    """78 official CDC-calculated indicators for GYTS 2022."""
    return pd.read_csv(DATA_DIR / "gyts_2022_derived_indicators_LABELED.csv")


@st.cache_data(show_spinner="Loading 2014 vs 2024 comparison data...")
def load_comparison() -> pd.DataFrame:
    """Side-by-side GATS 2014 vs 2024 trend indicators."""
    return pd.read_csv(DATA_DIR / "gats_2014_vs_2024_comparison_LABELED.csv")
