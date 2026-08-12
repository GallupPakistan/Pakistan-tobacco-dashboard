# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY — one auto-generated sentence that states the overall
# story before showing the raw numbers: is tobacco use trending down, and
# where's the biggest remaining concern. Computed live from the same
# comparison data used everywhere else, not hardcoded.
#
# IMPORTANT: the comparison dataset mixes indicators measured in different
# units — most are percentages, but two are Pakistani Rupees (average cost
# of cigarettes, monthly expenditure). Comparing their raw "change" values
# on one scale is meaningless (a PKR change of +1589.2 will always dwarf a
# percentage-point change of -30), so currency indicators must be excluded
# before finding the "biggest increase" among percentage indicators.
# ---------------------------------------------------------------------------
CURRENCY_INDICATORS = [
    "Avg cost of 20 manufactured cigarettes (PKR, inflation-adj.)",
    "Avg monthly cigarette expenditure (PKR, inflation-adj.)",
]

df_cmp = load_comparison()
overall_all = df_cmp[df_cmp["Group"].str.strip().str.lower() == "overall"].copy()
overall_all["Change (pts)"] = (overall_all["2024 Value"] - overall_all["2014 Value"]).round(1)

# percentage-point-only subset used for "biggest increase" ranking
overall_pct_only = overall_all[~overall_all["Indicator"].isin(CURRENCY_INDICATORS)]

use_row = overall_all[overall_all["Indicator"].str.contains("Current tobacco use", case=False, na=False)]
biggest_increase = (
    overall_pct_only.loc[overall_pct_only["Change (pts)"].idxmax()]
    if len(overall_pct_only) else None
)

if len(use_row):
    u = use_row.iloc[0]
    use_delta = round(u["2024 Value"] - u["2014 Value"], 1)
    direction_word = "declined" if use_delta < 0 else ("risen" if use_delta > 0 else "held steady")
    summary_html = (
        f"Since 2014, overall tobacco use has <b>{direction_word} by {abs(use_delta):.1f} points</b> "
        f"(from {u['2014 Value']:.1f}% to {u['2024 Value']:.1f}%)"
    )
    if biggest_increase is not None and biggest_increase["Change (pts)"] > 0:
        summary_html += (
            f", while <b>{biggest_increase['Indicator']}</b> shows the largest increase since 2014 "
            f"(+{biggest_increase['Change (pts)']:.1f} pts)."
        )
    elif biggest_increase is not None:
        # nothing actually increased among the percentage indicators — say so plainly
        summary_html += ", and every other tracked indicator moved in the healthy direction too."
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
