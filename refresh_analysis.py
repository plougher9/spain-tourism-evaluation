"""Refresh supplemental analytical indicators from official Eurostat datasets.

These are separate from the six assignment series: failure never overwrites
the existing verified dashboard snapshot. Do not invent or extrapolate data.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
from sources import eurostat_series

DATA = Path(__file__).resolve().parent / "data" / "analysis.json"
URL = "https://ec.europa.eu/eurostat/databrowser/view/"

CONFIG = {
    "hicp": {
        "dataset": "prc_hicp_aind",
        "filters": {"geo": "ES", "freq": "A", "unit": "INX_A_AVG", "coicop": "CP00"},
        "scale": 1.0,
        "source": "Eurostat HICP, all-items, annual average index",
        "url": URL + "prc_hicp_aind/default/table",
        "unit": "annual HICP index (rebasing does not affect 2019-ratio deflation)",
    },
    "current_account_eur": {
        "dataset": "bop_c6_a",
        "filters": {
            "geo": "ES", "freq": "A", "currency": "MIO_EUR",
            "bop_item": "CA", "stk_flow": "BAL",
            "partner": "WRL_REST", "sector10": "S1", "sectpart": "S1",
        },
        "scale": 0.001,
        "source": "Eurostat BPM6 annual current-account balance",
        "url": URL + "bop_c6_a/default/table",
        "unit": "€ billion",
    },
    "services_balance_eur": {
        "dataset": "bop_its6_det",
        "filters": {
            "geo": "ES", "freq": "A", "currency": "MIO_EUR",
            "bop_item": "S", "stk_flow": "BAL", "partner": "WRL_REST",
        },
        "scale": 0.001,
        "source": "Eurostat BPM6 international trade in services (total), balance",
        "url": URL + "bop_its6_det/default/table",
        "unit": "€ billion",
    },
}

def run():
    previous = {}
    if DATA.exists():
        previous = json.loads(DATA.read_text(encoding="utf-8"))
    payload = {"series": dict(previous.get("series", {})), "errors": {},
               "last_attempt_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    good = 0
    for key, spec in CONFIG.items():
        try:
            df = eurostat_series(spec["dataset"], spec["filters"], spec["scale"])
            values = [
                {"period": str(row.period), "value": round(float(row.value), 6)}
                for row in df.itertuples(index=False)
            ]
            if any(len(p["period"]) != 4 or not p["period"].isdigit() for p in values):
                raise ValueError(f"{key}: expected annual YYYY periods")
            if any(not (-5000 < p["value"] < 5000) for p in values):
                raise ValueError(f"{key}: implausible observation")
            if key == "hicp" and any(not (50 < p["value"] < 250) for p in values):
                raise ValueError("HICP index implausible")
            payload["series"][key] = {
                "observations": values, "source": spec["source"],
                "source_url": spec["url"], "unit": spec["unit"],
                "refreshed_utc": payload["last_attempt_utc"]
            }
            good += 1
            print(f"OK {key}: {len(values)} years, latest {values[-1]}")
        except Exception as err:
            payload["errors"][key] = str(err)
            print(f"FAILED {key}: {err}", file=sys.stderr)
    payload["last_successful_refresh_utc"] = (
        payload["last_attempt_utc"] if good == len(CONFIG)
        else previous.get("last_successful_refresh_utc")
    )
    DATA.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"Analytical indicators updated: {good}/{len(CONFIG)}")
    return 0 if good == len(CONFIG) else 1

if __name__ == "__main__":
    raise SystemExit(run())
