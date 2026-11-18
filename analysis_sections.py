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


def plot_line(years, series_items, ylabel, key, percent=False):
    """Small server-side image; never loads Plotly JavaScript in the browser."""
    fig, ax = plt.subplots(figsize=(10.2, 3.4), dpi=105)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    for label, values, color in series_items:
        ax.plot(years, [values.get(y, float("nan")) for y in years],
                color=color, linewidth=2.5, marker="o", markersize=4.3,
                label=label)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_xlabel("Calendar year (annual observations)", color=INK, labelpad=9)
    ax.tick_params(colors=INK, labelsize=9, length=0)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_xticks(years)
    ax.margins(x=0.035)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_analysis(series, analysis_data, start_year, end_year):
    spending, arrivals, hicp, current, services, travel = analyze(
        series, analysis_data
    )
    nominal = nominal_spending_per_visitor(spending, arrivals)
    real = real_spending_per_visitor(spending, arrivals, hicp)
    st.markdown("### Beyond the shock: is tourism delivering better returns?")
    st.markdown(
        "Two hypotheses distinguish a rising visitor count from genuine "
        "economic value, and a large travel surplus from its role in Spain's "
        "overall external accounts."
    )
    st.caption(
        f"Showing available annual observations for {start_year}–{end_year}. "
        "Spending-per-visitor indices retain 2019 = 100 as the fixed "
        "reference, even when that baseline falls outside the visible range."
    )

    st.markdown("#### Hypothesis 1 · Is tourism earning more per visitor after inflation?")
    years = [y for y in sorted(nominal) if start_year <= y <= end_year]
    if years and 2019 in nominal:
        latest = years[-1]
        nominal_index = {y: 100 * nominal[y] / nominal[2019] for y in years}
        cols = st.columns(3)
        with cols[0]:
            st.metric("2019 baseline, nominal / visitor", f"€{nominal[2019]:,.0f}")
            st.caption("Fixed reference, independent of date selection")
        with cols[1]:
            st.metric(f"{latest} nominal / visitor", f"€{nominal[latest]:,.0f}",
                      f"{nominal_index[latest]-100:+.1f}% vs 2019")
        with cols[2]:
            if latest in real and 2019 in real:
                change = 100 * real[latest] / real[2019] - 100
                st.metric(f"{latest} HICP-adjusted proxy",
                          f"€{real[latest]:,.0f}",
                          f"{change:+.1f}% vs 2019")
            else:
                st.metric(f"{latest} HICP-adjusted proxy", "Unavailable")
        real_index = {
            y: 100 * real[y] / real[2019]
            for y in years if y in real and 2019 in real
        }
        plot_items = [("Nominal spend per visitor", nominal_index, BLUE)]
        if real_index:
            plot_items.append(
                ("HICP-adjusted spend per visitor", real_index, TEAL)
            )
        plot_line(years, plot_items, "Index (2019 = 100)", "visitor-yield")
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
        if not real_index:
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
