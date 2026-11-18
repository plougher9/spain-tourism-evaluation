"""Reader-first four-chapter narrative; annual source units remain distinct."""
from __future__ import annotations

import matplotlib.pyplot as plt
import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analysis_sections import (
    analyze, change_from_baseline, nominal_spending_per_visitor,
    real_spending_per_visitor, plot_line,
)
from story_sections import (
    annual_values, annual_totals, filtered_years,
    plot_chart, chart_style, render_recent_rolling_balance,
    BLUE, TEAL, GOLD, RED, INK, GRID,
)


def financial_bridge(current_account, services_balance, travel_balance, remove_travel=False):
    """Annual BPM6 balance components in €B, with an accounting-only removal."""
    other_services = services_balance - travel_balance
    goods_and_income = current_account - services_balance
    adjusted_total = current_account - travel_balance if remove_travel else current_account
    return {
        "travel": 0.0 if remove_travel else travel_balance,
        "other_services": other_services,
        "goods_and_income": goods_and_income,
        "observed_travel": travel_balance,
        "observed_total": current_account,
        "total": adjusted_total,
    }


def draw_financial_bridge(values, year, remove_travel):
    """Zero-based component bars and a distinct total, rendered server-side.

    Every bar begins at the zero axis. Positive contributors rise above
    zero, negative contributors fall below; no waterfall stacking.
    """
    travel = values["travel"]
    other = values["other_services"]
    other_accounts = values["goods_and_income"]
    final = values["total"]
    parts = [travel, other, other_accounts, final]
    labels = [
        "Travel services" if not remove_travel else "Travel removed",
        "Other services",
        "Goods, income\n& transfers",
        "Accounting\nremainder" if remove_travel else "Reported current\naccount",
    ]
    colors = [
        TEAL if not remove_travel else "#B9C7CF",
        BLUE, GOLD, TEAL if final >= 0 else RED,
    ]
    fig, ax = plt.subplots(figsize=(10.2, 4.3), dpi=105)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar(
        range(4), parts, bottom=0, width=0.62, color=colors,
        edgecolor="white", linewidth=1,
    )
    for bar, value in zip(bars, parts):
        x = bar.get_x() + bar.get_width() / 2
        if abs(value) >= 12:
            ax.annotate(
                f"€{value:+.1f}B", (x, value / 2),
                ha="center", va="center", weight="bold", fontsize=10,
                color="white",
            )
        else:
            ax.annotate(
                f"€{value:+.1f}B", (x, value),
                xytext=(0, 7 if value >= 0 else -9),
                textcoords="offset points", ha="center",
                va="bottom" if value >= 0 else "top",
                weight="bold", fontsize=10, color=INK,
            )
    ax.axhline(0, color="#607C8B", linewidth=1.3)
    ax.set_xticks(range(4), labels)
    ax.set_ylabel("Annual balance (€ billion)", color=INK)
    ax.set_xlabel(f"Balance-of-payments components · {year}", color=INK, labelpad=9)
    ax.grid(axis="y", color=GRID, linewidth=.9)
    ax.set_axisbelow(True)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.tick_params(axis="both", colors=INK, labelsize=9, length=0)
    low = min(0, *parts)
    high = max(0, *parts)
    space = max(12, (high - low) * .13)
    ax.set_ylim(low - space, high + space)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_financial_section(travel, services, current, start_year, end_year):
    st.markdown("### 01 · How important is tourism to Spain's finances?")
    common = sorted(y for y in set(travel) & set(services) & set(current)
                    if start_year <= y <= end_year)
    if not common:
        st.info("No common annual travel, services and current-account observations "
                "within the selected years.")
        return
    year = common[-1]
    vals = financial_bridge(current[year], services[year], travel[year])
    def flip_travel_bridge():
        st.session_state["remove_travel_bridge"] = not st.session_state.get(
            "remove_travel_bridge", False
        )

    st.button(
        "Restore travel contribution" if st.session_state.get("remove_travel_bridge", False)
        else "Remove travel contribution",
        key="toggle_travel_bridge",
        on_click=flip_travel_bridge,
        help="Accounting illustration: subtracts observed net travel balance; not a forecast.",
    )
    removed = st.session_state.get("remove_travel_bridge", False)
    vals = financial_bridge(current[year], services[year], travel[year], removed)
    st.caption(f"Eurostat BPM6 · {year} annual values · € billions · "
               "Each component is shown independently from zero. "
               "Select a different year range in the sidebar to change the year shown.")
    draw_financial_bridge(vals, year, removed)
    if removed:
        st.markdown(
            f"**With the reported €{travel[year]:.1f}B net travel surplus removed, "
            f"the accounting remainder becomes €{vals['total']:+.1f}B.** "
            "This is why net travel matters to the external balance. "
            "Other accounts are held unchanged for illustration only."
        )
    else:
        st.markdown(
            f"**Spain's €{travel[year]:.1f}B net travel surplus helped support "
            f"a €{current[year]:.1f}B current-account balance in {year}.** "
            "Use **Remove travel contribution** to see how much of that reported "
            "balance is attributable to net travel in accounting terms."
        )
    st.markdown(
        f"**The math ({year}):** €{travel[year]:.2f}B travel + "
        f"€{vals['other_services']:+.2f}B other services + "
        f"€{vals['goods_and_income']:+.2f}B goods/income/transfers "
        f"= **€{current[year]:+.2f}B reported current account**. "
        f"Subtracting net travel: €{current[year]:.2f}B − "
        f"€{travel[year]:.2f}B = **€{current[year]-travel[year]:+.2f}B**."
    )
    st.caption(
        "**Important:** this removes the *net travel-services balance*, not "
        "all tourism economic activity or gross visitor receipts. The resulting "
        "negative figure is an accounting remainder, **not** an economic forecast. "
        "Sources: [Eurostat travel](https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table) "
        "and [annual balance of payments](https://ec.europa.eu/eurostat/databrowser/view/bop_c6_a/default/table)."
    )
    with st.expander("Explore the annual trend behind these balances"):
        residual = {y: current[y] - travel[y] for y in common}
        plot_line(common, [
            ("Travel-services balance", travel, TEAL),
            ("Reported current account", current, BLUE),
            ("Current account minus net travel", residual, GOLD),
        ], "Annual balance (€ billion)", "balance-history")
        st.caption("The three lines compare historical balances; the bridge "
                   "above is the primary explanation of how they add up.")


def render_dependence_section(gdp, start_year, end_year):
    st.markdown("### 02 · Is Spain becoming more dependent on tourism?")
    years = sorted(y for y in gdp if start_year <= y <= end_year)
    if not years:
        st.info("No annual tourism-GDP contribution observations in the selected years.")
        return
    plot_line(years, [("Tourism share of GDP", gdp, TEAL)],
              "Tourism contribution (% of GDP)", "tourism-gdp")
    if 2019 in gdp and 2024 in gdp:
        st.markdown(
            f"**The evidence does not establish continuously rising GDP dependence.** "
            f"The reported share was {gdp[2019]:.1f}% in 2019 and "
            f"{gdp[2024]:.1f}% in 2024. "
            "That does not mean financial exposure or concentration risk "
            "is unchanged."
        )
    st.caption(
        "INE Tourism Satellite Account / DCE89; latest reported 2024. "
        "**Series breaks:** 2015 Base 2010; 2016–2020 Revision 2019; "
        "2021 onward Revision 2024. Cross-revision comparisons need caution. "
        "[Official INE series](https://www.ine.es/consul/serie.do?L=1&d=true&s=DCE89)"
    )


def inflation_chart_data(years, nominal_change, real_change, hicp):
    """Values for a shared-year hover, all in % relative to 2019."""
    if 2019 not in hicp or hicp[2019] <= 0:
        return pd.DataFrame(columns=["Year", "Nominal", "Inflation", "Adjusted"])
    return pd.DataFrame([
        {
            "Year": str(y),
            "Nominal": nominal_change.get(y),
            "Inflation": 100 * (hicp[y] / hicp[2019] - 1) if y in hicp else None,
            "Adjusted": real_change.get(y),
        }
        for y in years
    ])


def draw_inflation_chart(data, view):
    """Lightweight Altair chart, with all three values visible on year hover.

    Only Part 3B is client-interactive. Other story charts remain server-side.
    """
    series_names = {
        "Nominal": "Nominal spending per visitor",
        "Inflation": "Cumulative Spanish consumer inflation",
        "Adjusted": "HICP-adjusted spending per visitor",
    }
    visible = {
        "Compare all": list(series_names),
        "Nominal only": ["Nominal"],
        "Inflation-adjusted only": ["Adjusted"],
    }[view]
    chart_data = data.melt(
        id_vars=["Year"], value_vars=visible,
        var_name="Measure", value_name="Change",
    ).dropna(subset=["Change"])
    chart_data["Measure"] = chart_data["Measure"].map(series_names)
    palette = {
        "Nominal spending per visitor": BLUE,
        "Cumulative Spanish consumer inflation": GOLD,
        "HICP-adjusted spending per visitor": TEAL,
    }
    year_values = data["Year"].tolist()
    base = alt.Chart(chart_data).encode(
        x=alt.X("Year:O", sort=year_values, title="Calendar year"),
        y=alt.Y(
            "Change:Q",
            title="Cumulative change from 2019 (%)",
            axis=alt.Axis(format="+.0f"),
            scale=alt.Scale(zero=False),
        ),
        color=alt.Color(
            "Measure:N",
            scale=alt.Scale(domain=list(palette), range=list(palette.values())),
            legend=alt.Legend(title=None, orient="top"),
        ),
    )
    lines = base.mark_line(strokeWidth=3, point=alt.OverlayMarkDef(size=55))
    baseline = alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(
        color="#7E929D", strokeDash=[4, 4], strokeWidth=1
    ).encode(y="zero:Q")
    # One vertical selection target per calendar year; tooltip shows *all*
    # values even when the toggle shows just one line.
    hover_data = data.copy()
    for col in ("Nominal", "Inflation", "Adjusted"):
        hover_data[col] = pd.to_numeric(hover_data[col], errors="coerce")
    nearest = alt.selection_point(
        fields=["Year"], nearest=True, on="pointerover", empty=False,
    )
    targets = alt.Chart(hover_data).mark_point(
        size=90, opacity=0.0,
    ).encode(
        x=alt.X("Year:O", sort=year_values),
        tooltip=[
            alt.Tooltip("Year:O", title="Year"),
            alt.Tooltip("Nominal:Q", title="Nominal / visitor", format="+.1f"),
            alt.Tooltip("Inflation:Q", title="Cumulative HICP", format="+.1f"),
            alt.Tooltip("Adjusted:Q", title="Adjusted / visitor", format="+.1f"),
        ],
    ).add_params(nearest)
    highlight = alt.Chart(hover_data).mark_rule(
        color="#8C9DA5", strokeWidth=1.2
    ).encode(
        x=alt.X("Year:O", sort=year_values),
        opacity=alt.condition(nearest, alt.value(.75), alt.value(0)),
    ).transform_filter(nearest)
    chart = alt.layer(baseline, lines, targets, highlight).properties(
        height=325
    ).configure_view(strokeWidth=0).configure_axis(
        labelColor=INK, titleColor=INK, gridColor=GRID
    )
    st.altair_chart(chart, use_container_width=True)


def render_yield_section(spending, arrivals, hicp, start_year, end_year):
    st.markdown("### 03 · Is Spain earning more per visitor after inflation?")
    nominal = nominal_spending_per_visitor(spending, arrivals)
    real = real_spending_per_visitor(spending, arrivals, hicp)
    years = sorted(y for y in nominal if start_year <= y <= end_year)
    if not years or 2019 not in nominal:
        st.info("No full-year international tourist arrivals and spending in "
                "the selected range. Complete annual totals begin in 2016.")
        return
    latest = years[-1]
    nominal_change = change_from_baseline(nominal)
    real_change = change_from_baseline(real)

    # Exhibit A: volume versus nominal receipts, indexed to a consistent
    # 2019 reference. These are overlapping lines, not additive/stacked amounts.
    volume_index = {y: 100.0 * arrivals[y] / arrivals[2019]
                    for y in years if y in arrivals}
    spending_index = {y: 100.0 * spending[y] / spending[2019]
                      for y in years if y in spending}
    st.markdown("**A · Have tourism receipts grown faster than visitor numbers?**")
    plot_line(
        years,
        [("International visitor arrivals", volume_index, BLUE),
         ("Nominal tourist spending", spending_index, TEAL)],
        "Annual index (2019 = 100)", "arrivals-versus-spending",
    )
    visitor_growth = volume_index[latest] - 100
    receipts_growth = spending_index[latest] - 100
    st.markdown(
        f"**Reading A ({latest} versus 2019):** visitor arrivals "
        f"**{visitor_growth:+.1f}%**, while nominal visitor spending "
        f"**{receipts_growth:+.1f}%**. Spending has grown faster than "
        "visitor numbers; that gap alone does not tell us whether "
        "visitors are spending more in real terms."
    )
    st.caption(
        "INE FRONTUR arrivals and INE EGATUR nominal spending; "
        "full-year totals only. Both series use 2019 = 100, allowing "
        "their growth paths to be compared—not summed."
    )
    with st.expander(f"Show the math for visitors versus spending ({latest})"):
        st.markdown(
            "**Both lines are indexed to 2019 = 100.** "
            "An index measures each series' growth against its own 2019 total; "
            "the lines share a baseline but have different original units."
        )
        st.markdown(
            f"**Visitor arrivals (INE FRONTUR):** "
            f"{latest} {arrivals[latest]:.3f} million ÷ "
            f"2019 {arrivals[2019]:.3f} million × 100 "
            f"= **{volume_index[latest]:.1f} index points** "
            f"({visitor_growth:+.1f}% versus 2019)."
        )
        st.markdown(
            f"**Total nominal visitor spending (INE EGATUR):** "
            f"{latest} €{spending[latest]:.3f} billion ÷ "
            f"2019 €{spending[2019]:.3f} billion × 100 "
            f"= **{spending_index[latest]:.1f} index points** "
            f"({receipts_growth:+.1f}% versus 2019)."
        )
        st.markdown(
            f"**Why the lines diverge:** annual nominal spending is "
            f"**visitor arrivals × nominal spending per visitor**. "
            f"Therefore the growth factor in spending per visitor is "
            f"({spending_index[latest]:.2f} ÷ "
            f"{volume_index[latest]:.2f} − 1) × 100 "
            f"= **{nominal_change[latest]:+.1f}%**. "
            "The index-point gap between the two lines is not itself "
            "the percentage change in spending per visitor."
        )
        st.caption(
            "Calculated from unrounded annual source totals; intermediate "
            "numbers are rounded for display. All annual totals require "
            "12 months. This first comparison is nominal: it does not "
            "adjust for price changes."
        )

    st.markdown("**B · Does higher spending per visitor hold up after inflation?**")
    st.markdown(
        "**Nominal spending per visitor** tells us how many euros the "
        "average international visitor spent in the prices of that year. "
        "A rise can reflect a more valuable visitor mix, longer stays, "
        "more purchases, **or simply higher prices**. It therefore "
        "cannot, on its own, establish more real tourism value. "
        "**Inflation-adjusted spending per visitor** translates those "
        "euros into 2019 purchasing-power terms using Spain's overall "
        "consumer price index (HICP). This is an approximation of "
        "purchasing power, not a tourism-specific price measure."
    )
    view = st.radio(
        "Choose the inflation comparison",
        ["Compare all", "Nominal only", "Inflation-adjusted only"],
        index=0, horizontal=True, key="inflation_comparison_view",
        help="Nominal is in the year's euros; adjusted removes broad Spanish "
             "consumer-price changes. Compare all includes cumulative HICP.",
    )
    chart_data = inflation_chart_data(years, nominal_change, real_change, hicp)
    if chart_data["Nominal"].notna().any():
        draw_inflation_chart(chart_data, view)
        st.caption(
            "Hover over any year marker to see nominal spending-per-visitor "
            "growth, cumulative Spanish HICP inflation, and adjusted growth "
            "together. Values are percentages relative to 2019 (0%), "
            "not percentage-point contributions that can simply be added."
        )
    else:
        st.info("Not enough annual observations to show the inflation comparison.")
    if latest in real_change:
        price_change = 100 * (hicp[latest] / hicp[2019] - 1)
        st.markdown(
            f"**Reading B ({latest} versus 2019):** nominal spending per "
            f"visitor increased **{nominal_change[latest]:+.1f}%**, "
            f"but after adjusting for general Spanish consumer inflation, "
            f"the increase is **{real_change[latest]:+.1f}%**. "
            f"Over the same period, Spain's all-items HICP rose "
            f"**{price_change:+.1f}%**. The difference tells us that "
            "much of the growth in euros per visitor is absorbed by the "
            "change in general purchasing power—not that visitors "
            "necessarily bought much more tourism in real terms."
        )
        st.markdown(
            f"**How to interpret the lines:** the nominal line measures "
            f"growth in euros actually spent per visitor; the adjusted line "
            f"measures what those euros would be worth at 2019 consumer "
            f"prices. They are related multiplicatively: "
            f"**(1 + {nominal_change[latest]/100:.3f}) = "
            f"(1 + {real_change[latest]/100:.3f}) × "
            f"(1 + {price_change/100:.3f})**, up to rounding. "
            "It would be misleading to subtract the two percentages "
            "and call that an exact share caused by inflation."
        )
        st.caption(
            "**Limit:** HICP tracks prices paid by consumers in Spain, "
            "not the specific basket bought by international visitors. "
            "This comparison does not establish the cause of higher "
            "tourist spending, changes in trip length, or tourism value added."
        )
    else:
        st.markdown(
            f"Nominal spending per visitor was {nominal_change[latest]:+.1f}% "
            f"relative to 2019 in {latest}; inflation-adjusted data are unavailable."
        )
    with st.expander(f"Show the math behind the {latest} percentages"):
        st.markdown(
            f"**Spending per visitor = annual EGATUR spending / annual FRONTUR arrivals.** "
            f"2019: €{spending[2019]:.2f}B ÷ {arrivals[2019]:.2f}M "
            f"= **€{nominal[2019]:,.2f}**. "
            f"{latest}: €{spending[latest]:.2f}B ÷ {arrivals[latest]:.2f}M "
            f"= **€{nominal[latest]:,.2f}**."
        )
        st.markdown(
            f"**Nominal change vs 2019:** "
            f"(€{nominal[latest]:,.2f} / €{nominal[2019]:,.2f} − 1) × 100 "
            f"= **{nominal_change[latest]:+.1f}%**."
        )
        if latest in real and latest in hicp and 2019 in hicp:
            st.markdown(
                f"**Consumer-price proxy in 2019 euros:** "
                f"€{nominal[latest]:,.2f} × ({hicp[2019]:.2f} / "
                f"{hicp[latest]:.2f}) = €{real[latest]:,.2f}. "
                f"**Adjusted change:** (€{real[latest]:,.2f} / "
                f"€{real[2019]:,.2f} − 1) × 100 "
                f"= **{real_change[latest]:+.1f}%**."
            )
        st.caption("Intermediate figures are rounded; calculations use full precision.")
    st.caption(
        "Full annual EGATUR/FRONTUR records begin in 2016. 2019 remains "
        "the fixed 0% reference even when outside the selected range. "
        "Spain-wide HICP is used as a general inflation proxy, not a tourism-specific "
        "deflator. [Eurostat HICP](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table)."
    )


def render_shock_section(travel, spending, arrivals, start_year, end_year):
    st.markdown("### 04 · What happens when conditions deteriorate?")
    years = filtered_years(travel, start_year, end_year)
    if not years:
        st.info("No annual travel-surplus figures in the selected range.")
        return
    fig = go.Figure(go.Bar(
        x=years, y=[travel[y] for y in years],
        marker_color=[RED if y == 2020 else TEAL for y in years],
    ))
    chart_style(fig, ytitle="Travel balance (€ billion)")
    fig.update_layout(showlegend=False)
    plot_chart(fig, "travel-surplus-shock")
    if 2019 in travel and 2020 in travel:
        loss = travel[2019] - travel[2020]
        st.markdown(
            f"**2020 — external demand shock:** Spain's annual travel surplus "
            f"fell from €{travel[2019]:.1f}B to €{travel[2020]:.1f}B "
            f"(a €{loss:.1f}B decline). This demonstrates exposure to "
            "international travel disruption."
        )
    if 2021 in travel and 2022 in travel:
        st.markdown(
            f"**2022 — a contrasting shock:** As energy-import costs rose, "
            f"the travel surplus recovered from €{travel[2021]:.1f}B "
            f"in 2021 to €{travel[2022]:.1f}B in 2022. "
            "Tourism provided support alongside an adverse energy-price shock; "
            "the chart alone does not quantify an offset or establish causation."
        )
    st.caption(
        "Source: Eurostat BPM6 annual travel-services balance; energy-crisis "
        "context: [IMF Spain Article IV](https://www.imf.org/en/publications/cr/issues/2023/01/19/spain-2022-article-iv-consultation-press-release-staff-report-and-statement-by-the-528338)."
    )


def render_exploration(travel, rolling_balance, start_year, end_year):
    st.markdown("### Explore further")
    with st.expander("Explore a hypothetical change in the travel-services surplus"):
        years = filtered_years(travel, start_year, end_year)
        if years:
            col1, col2 = st.columns([1, 2])
            with col1:
                year = st.selectbox("Baseline travel-surplus year", years,
                                    index=len(years)-1, key="scenario_year")
                reduction = st.slider(
                    "Hypothetical reduction in net travel surplus",
                    0, 100, 25, 5, format="%d%%", key="scenario_shock"
                )
            stressed = travel[year] * (1 - reduction / 100)
            with col2:
                st.metric("Reported travel surplus", f"€{travel[year]:.1f}B")
                st.metric("Hypothetical stressed surplus", f"€{stressed:.1f}B")
            st.caption(
                f"Arithmetic only: €{travel[year]:.2f}B × (1 − "
                f"{reduction}%) = €{stressed:.2f}B. "
                "This is not a GDP or current-account forecast."
            )
        else:
            st.info("No travel-surplus data in the selected period.")
    with st.expander("Recent Banco de España rolling travel surplus"):
        render_recent_rolling_balance(rolling_balance)


def render_reader_story(series, analysis_data, start_year, end_year, rolling_balance=None):
    spending, arrivals, hicp, current, services, travel = analyze(series, analysis_data)
    gdp = annual_values(series.get("tourism_gdp", {}))

    st.markdown("### The central finding")
    if 2025 in current and 2025 in travel:
        st.markdown(
            f"**Tourism helps support Spain's external financial position:** "
            f"the €{travel[2025]:.1f}B annual net travel surplus exceeded "
            f"the €{current[2025]:.1f}B overall current-account surplus "
            "in 2025. Yet higher nominal tourist spending should not be "
            "mistaken for the same increase in inflation-adjusted value. "
            "Whether dependence or vulnerability is increasing remains unproven."
        )
        st.caption("Headline benchmark uses 2025 annual Eurostat values. "
                   "Chapters below respond to the selected year range.")
    render_financial_section(travel, services, current, start_year, end_year)
    render_dependence_section(gdp, start_year, end_year)
    render_yield_section(spending, arrivals, hicp, start_year, end_year)
    render_shock_section(travel, spending, arrivals, start_year, end_year)

    st.markdown("### Overall analysis · What can we conclude?")
    st.markdown(
        "**Financial strength:** The net travel surplus makes a large positive "
        "accounting contribution to Spain's current account. "
        "**Economic value:** Nominal spending per visitor has grown considerably "
        "faster than a Spain-wide inflation-adjusted proxy. "
        "**Dependence:** The reported tourism share of GDP does not establish "
        "a continuously increasing share, and statistical revisions limit "
        "exact long-term comparisons. "
        "**Risk:** COVID demonstrates sensitivity to travel restrictions; "
        "the 2022 rebound during an energy shock illustrates resilience "
        "under a different stress. These findings are descriptive, not causal."
    )
    render_exploration(travel, rolling_balance, start_year, end_year)
