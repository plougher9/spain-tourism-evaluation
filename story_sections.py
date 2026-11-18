"""Narrative exhibits derived from the six official Spain dashboard series.

All statistics are computed from the saved source observations. This module
does not contact external services, synthesize missing observations, or
equate EGATUR visitor expenditure with balance-of-payments travel credits.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

INK = "#163344"
TEAL = "#16848C"
BLUE = "#416F94"
GOLD = "#C58B37"
RED = "#C9605A"
GRID = "#E7EDF1"


def annual_totals(entry):
    """Sum monthly values for *complete* 12-month calendar years only."""
    obs = entry.get("observations", [])
    rows = [
        {"year": int(o["period"][:4]), "month": o["period"][5:7],
         "value": float(o["value"])}
        for o in obs
        if len(str(o.get("period", ""))) == 7
        and str(o["period"])[4] == "-"
        and str(o["period"])[5:7].isdigit()
    ]
    if not rows:
        return {}
    df = pd.DataFrame(rows)
    grouped = df.groupby("year").agg(
        total=("value", "sum"), months=("month", "nunique"),
        observations=("value", "size")
    )
    return {
        int(y): float(row["total"])
        for y, row in grouped.iterrows()
        if int(row["months"]) == 12 and int(row["observations"]) == 12
    }


def annual_values(entry):
    """Read reported annual values; do not sum monthly/quarterly observations."""
    return {
        int(str(o["period"])): float(o["value"])
        for o in entry.get("observations", [])
        if str(o.get("period", "")).isdigit()
        and len(str(o["period"])) == 4
    }


def change_pct(current, baseline):
    if not baseline:
        return None
    return 100.0 * (current / baseline - 1.0)


def filtered_years(data, start_year, end_year):
    return [y for y in sorted(data) if start_year <= y <= end_year]


def format_delta(delta):
    return "—" if delta is None else f"{delta:+.1f}%"


def chart_style(fig, height=330, ytitle=None):
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=24, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK, size=12),
        hovermode="x unified",
        xaxis=dict(showgrid=False, tickmode="linear", dtick=1),
        yaxis=dict(gridcolor=GRID, zeroline=False, title=ytitle),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0),
    )
    return fig


def plot_chart(fig, key):
    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False}, key=key)


def render_recent_rolling_balance(release):
    """Source-published rolling 12-month snapshot, distinct from annual Eurostat."""
    required = ("period_end", "value_eur_billions",
                "prior_year_value_eur_billions", "source_url")
    if not isinstance(release, dict) or any(k not in release for k in required):
        return
    current = float(release["value_eur_billions"])
    previous = float(release["prior_year_value_eur_billions"])
    year_on_year = current - previous
    period = release["period_end"]
    published = release.get("published_date", "date not recorded")
    source = release["source_url"]
    st.markdown("#### Latest official external-finance reading")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rolling 12-month tourism surplus", f"€{current:,.1f}B",
                  delta=f"+€{year_on_year:.1f}B vs previous 12 months")
    with col2:
        st.metric("Comparable prior 12 months", f"€{previous:,.1f}B")
    with col3:
        share = release.get("gdp_share_percent")
        st.metric("Tourism surplus / GDP",
                  f"{float(share):.1f}%" if share is not None else "—")
    st.caption(
        f"**Period:** 12 months ending {period} · **Published:** {published} · "
        f"[Banco de España original release]({source}). "
        "**Source-published release snapshot, not automatically refreshed.** "
        "This is NOT a 2026 calendar-year total and should not be added to "
        "the annual Eurostat travel-services series. The GDP percentage "
        "here describes the tourism balance, NOT tourism's contribution to GDP."
    )


def render_story(series, specs, start_year, end_year, rolling_balance=None):
    arrivals = annual_totals(series.get("arrivals", {}))
    spending = annual_totals(series.get("spending", {}))
    travel = annual_values(series.get("travel_balance", {}))
    gdp_share = annual_values(series.get("tourism_gdp", {}))
    gdp = series.get("gdp_growth", {}).get("observations", [])
    current = series.get("current_account", {}).get("observations", [])

    st.markdown("### The finding")
    st.markdown(
        '<div class="narrative-lead"><strong>Tourism generates substantial '
        'external earnings for Spain, but that economic support can contract '
        'abruptly during a global shock.</strong><br>'
        'The evidence shows a severe 2020 collapse and an unusually strong '
        'recovery in nominal spending and the travel-services surplus. '
        'The data demonstrate exposure, not a causal estimate of '
        'tourism’s effect on GDP or the current account.</div>',
        unsafe_allow_html=True,
    )

    # Historical shock is deliberately a fixed 2019–2020 benchmark; the
    # year-range control governs every plot and the selected-year scorecards.
    shock_arrivals = (
        change_pct(arrivals[2020], arrivals[2019])
        if 2019 in arrivals and 2020 in arrivals else None
    )
    common = filtered_years(
        set(arrivals) & set(spending) & set(travel),
        start_year, end_year,
    )
    focus = common[-1] if common else None
    cols = st.columns(3, gap="medium")
    with cols[0]:
        st.metric(
            "2020 visitors vs. 2019",
            format_delta(shock_arrivals),
            help="Fixed historical shock benchmark using complete annual FRONTUR totals.",
        )
        st.caption("Historical shock benchmark · fixed 2019–2020")
    with cols[1]:
        if focus is not None:
            delta = (
                change_pct(spending[focus], spending[2019])
                if 2019 in spending else None
            )
            st.metric(f"{focus} visitor spending", f"€{spending[focus]:,.1f}B",
                      format_delta(delta) + " vs 2019" if delta is not None else None)
            st.caption("Nominal EGATUR spending · full calendar year")
        else:
            st.metric("Visitor spending", "No full year")
            st.caption("No common complete-year data in the selected range")
    with cols[2]:
        if focus is not None:
            st.metric(f"{focus} travel surplus", f"€{travel[focus]:,.1f}B")
            st.caption("Eurostat BPM6 travel-services balance · annual")
        else:
            st.metric("Travel-services balance", "No full year")
            st.caption("No common annual data in the selected range")

    st.caption(
        "Scorecards 2–3 follow the selected year range; the 2020 shock "
        "scorecard is a fixed historical reference. Annual visitor and "
        "spending totals require all 12 monthly observations."
    )

    st.markdown('<div class="story-chapter">01 / Growth: more spending, not just more visitors</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Index annual international arrivals and **nominal** visitor spending "
        "to 2019 = 100. The gap after reopening shows how the value of "
        "visitor spending has outpaced visitor volume."
    )
    valid = filtered_years(set(arrivals) & set(spending), start_year, end_year)
    if 2019 in arrivals and 2019 in spending and valid:
        fig = go.Figure()
        fig.add_hline(y=100, line_color="#9EACB5", line_dash="dot")
        fig.add_trace(go.Scatter(
            x=valid, y=[arrivals[y] / arrivals[2019] * 100 for y in valid],
            name="Visitor arrivals", mode="lines+markers",
            line=dict(color=BLUE, width=3), marker=dict(size=7),
            hovertemplate="%{x}: %{y:.1f} (2019=100)<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=valid, y=[spending[y] / spending[2019] * 100 for y in valid],
            name="Nominal visitor spending", mode="lines+markers",
            line=dict(color=TEAL, width=3), marker=dict(size=7),
            hovertemplate="%{x}: %{y:.1f} (2019=100)<extra></extra>",
        ))
        if 2020 in valid:
            fig.add_vrect(x0=2019.65, x1=2020.35, fillcolor=RED,
                          opacity=.09, line_width=0)
            fig.add_annotation(x=2020, y=20, text="COVID-19",
                               showarrow=False, font=dict(color=RED, size=11))
        if 2022 in valid:
            fig.add_vline(x=2022, line_dash="dot", line_color=GOLD, line_width=2)
            fig.add_annotation(
                x=2022, y=1.09, yref="paper", text="2022 energy-price shock",
                showarrow=False, font=dict(color=GOLD, size=11),
                xanchor="left",
            )
        plot_chart(chart_style(fig, ytitle="2019 = 100"), "tourism-index")
        st.caption(
            "Source: INE FRONTUR and EGATUR. Full calendar-year totals only; "
            "2015 and the incomplete 2026 year are intentionally excluded. "
            "Spending is nominal, so part of its growth may reflect inflation "
            "rather than real spending gains."
        )
    else:
        st.info("No complete annual arrivals-and-spending observations in this year range.")

    st.markdown('<div class="story-chapter">02 / Vulnerability: what happened when travel stopped?</div>',
                unsafe_allow_html=True)
    st.markdown(
        "During COVID-19, the flow of visitors and foreign tourism spending "
        "fell sharply, while Spain's travel-services trade surplus shrank. "
        "That is a concrete example of exposure to an external demand shock."
    )
    years = filtered_years(travel, start_year, end_year)
    if years:
        fig = go.Figure(go.Bar(
            x=years, y=[travel[y] for y in years],
            marker_color=[RED if y == 2020 else TEAL for y in years],
            text=[f"€{travel[y]:.1f}B" if y in (2019, 2020, max(years)) else "" for y in years],
            textposition="outside",
            hovertemplate="%{x}: €%{y:,.2f}B<extra></extra>",
        ))
        chart_style(fig, ytitle="€ billion")
        fig.update_layout(showlegend=False)
        if 2022 in years:
            fig.add_annotation(
                x=2022, y=travel[2022], yshift=22,
                text="2022: energy shock / tourism recovery",
                showarrow=True, arrowhead=2, ax=70, ay=-44,
                font=dict(color=GOLD, size=11), arrowcolor=GOLD,
            )
        plot_chart(fig, "travel-surplus-shock")
        if 2019 in travel and 2020 in travel:
            drop = change_pct(travel[2020], travel[2019])
            st.caption(
                f"Fixed shock benchmark: the travel surplus moved from "
                f"€{travel[2019]:.1f}B in 2019 to €{travel[2020]:.1f}B "
                f"in 2020 ({drop:.1f}%). Source: Eurostat bop_its6_det, "
                "services: travel, balance, rest of world."
            )
    else:
        st.info("No annual travel-services balance observations in this year range.")

    # Compare two shocks without suggesting the 2022 energy crisis caused
    # tourism's recovery or that the services rebound fully offset energy costs.
    if all(y in spending and y in travel for y in (2021, 2022)):
        spend_growth = change_pct(spending[2022], spending[2021])
        balance_growth = travel[2022] - travel[2021]
        st.markdown("#### 2022: Energy-price shock / Tourism resilience")
        left, right = st.columns(2)
        with left:
            st.metric(
                "2022 nominal visitor spending",
                f"€{spending[2022]:,.1f}B",
                f"{spend_growth:+.1f}% versus 2021",
            )
            st.caption("INE EGATUR · full-year tourism spending")
        with right:
            st.metric(
                "2022 travel-services surplus",
                f"€{travel[2022]:,.1f}B",
                f"+€{balance_growth:,.1f}B versus 2021",
            )
            st.caption("Eurostat bop_its6_det · annual balance")
        st.markdown(
            "**Contrasting shocks:** In 2020, restrictions on travel "
            "caused tourism revenues to collapse. In 2022, higher imported "
            "energy prices damaged Spain's terms of trade, while tourism "
            "and other services recovered. Strong services exports helped "
            "cushion the shock, but did **not** fully offset the higher "
            "energy-import bill. This is an observed association, not a "
            "causal estimate of tourism's contribution to the current account. "
            "[IMF 2023 External Sector Report]"
            "(https://www.imf.org/-/media/files/publications/esr/2023/english/ch3.pdf)"
        )
        st.caption(
            "The energy shock is contextual: this dashboard's six core "
            "series do not directly measure energy-import prices or the "
            "energy trade deficit. Nominal spending growth includes "
            "price effects."
        )

    st.markdown('<div class="story-chapter">03 / Dependence: tourism’s share of GDP</div>',
                unsafe_allow_html=True)
    st.markdown(
        "Tourism represents a material share of Spanish economic activity. "
        "The pre-pandemic and 2024 reported shares are both 12.6%, so "
        "this series alone does **not** establish a continuously rising GDP dependence."
    )
    years = filtered_years(gdp_share, start_year, end_year)
    if years:
        fig = go.Figure(go.Scatter(
            x=years, y=[gdp_share[y] for y in years],
            mode="lines+markers", name="Tourism share of GDP",
            line=dict(color=TEAL, width=3), marker=dict(size=8),
            hovertemplate="%{x}: %{y:.1f}% of GDP<extra></extra>",
        ))
        if 2020 in years:
            fig.add_vrect(x0=2019.65, x1=2020.35, fillcolor=RED,
                          opacity=.09, line_width=0)
        chart_style(fig, ytitle="% of GDP")
        fig.update_layout(showlegend=False)
        plot_chart(fig, "tourism-gdp-share")
        st.caption(
            "Source: INE Tourism Satellite Account / DCE89. "
            "**Important revision breaks:** 2015 (Base 2010), 2016–2020 "
            "(Statistical Revision 2019), and 2021 onward "
            "(Statistical Revision 2024). Compare across bases cautiously."
        )
    else:
        st.info("No annual tourism-GDP observations in this range. "
                "The latest available year is 2024.")

    st.markdown('<div class="story-chapter">04 / International finance: the wider external position</div>',
                unsafe_allow_html=True)
    st.markdown(
        "The travel-services surplus is one component of Spain's broader "
        "external accounts. GDP growth and the current account provide "
        "context, but neither can be attributed to tourism alone."
    )
    render_recent_rolling_balance(rolling_balance)

    cols = st.columns(2, gap="medium")
    series_pairs = [
        ("gdp_growth", gdp, "Real GDP growth", "% year over year", GOLD),
        ("current_account", current, "Current account", "% of GDP", BLUE),
    ]
    for col, (key, observations, heading, unit, color) in zip(cols, series_pairs):
        with col:
            st.markdown(f"**{heading}**")
            points = []
            for o in observations:
                p = str(o.get("period", ""))
                if "-Q" not in p:
                    continue
                try:
                    y, q = p.split("-Q")
                    dt = pd.Timestamp(int(y), (int(q) - 1) * 3 + 1, 1)
                except (ValueError, TypeError):
                    continue
                if start_year <= dt.year <= end_year:
                    points.append((dt, float(o["value"])))
            if points:
                fig = go.Figure(go.Scatter(
                    x=[x[0] for x in points],
                    y=[x[1] for x in points],
                    name=heading, mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=5),
                    hovertemplate="%{x|%Y-%m}: %{y:.2f}<extra></extra>",
                ))
                fig.add_hline(y=0, line_color="#A5B0B8", line_width=1)
                chart_style(fig, height=280, ytitle=unit)
                fig.update_layout(
                    showlegend=False,
                    xaxis=dict(showgrid=False,
                               range=[f"{start_year}-01-01", f"{end_year}-12-31"]),
                )
                plot_chart(fig, key + "-context")
                st.caption(
                    f"Quarterly · [{specs[key]['source']}]({specs[key]['url']}) "
                    f"· latest available: {observations[-1]['period']}"
                )
            else:
                st.info(f"No {heading.lower()} observations in this range.")

    st.markdown('<div class="story-chapter">05 / Explore a hypothetical travel-surplus shock</div>',
                unsafe_allow_html=True)
    st.markdown(
        "What if a future shock **reduces the net travel-services surplus**? "
        "This is an accounting sensitivity, not a prediction of visitor "
        "behavior or a model of the entire current account."
    )
    years = filtered_years(travel, start_year, end_year)
    if years:
        left, right = st.columns([1, 2], gap="large")
        with left:
            base_year = st.selectbox(
                "Baseline travel-surplus year",
                options=years, index=len(years) - 1,
                key="scenario_year",
            )
            shock = st.slider(
                "Hypothetical reduction in net travel surplus",
                min_value=0, max_value=100, value=25, step=5,
                format="%d%%", key="scenario_shock",
            )
        base = travel[base_year]
        stressed = base * (1 - shock / 100.0)
        loss = base - stressed
        with right:
            a, b = st.columns(2)
            with a:
                st.metric("Reported travel surplus", f"€{base:,.1f}B",
                          help=f"Eurostat {base_year} annual travel-services balance")
            with b:
                st.metric("Hypothetical stressed surplus",
                          f"€{stressed:,.1f}B",
                          f"€{-loss:,.1f}B versus baseline",
                          delta_color="normal")
            st.progress((100 - shock) / 100.0)
            st.caption(
                f"Scenario arithmetic: €{base:.2f}B × (1 − {shock}%) "
                f"= €{stressed:.2f}B. It does not estimate travel "
                "receipts/debits separately, substitution, policy responses, "
                "GDP effects, or the full current-account response."
            )
    else:
        st.info("Choose a period containing an annual travel-surplus observation "
                "to use the scenario tool.")

    st.markdown("### Interpretation")
    st.markdown(
        '<div class="narrative-conclusion"><strong>What the evidence supports:</strong> '
        'Tourism materially contributes to Spain’s external earnings. '
        'The 2020 collapse illustrates vulnerability, while the subsequent '
        'spending and trade-balance recovery illustrates resilience. '
        '<strong>What it does not prove:</strong> that tourism dependence is '
        'continuously increasing, or that movements in aggregate GDP and '
        'the current account were caused by tourism alone.</div>',
        unsafe_allow_html=True,
    )
