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
    ax.tick_params(colors=INK, labelsize=9, length=0)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_xticks(years)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_analysis(series, analysis_data):
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

    st.markdown("#### Hypothesis 1 · Is tourism earning more per visitor after inflation?")
    if 2019 in nominal and 2025 in nominal:
        years = sorted(y for y in nominal if 2019 <= y <= 2025)
        nominal_index = {y: 100 * nominal[y]/nominal[2019] for y in years}
        cols = st.columns(3)
        with cols[0]:
            st.metric("2019 nominal spending per visitor",
                      f"€{nominal[2019]:,.0f}")
        with cols[1]:
            st.metric("2025 nominal spending per visitor",
                      f"€{nominal[2025]:,.0f}",
                      f"{nominal_index[2025]-100:+.1f}% vs 2019")
        with cols[2]:
            if 2025 in real and 2019 in real:
                change = 100 * real[2025]/real[2019]-100
                st.metric("2025 inflation-adjusted proxy",
                          f"€{real[2025]:,.0f}",
                          f"{change:+.1f}% vs 2019")
            else:
                st.metric("Inflation-adjusted proxy", "Awaiting HICP data")
        real_index = {
            y: 100 * real[y]/real[2019]
            for y in years if y in real and 2019 in real
        }
        if len(real_index) >= 2:
            plot_line(
                years,
                [("Nominal spend per visitor", nominal_index, BLUE),
                 ("HICP-adjusted spend per visitor", real_index, TEAL)],
                "Index (2019 = 100)", "visitor-yield"
            )
            st.caption(
                "Spending per visitor = annual INE EGATUR spending / annual "
                "INE FRONTUR arrivals. Real proxy = nominal amount × "
                "Spain all-items annual HICP(2019) / HICP(year). "
                "**This is a consumer-price-adjusted proxy, NOT official "
                "real tourism receipts or tourism value added.** "
                "[Eurostat annual HICP source]"
                "(https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table)"
            )
        else:
            plot_line(
                years, [("Nominal spend per visitor", nominal_index, BLUE)],
                "Index (2019 = 100)", "visitor-yield-nominal"
            )
            st.info("Consumer-price-adjusted results will appear once "
                    "the official Eurostat annual HICP dataset passes refresh.")
    else:
        st.info("Complete annual arrivals and visitor spending are required.")

    st.markdown("#### Hypothesis 2 · How much does travel contribute to the external balance?")
    common = sorted(set(travel) & set(services) & set(current))
    if common:
        years = [y for y in common if 2019 <= y <= 2025]
        if not years:
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
            "The historical travel surplus is available, but an annual "
            "euro-denominated current account is not yet verified. Once "
            "the official supplemental dataset refreshes, this chart "
            "will show net travel alongside the broader current account."
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
