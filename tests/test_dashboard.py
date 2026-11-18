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

    def test_slider_changes_hypothesis_headline_cards(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        self.assertFalse(app.exception)
        app.sidebar.slider[0].set_value((2015, 2022)).run(timeout=55)
        self.assertFalse(app.exception)
        labels = [metric.label for metric in app.metric]
        self.assertIn("2022 nominal / visitor", labels)
        self.assertNotIn("2025 nominal / visitor", labels)
        app.sidebar.slider[0].set_value((2019, 2026)).run(timeout=55)
        self.assertFalse(app.exception)
        labels = [metric.label for metric in app.metric]
        self.assertIn("2025 nominal / visitor", labels)

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
        self.assertIn("creating greater economic value and financial resilience", source)
        self.assertNotIn("growing reliance on international tourism", source)

    def test_streamlit_page_renders(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        if len(app.exception):
            self.fail("Dashboard render exception(s): " +
                      "; ".join(str(e.message) for e in app.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
