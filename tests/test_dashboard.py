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

    def test_streamlit_page_renders(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=55)
        if len(app.exception):
            self.fail("Dashboard render exception(s): " +
                      "; ".join(str(e.message) for e in app.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
