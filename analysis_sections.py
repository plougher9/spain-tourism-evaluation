"""Analytical hypotheses: tourism yield, inflation, and external balances."""
from __future__ import annotations
from matplotlib import pyplot as plt
import streamlit as st
from story_sections import annual_totals, annual_values, TEAL, BLUE, GOLD, INK, GRID


def analyze(series, extras):
    spending = annual_totals(series.get("spending", {}))
    arrivals = annual_totals(series.get("arrivals", {}))
    extra = extras.get("series", {}) if isinstance(extras, dict) else {}
    hicp = annual_values(extra.get("hicp", {}))
    current = annual_values(extra.get("current_account_eur", {}))
    services = annual_values(extra.get("services_balance_eur", {}))
    travel = annual_values(series.get("travel_balance", {}))
    return spending, arrivals, hicp, current, services, travel


def real_spending_per_visitor(spending, arrivals, hicp, base_year=2019):
    """Approximate € per visitor, adjusted by Spain-wide consumer inflation."""
    if base_year not in hicp or hicp[base_year] <= 0:
        return {}
    return {
        y: (spending[y] * 1_000_000_000 / (arrivals[y] * 1_000_000))
           * hicp[base_year] / hicp[y]
        for y in sorted(set(spending) & set(arrivals) & set(hicp))
        if arrivals[y] > 0 and hicp[y] > 0
    }


def nominal_spending_per_visitor(spending, arrivals):
    return {y: spending[y] * 1000 / arrivals[y]
            for y in sorted(set(spending) & set(arrivals))
            if arrivals[y] > 0}


def change_from_baseline(values, base_year=2019):
    """Percentage change from a fixed baseline, even if baseline is off-chart."""
    base = values.get(base_year)
    if base is None or base <= 0:
        return {}
    return {year: 100.0 * (value / base - 1.0)
            for year, value in values.items()}


def plot_line(years, series_items, ylabel, key, percent=False):
    """Small server-side image; never loads Plotly JavaScript in the browser."""
    fig, ax = plt.subplots(figsize=(10.2, 3.4), dpi=105)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for label, values, color in series_items:
        ax.plot(years, [values.get(y, float("nan")) for y in years],
                color=color, linewidth=2.5, marker="o", markersize=4.3,
                label=label)
    if percent:
        from matplotlib.ticker import FuncFormatter
        ax.axhline(0, color="#687A86", linewidth=1.3, linestyle="--")
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, position: f"{value:+.0f}%"))
        # Show exact endpoint figures, so quoted growth is visible on the plot.
        last_year = years[-1]
        for i, (label, values, color) in enumerate(series_items):
            if last_year in values:
                point = values[last_year]
                ax.annotate(
                    f"{point:+.1f}%",
                    xy=(last_year, point),
                    xytext=(8, 10 if i == 0 else -14),
                    textcoords="offset points",
                    color=color, weight="bold", fontsize=10
                )
        ax.margins(y=0.19)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_xlabel("Calendar year (annual observations)", color=INK, labelpad=9)
    ax.tick_params(colors=INK, labelsize=9, length=0)
    if key == "tourism-gdp":
        # Single series already identified by its title and vertical axis.
        # The old legend covered the first visible point (often 2019).
        # Add nearly a full year of horizontal room on both sides.
        ax.set_xlim(years[0] - 0.8, years[-1] + 0.8)
    else:
        ax.legend(frameon=False, loc="upper left", fontsize=9)
        ax.margins(x=0.075)
    ax.set_xticks(years)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_analysis(series, analysis_data, start_year, end_year):
    spending, arrivals, hicp, current, services, travel = analyze(
        series, analysis_data
    )
    nominal = nominal_spending_per_visitor(spending, arrivals)
    real = real_spending_per_visitor(spending, arrivals, hicp)
    st.markdown("### What does the evidence actually say?")
    if all(yr in nominal and yr in real for yr in (2019, 2025)) and (
        2025 in travel and 2025 in current
    ):
        nominal_change = 100 * (nominal[2025] / nominal[2019] - 1)
        real_change = 100 * (real[2025] / real[2019] - 1)
        other_balance = current[2025] - travel[2025]
        st.markdown(
            '<div class="narrative-lead"><strong>'
            'Spain earns substantially more from international tourism, '
            'but stronger nominal receipts are not the same as stronger '
            'inflation-adjusted returns.</strong><br>'
            f'From 2019 to 2025, nominal spending per visitor rose '
            f'{nominal_change:.1f}%, versus {real_change:.1f}% under a '
            'general consumer-price adjustment. In 2025, net travel '
            f'contributed €{travel[2025]:.1f}B to a total current-account '
            f'balance of €{current[2025]:.1f}B; the other current-account '
            f'components summed to €{other_balance:.1f}B. '
            'These are historical observations, not proof that dependence '
            'has increased or that tourism alone creates resilience.'
            '</div>',
            unsafe_allow_html=True
        )
        st.caption(
            "Executive benchmark: 2019–2025 complete-year observations; "
            "fixed for comparability even if the sidebar displays fewer years. "
            "Inflation adjustment uses Spain-wide HICP, not a tourism deflator."
        )
    st.markdown(
        "The charts test two linked questions: is the growth in tourism "
        "receipts still meaningful after inflation, and how important is "
        "net travel to Spain's observed external financial balance?"
    )
    st.caption(
        f"Showing available annual observations for {start_year}–{end_year}. "
        "Hypothesis 1 shows percentage changes relative to the fixed "
        "2019 baseline (0%), even when 2019 falls outside the visible range."
    )

    st.markdown("#### Hypothesis 1 · Is tourism earning more per visitor after inflation?")
    years = [y for y in sorted(nominal) if start_year <= y <= end_year]
    if years and 2019 in nominal:
        latest = years[-1]
        nominal_growth_series = change_from_baseline(nominal)
        nominal_visible = {y: nominal_growth_series[y] for y in years}
        cols = st.columns(3)
        with cols[0]:
            st.metric("2019 baseline, nominal / visitor", f"€{nominal[2019]:,.0f}")
            st.caption("Fixed reference, independent of date selection")
        with cols[1]:
            st.metric(f"{latest} nominal / visitor", f"€{nominal[latest]:,.0f}",
                      f"{nominal_visible[latest]:+.1f}% vs 2019")
        with cols[2]:
            if latest in real and 2019 in real:
                change = 100 * real[latest] / real[2019] - 100
                st.metric(f"{latest} HICP-adjusted proxy",
                          f"€{real[latest]:,.0f}",
                          f"{change:+.1f}% vs 2019")
            else:
                st.metric(f"{latest} HICP-adjusted proxy", "Unavailable")
        real_growth_series = change_from_baseline(real)
        real_visible = {
            y: real_growth_series[y] for y in years
            if y in real_growth_series
        }
        plot_items = [("Nominal spending per visitor", nominal_visible, BLUE)]
        if real_visible:
            plot_items.append(
                ("Inflation-adjusted spending per visitor", real_visible, TEAL)
            )
        plot_line(
            years, plot_items, "Change vs 2019 (%)", "visitor-yield",
            percent=True
        )
        st.caption(
            f"Full-year annual visitor averages available for "
            f"{min(nominal)}–{max(nominal)}. "
            "The arrivals/spending sources begin in September 2015, so "
            "**2015 is excluded from annual per-visitor calculations**; "
            "incomplete 2026 is also excluded. "
            "Spending per visitor = annual INE EGATUR spending / "
            "annual INE FRONTUR arrivals. "
            "HICP-adjusted proxy = nominal spending per visitor × "
            "Spain all-items annual HICP(2019) / HICP(year). "
            "**This is not an official tourism-specific real-spending "
            "measure.** "
            "[Eurostat annual HICP]"
            "(https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table)"
        )
        if latest in real and 2019 in real and latest in hicp and 2019 in hicp:
            with st.expander(f"Show the math behind the {latest} percentages"):
                st.markdown(
                    f"**1. Spending per visitor** (annual spending ÷ arrivals): "
                    f"2019 = €{spending[2019]:.2f}B ÷ {arrivals[2019]:.2f}M "
                    f"= **€{nominal[2019]:,.2f} per visitor**. "
                    f"{latest} = €{spending[latest]:.2f}B ÷ "
                    f"{arrivals[latest]:.2f}M = "
                    f"**€{nominal[latest]:,.2f} per visitor**."
                )
                st.markdown(
                    f"**2. Nominal growth vs 2019:** "
                    f"(€{nominal[latest]:,.2f} ÷ €{nominal[2019]:,.2f} − 1) "
                    f"× 100 = **{nominal_visible[latest]:+.1f}%**."
                )
                st.markdown(
                    f"**3. Consumer-price adjustment:** Spain's annual "
                    f"all-items HICP is {hicp[2019]:.2f} in 2019 and "
                    f"{hicp[latest]:.2f} in {latest}. "
                    f"€{nominal[latest]:,.2f} × "
                    f"({hicp[2019]:.2f} ÷ {hicp[latest]:.2f}) = "
                    f"**€{real[latest]:,.2f} in 2019 euros**."
                )
                st.markdown(
                    f"**4. Inflation-adjusted growth vs 2019:** "
                    f"(€{real[latest]:,.2f} ÷ €{real[2019]:,.2f} − 1) "
                    f"× 100 = **{real_visible[latest]:+.1f}%**."
                )
                st.caption(
                    "Arithmetic uses unrounded data; displayed intermediate "
                    "amounts are rounded. General consumer inflation is a "
                    "proxy, not a tourism-specific price deflator."
                )
        if 2019 in nominal and latest in nominal and latest in real:
            nominal_growth = 100 * (nominal[latest] / nominal[2019] - 1)
            adjusted_growth = 100 * (real[latest] / real[2019] - 1)
            st.markdown(
                f"**Reading the chart:** Compared with 2019, nominal spending "
                f"per visitor is **{nominal_growth:+.1f}%** in {latest}, but "
                f"only **{adjusted_growth:+.1f}%** after adjusting for "
                f"Spanish consumer inflation. Most of the nominal increase "
                f"is associated with higher prices under this proxy, "
                f"rather than a comparable increase in purchasing-power-adjusted "
                f"spending per visitor."
            )
        if not real_visible:
            st.info("Official HICP observations are unavailable for the selected years.")
    else:
        st.info(
            f"No complete annual spending-and-arrivals observations "
            f"for {start_year}–{end_year}. Available complete years: "
            f"{min(nominal) if nominal else 'none'}–"
            f"{max(nominal) if nominal else 'none'}."
        )

    st.markdown("#### Hypothesis 2 · How much does travel contribute to the external balance?")
    common = sorted(
        y for y in (set(travel) & set(services) & set(current))
        if start_year <= y <= end_year
    )
    if common:
        years = common
        if years:
            residual = {y: current[y]-travel[y] for y in years}
            plot_line(
                years,
                [("Travel-services surplus", travel, TEAL),
                 ("Total current-account balance", current, BLUE),
                 ("Current account excluding net travel", residual, GOLD)],
                "€ billion · annual", "travel-ca-comparison"
            )
            y = years[-1]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{y} travel surplus", f"€{travel[y]:,.1f}B")
            with col2:
                st.metric(f"{y} total current account", f"€{current[y]:,.1f}B")
            with col3:
                st.metric(f"{y} excluding net travel", f"€{residual[y]:,.1f}B")
            st.markdown(
                f"**Reading the chart:** Net travel services contributed "
                f"€{travel[y]:,.1f}B in {y} versus a total current-account "
                f"balance of €{current[y]:,.1f}B. Removing the reported travel "
                f"balance arithmetically leaves **€{residual[y]:,.1f}B** from "
                f"all other current-account components combined. This shows "
                f"how important travel is to the observed external balance, "
                f"without estimating what would happen if tourism disappeared."
            )
            if y in services and services[y] > 0:
                share = 100 * travel[y] / services[y]
                st.caption(
                    f"In {y}, net travel was **{share:.1f}% of the overall "
                    "services surplus**. This is a ratio of net balances, "
                    "not a share of gross exports, and may exceed 100% if "
                    "other services are in deficit."
                )
            st.caption(
                "**Accounting identity, not a causal counterfactual:** "
                "'current account excluding net travel' means total "
                "current-account balance minus the reported travel-services "
                "balance for the same year and unit. It does NOT estimate "
                "what the current account would have been if tourism vanished. "
                "The current account also includes goods, other services, "
                "primary income and secondary income. Source: "
                "[Eurostat balance of payments]"
                "(https://ec.europa.eu/eurostat/databrowser/view/bop_c6_a/default/table)."
            )
    else:
        st.info(
            f"No matching annual travel-services and current-account "
            f"observations for {start_year}–{end_year}. "
            "Verify the supplemental Eurostat series if this persists."
        )

    with st.expander("Supplemental source freshness and methodological limits"):
        state = analysis_data if isinstance(analysis_data, dict) else {}
        st.caption("Last successful complete supplemental refresh (UTC): "
                   + str(state.get("last_successful_refresh_utc") or "Not yet available"))
        for name, entry in extra_series(state).items():
            obs = entry.get("observations", [])
            st.write(f"{name}: latest {obs[-1]['period'] if obs else 'unavailable'} · "
                     f"{entry.get('source', '')}")
        for name, err in state.get("errors", {}).items():
            st.warning(f"{name}: {err}")
        st.caption(
            "Analysis uses a supplementary official-source refresh distinct "
            "from the six original assignment indicators. Missing source "
            "data are not estimated or backfilled."
        )


def extra_series(data):
    return data.get("series", {}) if isinstance(data, dict) else {}
