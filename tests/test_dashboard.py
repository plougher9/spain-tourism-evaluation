"""Regression tests for the Spain tourism narrative dashboard."""
from pathlib import Path
import unittest

from story_sections import annual_totals, annual_values, change_pct
from sources import load_snapshot


ROOT = Path(__file__).resolve().parents[1]


class NarrativesTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = load_snapshot(ROOT / "data")
        self.series = self.snapshot["series"]

    def test_full_years_only(self):
        arrivals = annual_totals(self.series["arrivals"])
        spending = annual_totals(self.series["spending"])
        self.assertEqual(len(self.series["arrivals"]["observations"]), 132)
        self.assertNotIn(2015, arrivals)  # only September–December reported
        self.assertNotIn(2026, arrivals)  # latest snapshot ends in August
        self.assertIn(2019, arrivals)
        self.assertIn(2025, spending)
        self.assertAlmostEqual(arrivals[2019], 83.45, delta=0.1)

    def test_shock_benchmarks(self):
        arrivals = annual_totals(self.series["arrivals"])
        travel = annual_values(self.series["travel_balance"])
        self.assertLess(change_pct(arrivals[2020], arrivals[2019]), -80)
        self.assertAlmostEqual(travel[2020], 8.631, places=3)
        self.assertAlmostEqual(travel[2025], 70.46, places=2)

    def test_2022_energy_shock_context_uses_real_observations(self):
        spending = annual_totals(self.series["spending"])
        travel = annual_values(self.series["travel_balance"])
        self.assertIn(2021, spending)
        self.assertIn(2022, spending)
        self.assertGreater(spending[2022], spending[2021])
        self.assertAlmostEqual(spending[2022], 89.31535, places=3)
        self.assertAlmostEqual(travel[2022], 48.089, places=3)
        self.assertGreater(travel[2022], travel[2021])

    def test_tourism_gdp_history(self):
        tourism = annual_values(self.series["tourism_gdp"])
        self.assertEqual(min(tourism), 2015)
        self.assertEqual(max(tourism), 2024)
        self.assertAlmostEqual(tourism[2020], 6.0, places=1)

    def test_rolling_balance_is_separate_release_snapshot(self):
        import json
        from datetime import date
        path = ROOT / "data" / "bde_travel_rolling12.json"
        release = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(release["period_end"], "2026-08")
        self.assertAlmostEqual(release["value_eur_billions"], 74.9, places=1)
        self.assertAlmostEqual(release["prior_year_value_eur_billions"], 71.1, places=1)
        self.assertEqual(release["published_date"], "2026-10-30")
        self.assertLessEqual(date.fromisoformat(release["published_date"]), date.today())
        self.assertEqual(
            self.series["travel_balance"]["observations"][-1]["period"], "2025"
        )

    def test_static_chart_renderer_is_available(self):
        import matplotlib
        from story_sections import plot_chart
        self.assertTrue(callable(plot_chart))
        self.assertTrue(matplotlib.__version__)

    def test_inflation_adjusted_visitor_yield_and_external_balances(self):
        import json
        from analysis_sections import (
            annual_totals, annual_values, nominal_spending_per_visitor,
            real_spending_per_visitor,
        )
        analysis = json.loads(
            (ROOT / "data" / "analysis.json").read_text(encoding="utf-8")
        )
        self.assertFalse(analysis["errors"])
        a = annual_totals(self.series["arrivals"])
        s = annual_totals(self.series["spending"])
        hicp = annual_values(analysis["series"]["hicp"])
        nominal = nominal_spending_per_visitor(s, a)
        real = real_spending_per_visitor(s, a, hicp)
        self.assertAlmostEqual(nominal[2019], 1102.5, delta=0.5)
        self.assertAlmostEqual(nominal[2025], 1397.9, delta=0.5)
        self.assertAlmostEqual(real[2025], 1150.8, delta=0.5)
        self.assertGreater(real[2025], nominal[2019])
        self.assertLess(real[2025], nominal[2025])
        travel = annual_values(self.series["travel_balance"])
        ca = annual_values(analysis["series"]["current_account_eur"])
        services = annual_values(analysis["series"]["services_balance_eur"])
        self.assertAlmostEqual(ca[2025] - travel[2025], -15.631, places=2)
        self.assertAlmostEqual(travel[2025] / services[2025] * 100,
                               62.09, delta=0.1)

    def test_hypothesis_one_percentages_match_displayed_math(self):
        import json
        from analysis_sections import (
            change_from_baseline, nominal_spending_per_visitor,
            real_spending_per_visitor,
        )
        analysis = json.loads(
            (ROOT / "data" / "analysis.json").read_text(encoding="utf-8")
        )
        spending = annual_totals(self.series["spending"])
        arrivals = annual_totals(self.series["arrivals"])
        hicp = annual_values(analysis["series"]["hicp"])
        nominal = nominal_spending_per_visitor(spending, arrivals)
        real = real_spending_per_visitor(spending, arrivals, hicp)
        nominal_changes = change_from_baseline(nominal)
        real_changes = change_from_baseline(real)
        self.assertAlmostEqual(nominal_changes[2019], 0.0, places=6)
        self.assertAlmostEqual(real_changes[2019], 0.0, places=6)
        self.assertAlmostEqual(nominal_changes[2025], 26.8, delta=.2)
        self.assertAlmostEqual(real_changes[2025], 4.4, delta=.2)
        self.assertAlmostEqual(
            100 * (real[2025] / real[2019] - 1),
            real_changes[2025], places=8
        )
        self.assertEqual(
            sorted(y for y in nominal_changes if 2015 <= y <= 2026)[0],
            2016,
        )

    def test_year_selection_changes_analytical_series(self):
        import json
        from analysis_sections import analyze, nominal_spending_per_visitor
        extras = json.loads(
            (ROOT / "data" / "analysis.json").read_text(encoding="utf-8")
        )
        spending, arrivals, hicp, current, services, travel = analyze(
            self.series, extras
        )
        visitor = nominal_spending_per_visitor(spending, arrivals)
        narrow = [y for y in sorted(visitor) if 2019 <= y <= 2026]
        full = [y for y in sorted(visitor) if 2015 <= y <= 2026]
        self.assertEqual(narrow[0], 2019)
        self.assertEqual(full[0], 2016)
        self.assertIn(2016, full)
        self.assertNotIn(2016, narrow)
        common = set(current) & set(services) & set(travel)
        selected = sorted(y for y in common if 2015 <= y <= 2026)
        self.assertEqual(selected[0], 2015)
        self.assertEqual(selected[-1], 2025)
        self.assertEqual([y for y in common if 2026 <= y <= 2026], [])

    def test_financial_bridge_arithmetic_and_toggle(self):
        from reader_story import financial_bridge
        observed = financial_bridge(54.829, 113.48, 70.46, False)
        removed = financial_bridge(54.829, 113.48, 70.46, True)
        self.assertAlmostEqual(observed["other_services"], 43.02, places=2)
        self.assertAlmostEqual(observed["goods_and_income"], -58.651, places=3)
        self.assertAlmostEqual(observed["total"], 54.829, places=3)
        self.assertAlmostEqual(removed["total"], -15.631, places=3)
        self.assertAlmostEqual(removed["travel"], 0.0)
        self.assertAlmostEqual(
            removed["other_services"], observed["other_services"]
        )

    def test_financial_bars_are_zero_based_and_negative_below_axis(self):
        from unittest.mock import patch
        from reader_story import financial_bridge, draw_financial_bridge
        captured = []
        def inspect(fig, **kwargs):
            ax = fig.axes[0]
            captured.append((
                [(bar.get_y(), bar.get_height()) for bar in ax.patches],
                ax.get_ylabel(), ax.get_ylim(),
            ))
        with patch("reader_story.st.pyplot", side_effect=inspect):
            for remove in (False, True):
                values = financial_bridge(54.829, 113.48, 70.46, remove)
                draw_financial_bridge(values, 2025, remove)
        self.assertEqual(len(captured), 2)
        for bars, label, limits in captured:
            self.assertEqual(len(bars), 4)
            self.assertTrue(all(abs(bottom) < 1e-9 for bottom, _ in bars))
            self.assertLess(bars[2][1], 0)  # Goods and income below zero
            self.assertGreater(bars[1][1], 0)  # Other services above zero
            self.assertLess(limits[0], 0)
            self.assertGreater(limits[1], 0)
            self.assertIn("billion", label)
        self.assertGreater(captured[0][0][3][1], 0)
        self.assertLess(captured[1][0][3][1], 0)

    def test_part_three_arrivals_spending_and_real_yield_are_comparable(self):
        from unittest.mock import patch
        import json
        from reader_story import render_yield_section
        from analysis_sections import (change_from_baseline, nominal_spending_per_visitor, real_spending_per_visitor)
        from story_sections import annual_totals, annual_values
        spending = annual_totals(self.series["spending"])
        arrivals = annual_totals(self.series["arrivals"])
        analysis = json.loads(
            (ROOT / "data" / "analysis.json").read_text(encoding="utf-8")
        )
        hicp = annual_values(analysis["series"]["hicp"])
        captured = []
        def capture(years, series_items, ylabel, key, percent=False):
            captured.append((years, series_items, ylabel, key, percent))
        with patch("reader_story.plot_line", side_effect=capture):
            render_yield_section(spending, arrivals, hicp, 2019, 2025)
        self.assertEqual(len(captured), 1)
        years, series_items, ylabel, key, percent = captured[0]
        self.assertEqual(key, "arrivals-versus-spending")
        self.assertFalse(percent)
        self.assertAlmostEqual(series_items[0][1][2019], 100.0)
        self.assertAlmostEqual(series_items[1][1][2019], 100.0)
        self.assertGreater(series_items[1][1][2025], series_items[0][1][2025])
        self.assertIn("2019 = 100", ylabel)
        from reader_story import inflation_chart_data
        nominal = nominal_spending_per_visitor(spending, arrivals)
        real = real_spending_per_visitor(spending, arrivals, hicp)
        inflation = inflation_chart_data(
            years, change_from_baseline(nominal),
            change_from_baseline(real), hicp
        )
        self.assertEqual(inflation["Year"].tolist(), [str(y) for y in years])
        self.assertAlmostEqual(inflation.loc[inflation["Year"] == "2019", "Inflation"].iloc[0], 0.0)
        self.assertAlmostEqual(inflation.loc[inflation["Year"] == "2025", "Nominal"].iloc[0], 26.8, delta=.2)
        self.assertAlmostEqual(inflation.loc[inflation["Year"] == "2025", "Inflation"].iloc[0], 21.5, delta=.2)
        self.assertAlmostEqual(inflation.loc[inflation["Year"] == "2025", "Adjusted"].iloc[0], 4.4, delta=.2)

    def test_part_three_b_hover_chart_and_toggle_controls(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        self.assertFalse(app.exception)
        options = [x for x in app.radio if x.key == "inflation_comparison_view"]
        self.assertEqual(len(options), 1)
        self.assertEqual(list(options[0].options), [
            "Compare all", "Nominal only", "Inflation-adjusted only"
        ])
        self.assertGreaterEqual(len(app.get("vega_lite_chart")), 1)
        options[0].set_value("Nominal only").run(timeout=55)
        self.assertFalse(app.exception)
        self.assertEqual(
            next(x for x in app.radio
                 if x.key == "inflation_comparison_view").value, "Nominal only"
        )
        next(x for x in app.radio
             if x.key == "inflation_comparison_view").set_value(
                 "Inflation-adjusted only"
             ).run(timeout=55)
        self.assertFalse(app.exception)

    def test_part_three_math_dropdowns_and_inflation_explanation(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        self.assertFalse(app.exception)
        expanders = [x.label for x in app.get("expander")]
        self.assertTrue(any("math for visitors versus spending" in x.lower()
                            for x in expanders))
        self.assertTrue(any("math behind the" in x.lower()
                            for x in expanders))
        markdown = " ".join(m.value for m in app.markdown)
        self.assertIn("all-items HICP rose", markdown)
        self.assertIn("change in general purchasing power", markdown)

    def test_part_four_shock_charts_have_both_event_annotations(self):
        from unittest.mock import patch
        from reader_story import plot_shock_history, plot_shock_accounts
        travel = {2019: 46.354, 2020: 8.631, 2022: 48.089, 2025: 70.46}
        goods = {2019: -25.0, 2020: -15.0, 2022: -70.0, 2025: -50.266}
        current = {2019: 26.69, 2020: 8.906, 2022: 5.766, 2025: 54.829}
        years = [2019, 2020, 2022, 2025]
        captured = []
        def capture(fig, **kwargs):
            ax = fig.axes[0]
            captured.append(ax)
            if len(captured) == 1:
                labels = " ".join(t.get_text() for t in ax.texts)
                self.assertIn("COVID-19", labels)
                self.assertIn("energy-price shock", labels)
            else:
                bars = ax.patches
                self.assertEqual(len(bars), 12)
                self.assertTrue(any(x.get_height() < 0 for x in bars))
                self.assertIn("billion", ax.get_ylabel())
        with patch("reader_story.st.pyplot", side_effect=capture):
            plot_shock_history(travel, years)
            plot_shock_accounts(travel, goods, current, years)
        self.assertEqual(len(captured), 2)

    def test_shock_labels_clear_bars_at_full_history(self):
        from unittest.mock import patch
        from reader_story import plot_shock_history
        travel = {2015: 40.7, 2016: 43.5, 2017: 46.8,
                  2018: 46.7, 2019: 46.354, 2020: 8.631,
                  2021: 18.531, 2022: 48.089, 2023: 58.798,
                  2024: 68.5, 2025: 70.46}
        with patch("reader_story.st.pyplot") as render:
            plot_shock_history(travel, sorted(travel))
            fig = render.call_args.args[0]
            ax = fig.axes[0]
            shock_labels = [text for text in ax.texts
                            if "COVID-19" in text.get_text()
                            or "energy-price shock" in text.get_text()]
            self.assertEqual(len(shock_labels), 2)
            self.assertTrue(all(text.xyann[1] > max(travel.values())
                                for text in shock_labels))

    def test_part_three_legend_is_horizontal_and_chart_has_height(self):
        from unittest.mock import patch
        from reader_story import draw_inflation_chart
        import pandas as pd
        data = pd.DataFrame({
            "Year": ["2019", "2020", "2021", "2022", "2023", "2024", "2025"],
            "Nominal": [0, -10, -3, 15, 20, 24, 27],
            "Inflation": [0, 0, 3, 12, 17, 19, 21],
            "Adjusted": [0, -10, -5, 3, 3, 4, 5],
        })
        with patch("reader_story.st.altair_chart") as render:
            draw_inflation_chart(data, "Compare all")
            chart = render.call_args.args[0].to_dict()
        self.assertGreaterEqual(chart["height"], 400)
        legend = chart["layer"][1]["encoding"]["color"]["legend"]
        self.assertEqual(legend["orient"], "bottom")
        self.assertEqual(legend["columns"], 3)

    def test_visitor_concentration_source_and_dashboard_render(self):
        import json
        from unittest.mock import patch
        from reader_story import render_visitor_concentration
        release = json.loads((ROOT / "data" / "visitor_concentration.json").read_text())
        years = {x["year"]: x for x in release["observations"]}
        self.assertAlmostEqual(years[2019]["top_three_pct"], 48.28, delta=0.04)
        self.assertAlmostEqual(years[2025]["top_three_pct"], 45.3523, places=3)
        self.assertAlmostEqual(years[2025]["uk_pct"], 19.7145, places=3)
        self.assertLess(years[2025]["top_three_pct"], years[2019]["top_three_pct"])
        with patch("reader_story.st.pyplot") as plot:
            render_visitor_concentration(release, 2015, 2026)
            self.assertEqual(plot.call_count, 1)
            axes = plot.call_args.args[0].axes[0]
            self.assertEqual(len(axes.lines[0].get_xdata()), 10)

    def test_visitor_concentration_year_range_and_missing_data(self):
        import json
        from unittest.mock import patch
        from reader_story import render_visitor_concentration
        release = json.loads((ROOT / "data" / "visitor_concentration.json").read_text())
        with patch("reader_story.st.pyplot") as plot, \
             patch("reader_story.st.caption") as caption:
            render_visitor_concentration(release, 2022, 2024)
            years = list(plot.call_args.args[0].axes[0].lines[0].get_xdata())
            self.assertEqual(years, [2022, 2023, 2024])
            self.assertTrue(any("vs 2022" in str(c.args[0])
                                for c in caption.call_args_list))
        with patch("reader_story.st.pyplot"), \
             patch("reader_story.st.caption") as caption:
            render_visitor_concentration(release, 2015, 2025)
            self.assertTrue(any("vs 2016" in str(c.args[0])
                                for c in caption.call_args_list))
            self.assertTrue(any("-7.9 percentage points" in str(c.args[0])
                                for c in caption.call_args_list))
        with patch("reader_story.st.info") as info:
            render_visitor_concentration(None, 2015, 2026)
            self.assertTrue(info.called)

    def test_part_four_goods_are_from_official_data_when_available(self):
        import json
        from story_sections import annual_values
        analysis = json.loads(
            (ROOT / "data" / "analysis.json").read_text(encoding="utf-8")
        )
        if "goods_balance_eur" not in analysis.get("series", {}):
            self.skipTest("Official goods balance is awaiting scheduled refresh")
        goods = annual_values(analysis["series"]["goods_balance_eur"])
        self.assertIn(2022, goods)
        self.assertAlmostEqual(goods[2019], -25.195, places=3)
        self.assertAlmostEqual(goods[2022], -60.215, places=3)
        self.assertAlmostEqual(goods[2025], -50.266, places=3)
        self.assertLess(goods[2022], goods[2019])

    def test_tourism_gdp_has_room_at_2019(self):
        from unittest.mock import patch
        from analysis_sections import plot_line
        captured = []
        def inspect(fig, **kwargs):
            ax = fig.axes[0]
            captured.append((ax.get_xlim(), ax.get_legend()))
        with patch("analysis_sections.st.pyplot", side_effect=inspect):
            plot_line([2019, 2020, 2021, 2022, 2023, 2024],
                      [("Tourism share", {2019: 12.6, 2020: 6.0, 2021: 7.8,
                                          2022: 12.1, 2023: 12.4, 2024: 12.6},
                        "#16848C")],
                      "Tourism contribution (% of GDP)", "tourism-gdp")
        bounds, legend = captured[0]
        self.assertLess(bounds[0], 2018.5)
        self.assertGreater(bounds[1], 2024.5)
        self.assertIsNone(legend)

    def test_slider_changes_narrative_year_and_financial_toggle(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        self.assertFalse(app.exception)
        self.assertTrue(any("01 · How important" in m.value
                            for m in app.markdown))
        app.sidebar.slider[0].set_value((2015, 2022)).run(timeout=55)
        self.assertFalse(app.exception)
        self.assertTrue(any("2022 annual values" in c.value
                            for c in app.caption))
        self.assertTrue(any("2022" in m.value and "annual travel surplus" in m.value
                            for m in app.markdown) or
                        any("2022" in m.value and "net travel" in m.value
                            for m in app.markdown))
        app.sidebar.slider[0].set_value((2019, 2026)).run(timeout=55)
        self.assertFalse(app.exception)
        self.assertTrue(any("2025 annual values" in c.value
                            for c in app.caption))
        toggle = next(button for button in app.button
                      if button.label == "Remove travel contribution")
        toggle.click().run(timeout=55)
        self.assertFalse(app.exception)
        self.assertTrue(any("€-15.6B" in m.value for m in app.markdown))
        self.assertTrue(any(button.label == "Restore travel contribution"
                            for button in app.button))

    def test_every_main_chart_has_labeled_axes(self):
        from unittest.mock import patch
        import plotly.graph_objects as go
        from story_sections import plot_chart
        from analysis_sections import plot_line

        evidence = []
        def capture(fig, **kwargs):
            axes = fig.axes[0]
            evidence.append((axes.get_xlabel(), axes.get_ylabel()))

        with patch("analysis_sections.st.pyplot", side_effect=capture):
            plot_line([2019, 2020],
                      [("Growth", {2019: 0, 2020: -20}, "#416F94")],
                      "Change vs 2019 (%)", "visitor-yield", percent=True)
            plot_line([2019, 2020],
                      [("Travel surplus", {2019: 46, 2020: 9}, "#16848C")],
                      "Annual balance (€ billion)", "external-finance")

        for key in ("tourism-index", "travel-surplus-shock",
                    "tourism-gdp-share", "gdp_growth-context",
                    "current_account-context"):
            from datetime import datetime
            x = [datetime(2019, 1, 1), datetime(2020, 1, 1)] if key.endswith("-context") else [2019, 2020]
            y = [100.0, 80.0]
            fig = go.Figure(go.Scatter(x=x, y=y,
                                      line={"color": "#416F94"}))
            with patch("story_sections.st.pyplot", side_effect=capture):
                plot_chart(fig, key)

        self.assertEqual(len(evidence), 7)
        for horizontal, vertical in evidence:
            self.assertTrue(horizontal.strip(), "Missing horizontal-axis label")
            self.assertTrue(vertical.strip(), "Missing vertical-axis label")
            self.assertIn("year", horizontal.lower())

    def test_dashboard_research_question_reframed(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("How does international tourism strengthen Spain", source)
        self.assertNotIn("growing reliance on international tourism", source)

    def test_full_synthesis_is_in_memo_not_dashboard(self):
        source = (ROOT / "reader_story.py").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("Overall analysis · What can we conclude?", source)
        self.assertNotIn("**Financial strength:** In 2025 Spain recorded", source)
        self.assertIn('st.markdown("### The central finding")', source)
        self.assertIn("render_financial_section(", source)
        self.assertIn("render_dependence_section(", source)
        self.assertIn("render_yield_section(", source)
        self.assertIn("render_shock_section(", source)
        self.assertIn("render_exploration(", source)
        self.assertIn("separate required memo", readme)

    def test_streamlit_page_renders(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        if len(app.exception):
            self.fail("Dashboard render exception(s): " +
                      "; ".join(str(e.message) for e in app.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
