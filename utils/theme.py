"""
Per-page color themes + shared UI helpers (KPI cards, graph/table toggle,
top-N filter, Pakistan urban/rural map) so every page can look distinct
while staying consistent in structure.
"""

import textwrap

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# ONE UNIFIED BRAND IDENTITY. Every page now shares the same primary color
# and the same chart colorway, so the app reads as one consistent product
# rather than nine differently-branded pages. Each page keeps a small,
# distinct ACCENT (a tint/shade of the same green family) purely so KPI
# cards and small highlights still give a subtle per-page wayfinding cue —
# but charts, headers, and the overall "identity" color are shared.
# ---------------------------------------------------------------------------
BRAND_PRIMARY = "#1B4332"   # dark green — same primary used on the Overview page
BRAND_COLORWAY = ["#1B4332", "#40916C", "#74C69D", "#B08900", "#3D5A80", "#9D4EDD", "#9D0208"]

THEMES = {
    "gats_2014": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#2D6A4F",
        "colorway": BRAND_COLORWAY,
    },
    "gyts_2022": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#40916C",
        "colorway": BRAND_COLORWAY,
    },
    "gyts_2013": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#52B788",
        "colorway": BRAND_COLORWAY,
    },
    "gats_2024": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#1B4332",
        "colorway": BRAND_COLORWAY,
    },
    "kpi_2022": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#40916C",
        "colorway": BRAND_COLORWAY,
    },
    "trend": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#2D6A4F",
        "colorway": BRAND_COLORWAY,
    },
    "scorecard": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#52B788",
        "colorway": BRAND_COLORWAY,
    },
    "youth_trend": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#40916C",
        "colorway": BRAND_COLORWAY,
    },
    "methodology": {
        "name": "GTSS Pakistan",
        "primary": BRAND_PRIMARY,
        "accent": "#1B4332",
        "colorway": BRAND_COLORWAY,
    },
}


def apply_theme(theme_key: str) -> dict:
    """Return the theme dict for a page (also usable as fig.update_layout(colorway=...))."""
    return THEMES[theme_key]


# ---------------------------------------------------------------------------
# PAGE FOOTER — consistent data-source line at the bottom of every page.
# Small, but a flat list of pages with no consistent close feels like a
# collection of separate scripts rather than one finished product.
# ---------------------------------------------------------------------------
def page_footer(note: str | None = None) -> None:
    st.divider()
    line = "GTSS Pakistan — Global Tobacco Surveillance System, Pakistan"
    if note:
        line += f"  ·  {note}"
    st.caption(line)


# ---------------------------------------------------------------------------
# SIDEBAR FILTERS — consistent header + "is the view filtered?" status line.
# Every page used a different label/position for this, so a viewer landing
# mid-session on any page couldn't tell at a glance whether they were
# looking at the full dataset or a filtered slice.
# ---------------------------------------------------------------------------
def filter_header(icon: str = "🔎", label: str = "Filters") -> None:
    """Bolded micro-header every sidebar filter section starts with."""
    st.sidebar.markdown(f"**{icon} {label}**")


def filter_status(total: int, shown: int, n_active: int, noun: str = "indicators") -> None:
    """Caption placed in the page-title area (not just the sidebar) so the
    active-filter state is visible even if the sidebar is collapsed."""
    if total <= 0:
        return
    if n_active > 0:
        st.caption(
            f"👁️ Showing **{shown:,}** of **{total:,}** {noun} · "
            f"**{n_active}** filter{'s' if n_active != 1 else ''} active"
        )
    else:
        st.caption(f"👁️ Showing all **{total:,}** {noun} · no filters active")


def count_active(*flags: bool) -> int:
    """Count how many filter controls differ from their 'show everything' default."""
    return sum(1 for f in flags if f)


# ---------------------------------------------------------------------------
# RESPONSIVE / MOBILE FIXES — the app was only ever tested maximized on a
# desktop browser. Below ~900px, side-by-side st.columns(2) layouts and wide
# HTML scorecard tables are the two things most likely to break, so this
# stacks columns vertically and lets wide tables scroll horizontally instead
# of blowing out the page width.
# ---------------------------------------------------------------------------
def inject_responsive_css() -> None:
    st.markdown(
        """
        <style>
        @media (max-width: 900px) {
            div[data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
            }
            .why-matters-grid {
                grid-template-columns: repeat(2, 1fr) !important;
            }
            .insight-jump-grid {
                grid-template-columns: 1fr !important;
            }
        }
        @media (max-width: 600px) {
            .why-matters-grid {
                grid-template-columns: 1fr !important;
            }
        }
        .scroll-table-wrap {
            overflow-x: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------------------------
def kpi_row(items: list[dict], accent: str) -> None:
    """
    Render a row of styled KPI cards.
    items: [{"label": str, "value": str, "sub": str (optional)}]
    """
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.markdown(
                f"""
                <div style="
                    border-top: 4px solid {accent};
                    background: rgba(127,127,127,0.06);
                    border-radius: 8px;
                    padding: 14px 16px 12px 16px;
                    margin-bottom: 6px;
                ">
                    <div style="font-size:0.80rem; opacity:0.75; margin-bottom:4px;">
                        {item['label']}
                    </div>
                    <div style="font-size:1.65rem; font-weight:700; color:{accent};">
                        {item['value']}
                    </div>
                    {f"<div style='font-size:0.75rem; opacity:0.6;'>{item.get('sub','')}</div>" if item.get('sub') else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# GRAPH / TABLE TOGGLE
# ---------------------------------------------------------------------------
def chart_or_table(fig, table_df, key: str, height: int = 400) -> None:
    """Render a toggle between the Plotly chart and its underlying table."""
    mode = st.radio(
        "View",
        ["📈 Graph", "📋 Table"],
        horizontal=True,
        key=f"{key}_view",
        label_visibility="collapsed",
    )
    if mode == "📈 Graph":
        st.plotly_chart(fig, use_container_width=True, key=f"{key}_fig")
    else:
        st.dataframe(table_df, use_container_width=True, height=height, key=f"{key}_tbl")


# ---------------------------------------------------------------------------
# "HOW MANY TO SHOW" FILTER — controls label clutter on wide charts
# ---------------------------------------------------------------------------
def top_n_control(label: str, max_n: int, key: str, default: int | None = None) -> int:
    if max_n <= 1:
        return max_n
    default = default or min(10, max_n)
    return st.sidebar.slider(label, 1, max_n, default, key=key)


# ---------------------------------------------------------------------------
# LONG-LABEL BAR CHARTS
# The old approach (long indicator text rotated -35° along the x-axis)
# produced huge empty margins and labels that overlapped or ran off the
# chart. Horizontal bars read the full text left-to-right with zero
# rotation, so this is now the standard for any chart whose category
# labels are full survey-indicator sentences rather than short words.
# ---------------------------------------------------------------------------
def wrap_label(text: str, width: int = 30) -> str:
    """Wrap long text onto a few lines (HTML <br>) instead of one long run."""
    if not isinstance(text, str):
        return text
    lines = textwrap.wrap(text, width=width, break_long_words=False)
    return "<br>".join(lines) if lines else text


def wrap_labels(series, width: int = 30):
    return series.astype(str).apply(lambda t: wrap_label(t, width=width))


def bar_height(n_bars: int, per_bar: int = 34, base: int = 110, min_h: int = 260) -> int:
    """Auto-size chart height so horizontal bars never feel cramped."""
    return max(min_h, base + per_bar * max(n_bars, 1))


def hbar(
    df,
    label_col: str,
    value_col: str,
    color_col: str | None = None,
    colorway: list | None = None,
    barmode: str | None = None,
    text_auto=None,
    label_width: int = 30,
    height: int | None = None,
):
    """
    Build a clean horizontal bar chart for long-label indicator data.
    Pass in data already sorted the way you want it to read top-to-bottom
    (e.g. sort_values(..., ascending=False)) - this handles the display flip
    automatically so the first row lands at the top of the chart.
    """
    plot_df = df.copy()
    plot_df[label_col] = wrap_labels(plot_df[label_col], width=label_width)

    kwargs = {"orientation": "h"}
    per_bar_color = color_col is None
    if color_col:
        kwargs["color"] = color_col
        if barmode:
            kwargs["barmode"] = barmode
    else:
        # No explicit grouping column (e.g. "Group", "Category") — color
        # each bar individually so every label is visually distinguishable
        # instead of the whole chart rendering in one flat color.
        kwargs["color"] = label_col
    if colorway:
        kwargs["color_discrete_sequence"] = colorway
    if text_auto:
        kwargs["text_auto"] = text_auto

    fig = px.bar(plot_df, x=value_col, y=label_col, **kwargs)

    n_bars = plot_df[label_col].nunique()
    # Wrapped labels can run 1-4 lines; a fixed per-row height only works
    # for single-line labels, so scale row height by the tallest wrapped
    # label in this chart to stop adjacent rows' text from colliding.
    max_lines = int(plot_df[label_col].astype(str).str.count("<br>").max()) + 1 if len(plot_df) else 1
    per_bar = max(34, 17 * max_lines + 22)

    fig.update_yaxes(autorange="reversed", automargin=True, title="")
    fig.update_xaxes(title=value_col)
    fig.update_layout(
        height=height or bar_height(n_bars, per_bar=per_bar),
        margin=dict(l=10, r=20, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        showlegend=not per_bar_color,  # legend would just repeat the y-axis labels
    )
    if text_auto:
        fig.update_traces(textposition="outside", cliponaxis=False)
    return fig


# ---------------------------------------------------------------------------
# SLOPE CHART — the best chart type for "did it go up or down" across many
# indicators at once: one line per indicator running from the left value to
# the right value. Reads faster than a grouped bar for exactly this shape
# of data (a before/after comparison across many rows). Color only encodes
# DIRECTION (up vs down) — not whether that direction is good or bad for a
# given indicator, since that judgement is page-specific.
#
# Label decluttering: when several indicators land at similar values, their
# text labels would otherwise stack on top of each other and become
# unreadable. _declutter_y nudges label positions apart (never the actual
# marker/line, which always sits at the true value) so every label stays
# legible; exact numbers are still available via hover and the Table toggle.
# ---------------------------------------------------------------------------
def _declutter_y(values: list, min_gap: float) -> list:
    """Return label y-positions with at least min_gap between any two,
    preserving the original order and never moving a value's line/marker
    (only used for where the TEXT gets placed)."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    adjusted = [None] * len(values)
    prev = None
    for idx in order:
        v = values[idx]
        if prev is not None and v - prev < min_gap:
            v = prev + min_gap
        adjusted[idx] = v
        prev = v
    return adjusted


def slope_chart(
    df,
    label_col: str,
    left_col: str,
    right_col: str,
    left_title: str,
    right_title: str,
    up_color: str = "#B08900",
    down_color: str = "#2D6A4F",
    label_width: int = 30,
    height: int | None = None,
):
    plot_df = df.copy().sort_values(right_col, ascending=False).reset_index(drop=True)
    n = len(plot_df)
    if n == 0:
        fig = go.Figure()
        fig.update_layout(height=height or 200)
        return fig

    y_all = pd.concat([plot_df[left_col], plot_df[right_col]])
    y_min, y_max = y_all.min(), y_all.max()
    y_range = (y_max - y_min) or max(abs(y_max), 1)
    min_gap = (y_range / max(n, 1)) * 0.75
    label_y = _declutter_y(plot_df[left_col].tolist(), min_gap)

    fig = go.Figure()
    for i, row in plot_df.iterrows():
        went_up = row[right_col] >= row[left_col]
        color = up_color if went_up else down_color
        fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[row[left_col], row[right_col]],
                mode="lines+markers",
                line=dict(color=color, width=2.4),
                marker=dict(size=7, color=color),
                hovertext=f"{row[label_col]}<br>{left_title}: {row[left_col]:.1f} → {right_title}: {row[right_col]:.1f}",
                hoverinfo="text",
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=-0.05,
            y=label_y[i],
            text=f"{wrap_label(str(row[label_col]), width=label_width)}  ({row[left_col]:.1f}→{row[right_col]:.1f})",
            showarrow=False,
            xanchor="right",
            align="right",
            font=dict(size=10, color="#374151"),
        )

    fig.update_xaxes(
        range=[-0.75, 1.1],
        tickvals=[0, 1],
        ticktext=[f"<b>{left_title}</b>", f"<b>{right_title}</b>"],
        showgrid=False,
        zeroline=False,
    )
    fig.update_yaxes(title="Value (%)", showgrid=True, gridcolor="rgba(150,150,150,0.15)")
    fig.update_layout(
        height=height or max(360, 46 * n + 100),
        margin=dict(l=280, r=50, t=20, b=30),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---------------------------------------------------------------------------
# PIE / DONUT CHARTS
# Plotly's default legend placement borrows space from the plot area, so a
# handful of long response options (e.g. full survey answer text) can crush
# the pie down to a tiny circle in the corner. Pinning the pie to a fixed
# domain and wrapping/shrinking the legend keeps the pie a consistent,
# readable size no matter how long the category labels are.
# ---------------------------------------------------------------------------
def themed_pie(df, names_col: str, values_col: str, colorway: list | None = None,
                hole: float = 0.45, height: int = 380, legend_wrap: int = 24):
    plot_df = df.copy()
    plot_df[names_col] = wrap_labels(plot_df[names_col], width=legend_wrap)

    fig = px.pie(plot_df, names=names_col, values=values_col,
                 color_discrete_sequence=colorway, hole=hole)
    fig.update_traces(domain=dict(x=[0, 0.52], y=[0, 1]), textposition="inside", textinfo="percent")
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(x=0.58, y=0.5, xanchor="left", yanchor="middle", font=dict(size=11)),
    )
    return fig


# ---------------------------------------------------------------------------
# PAKISTAN URBAN / RURAL MAP
# Real Pakistan boundary (Plotly's bundled Natural Earth data via ISO-3
# choropleth) with two illustrative emoji-labeled markers for Urban vs
# Rural. The dataset only records Urban/Rural residence (no province or
# district), so this deliberately does NOT claim province-level precision
# — the two points are representative, not geocoded respondent locations.
# ---------------------------------------------------------------------------
def pakistan_urban_rural_map(urban_val: float, rural_val: float, metric_label: str, fill_color: str):
    fig = go.Figure()

    # Country outline
    fig.add_trace(
        go.Choropleth(
            locations=["PAK"],
            z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            marker_line_color=fill_color,
            marker_line_width=2.5,
            showscale=False,
            hoverinfo="skip",
        )
    )

    # Representative Urban point (Karachi) and Rural point (central Punjab)
    fig.add_trace(
        go.Scattergeo(
            lon=[67.01, 70.9],
            lat=[24.86, 30.3],
            text=["🏙️", "🌾"],
            mode="text+markers",
            marker=dict(
                size=[max(18, urban_val), max(18, rural_val)],
                color=fill_color,
                opacity=0.35,
            ),
            textfont=dict(size=28),
            hovertext=[
                f"Urban — {metric_label}: {urban_val:.1f}%",
                f"Rural — {metric_label}: {rural_val:.1f}%",
            ],
            hoverinfo="text",
        )
    )

    fig.update_geos(
        scope="asia",
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
        showcountries=True,
        countrycolor="rgba(150,150,150,0.3)",
    )
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
