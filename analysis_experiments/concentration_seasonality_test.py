"""Standalone official INE FRONTUR concentration and seasonality tests.

Does not alter the Streamlit app, its data snapshots or refresh flows.
Uses monthly INE FRONTUR by country of residence, 2016–2025.
"""
from pathlib import Path
import csv
import io
import json
import requests
import pandas as pd

SOURCE = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/10822.csv"
OUT = Path(__file__).resolve().parent
YEARS = range(2016, 2026)
COUNTRIES = {
    "Reino Unido", "Francia", "Alemania", "Italia", "Países Bajos",
    "Bélgica", "Irlanda", "Portugal", "Suiza", "Estados Unidos",
}
# Regional aggregates (e.g. Nordic Countries) are not individual countries.
def fetch():
    r = requests.get(SOURCE, timeout=90)
    r.raise_for_status()
    raw = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig")), delimiter=";"))
    rows = []
    for x in raw:
        if x.get("Tipo de dato") != "Dato base": continue
        p = str(x.get("Periodo",""))
        if len(p) != 7 or p[4] != "M" or not p[5:].isdigit(): continue
        year, month = int(p[:4]), int(p[5:])
        if year not in YEARS or not 1 <= month <= 12: continue
        v = x.get("Total", "").strip()
        if v in ("", ".", "..", "-", "NA"): continue
        try: value = int(v.replace(".", ""))
        except ValueError: continue
        rows.append({"year":year,"month":month,"market":x["País de residencia"],"visitors":value})
    df=pd.DataFrame(rows)
    assert not df.empty, "INE returned no monthly base values"
    duplicates=df.duplicated(["year","month","market"])
    assert not duplicates.any(),df.loc[duplicates].head()
    print("INE categories:", sorted(df.market.unique()))
    return df

def evaluate(df):
    total=df[df.market=="Total"].copy()
    assert len(total)==120, "expected complete monthly national data"
    national=total.groupby("year").visitors.sum()
    base=df[df.market!="Total"]
    # Official file has incomplete historical coverage for some small
    # countries and changed the Russia grouping. Do not fill or fabricate.
    # Use the complete individual-country categories for ranking.
    month_counts=base.groupby("market").size()
    individual=[market for market in sorted(COUNTRIES)
                if market in month_counts and month_counts[market]==120]
    assert all(market in individual for market in
               ("Reino Unido","Francia","Alemania")),individual
    annual=base[base.market.isin(individual)].groupby(
        ["year","market"]).visitors.sum().unstack("market")
    assert (annual.sum(axis=1)<=national*1.001).all()
    shares=annual.div(national,axis=0)*100
    top3=shares.apply(lambda row: row.nlargest(3).sum(),axis=1)
    rank=shares.apply(lambda row: " + ".join(row.nlargest(3).index.tolist()),axis=1)
    concentration=pd.DataFrame({
        "year":list(YEARS),
        "total_visitors":national.reindex(YEARS).values,
        "top_three_country_share_pct":top3.reindex(YEARS).values,
        "top_three_countries":rank.reindex(YEARS).values,
        "largest_country_share_pct":shares.max(axis=1).reindex(YEARS).values,
        "UK_pct":shares["Reino Unido"].reindex(YEARS).values,
        "France_pct":shares["Francia"].reindex(YEARS).values,
        "Germany_pct":shares["Alemania"].reindex(YEARS).values,
    })
    # Top-three individual-country shares do NOT sum residual "rest of..." to a country.
    months=total.pivot(index="year",columns="month",values="visitors").reindex(YEARS)
    assert months.notna().all().all()
    seasonality=pd.DataFrame({
        "year":list(YEARS),
        "june_august_pct":months[[6,7,8]].sum(axis=1).div(national)*100,
        "july_august_pct":months[[7,8]].sum(axis=1).div(national)*100,
        "may_september_pct":months[[5,9]].sum(axis=1).div(national)*100,
        "winter_nov_feb_pct":months[[11,12,1,2]].sum(axis=1).div(national)*100,
        "peak_month_pct":months.max(axis=1).div(national)*100,
        "peak_month":months.idxmax(axis=1),
    })
    # Dashboard-ready source-derived observations: no fabricated values and
    # no additions to the original six indicators.
    dashboard = {
        "source_name": "INE FRONTUR, country of residence, monthly base arrivals",
        "source_url": SOURCE,
        "frequency": "annual",
        "measure": "share of international visitor arrivals, percent",
        "source_market_definition": "United Kingdom, France and Germany; top-three individual markets for observed years",
        "coverage_note": "Complete calendar years only. No 2026 annual observation yet.",
        "method_note": "Top-three individual-country share divided by total arrivals. UK share provides potential pound/euro exposure, not an estimated FX effect.",
        "observations": [
            {
                "year": int(row["year"]),
                "top_three_pct": round(float(row["top_three_country_share_pct"]), 4),
                "uk_pct": round(float(row["UK_pct"]), 4),
                "france_pct": round(float(row["France_pct"]), 4),
                "germany_pct": round(float(row["Germany_pct"]), 4),
            }
            for _, row in concentration.iterrows()
        ],
    }
    path = OUT.parent / "data" / "visitor_concentration.json"
    path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + "\\n",
                    encoding="utf-8")
    print("Wrote dashboard observations:", path)
    concentration.to_csv(OUT/"country_concentration_results.csv",index=False)
    seasonality.to_csv(OUT/"seasonality_results.csv",index=False)
    shares.to_csv(OUT/"country_market_shares.csv",index_label="year")
    print("\nCOUNTRY CONCENTRATION")
    print(concentration.round(3).to_string(index=False))
    print("\nSEASONALITY")
    print(seasonality.round(3).to_string(index=False))
    print("\nCOMPARISONS 2019 vs 2025")
    for name,frame,fields in (
        ("Country concentration",concentration,["top_three_country_share_pct","largest_country_share_pct","UK_pct","France_pct","Germany_pct"]),
        ("Seasonality",seasonality,["june_august_pct","july_august_pct","may_september_pct","winter_nov_feb_pct"])):
        a=frame.set_index("year")
        print(name)
        for field in fields:
            old,new=float(a.loc[2019,field]),float(a.loc[2025,field])
            print(f"  {field}: 2019={old:.3f}, 2025={new:.3f}, change={new-old:+.3f} {'points' if field.endswith('_pct') else 'index units'}")
    summary={"source":SOURCE,"years":"2016-2025 complete calendar years","complete_individual_country_categories":individual,"caveats":[
        "Some countries and aggregate regions have missing or revised historical categories. Rankings include only individual-country categories with full monthly coverage; UK/France/Germany are complete. No all-country HHI is computed.",
        "Measures count visitor arrivals, not tourism spending, economic loss, or causal vulnerability.",
        "2020-2021 are pandemic-distorted; compare 2019 with 2025 and inspect full trend.",
        "Peak season is a share, not a direct measure of weather/disruption risk.",
    ]}
    (OUT/"concentration_seasonality_metadata.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

if __name__=="__main__":
    evaluate(fetch())
