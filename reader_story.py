"""Reader-first four-chapter narrative; annual source units remain distinct."""
from __future__ import annotations

import matplotlib.pyplot as plt
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
    """Static waterfall: components flow into the total, avoiding browser Plotly."""
    travel = values["travel"]
    other = values["other_services"]
    other_accounts = values["goods_and_income"]
    final = values["total"]
    parts = [travel, other, other_accounts]
    labels = ["Travel services" if not remove_travel else "Travel removed",
              "Other services", "Goods + income\n& transfers",
              "Total current\naccount"]
    colors = [TEAL if not remove_travel else "#B9C7CF",
              BLUE, GOLD, TEAL if final >= 0 else RED]
    fig, ax = plt.subplots(figsize=(10.2, 4.2), dpi=105)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    cumulative = 0.0
    heights = [0.0]
    for i, value in enumerate(parts):
        lower = min(cumulative, cumulative + value)
        ax.bar(i, abs(value), bottom=lower, width=0.64,
               color=colors[i], edgecolor="white", linewidth=1)
        cumulative += value
        heights.append(cumulative)
        if i < 2:
            ax.plot([i + .32, i + .68], [cumulative, cumulative],
                    color="#91A3AB", linestyle="--", linewidth=1.15)
        middle = lower + abs(value) / 2 if abs(value) > 2 else lower
        ax.annotate(f"{value:+.1f}", (i, middle),
                    ha="center", va="center" if abs(value) > 9 else "bottom",
                    xytext=(0, 0 if abs(value) > 9 else 5),
                    textcoords="offset points",
                    color="white" if abs(value) > 9 else INK,
                    fontsize=11, weight="bold")
    ax.bar(3, abs(final), bottom=min(0, final), width=0.64,
           color=colors[3], edgecolor="white")
    ax.annotate(f"€{final:+.1f}B", (3, final),
                ha="center", va="bottom" if final >= 0 else "top",
                xytext=(0, 6 if final >= 0 else -7),
                textcoords="offset points", weight="bold", fontsize=12, color=INK)
    ax.axhline(0, color="#607C8B", linewidth=1.3)
    ax.set_xticks(range(4), labels)
    ax.set_ylabel("Contribution to current-account balance (€ billion)", color=INK)
    ax.set_xlabel(f"Annual balances · {year}", color=INK, labelpad=9)
    ax.grid(axis="y", color=GRID, linewidth=.9)
    ax.set_axisbelow(True)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.tick_params(axis="both", colors=INK, labelsize=9, length=0)
    extreme = max(abs(v) for v in (travel, other, other_accounts, final))
    ax.set_ylim(min(-75, -extreme * 1.2), max(125, extreme * 1.25))
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
    remove = st.button(
        "Restore travel contribution" if st.session_state.get("remove_travel_bridge", False)
        else "Remove travel contribution",
        key="toggle_travel_bridge",
        help="Accounting illustration: subtracts observed net travel balance; not a forecast.",
    )
    if remove:
        st.session_state["remove_travel_bridge"] = not st.session_state.get(
            "remove_travel_bridge", False
        )
    removed = st.session_state.get("remove_travel_bridge", False)
    vals = financial_bridge(current[year], services[year], travel[year], removed)
    st.caption(f"Eurostat BPM6 · {year} annual values · € billions · "
               "select a different year range in the sidebar to change the year shown.")
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
    items = [("Nominal spending per visitor", nominal_change, BLUE)]
    if real_change:
        items.append(("Inflation-adjusted proxy", real_change, TEAL))
    visible = [(label, {y: values[y] for y in years if y in values}, color)
               for label, values, color in items]
    plot_line(years, visible, "Change vs 2019 (%)", "visitor-yield",
              percent=True)
    if latest in real_change:
        st.markdown(
            f"**Nominal spending per visitor is {nominal_change[latest]:+.1f}% "
            f"above 2019 in {latest}; the inflation-adjusted proxy is only "
            f"{real_change[latest]:+.1f}%.** General price inflation "
            "explains much of the nominal gain under this broad proxy."
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
