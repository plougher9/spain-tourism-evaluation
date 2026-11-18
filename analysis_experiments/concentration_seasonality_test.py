"""Standalone official INE FRONTUR concentration and seasonality tests.

Does not alter the Streamlit app, its data snapshots or refresh flows.
Uses monthly INE FRONTUR by country of residence, 2016–2025.
"""
from pathlib import Path
import csv
import io
import json
import math
import requests
import pandas as pd

SOURCE = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/10822.csv"
OUT = Path(__file__).resolve().parent
YEARS = range(2016, 2026)
COUNTRIES = {
    "Reino Unido", "Francia", "Alemania", "Italia", "Países Bajos",
    "Bélgica", "Irlanda", "Portugal", "Suiza", "Estados Unidos",
}
# Others are aggregate regions (e.g. Nordic Countries, rest of world),
# not individual countries. HHI uses all non-overlapping source categories.
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
    months=base.groupby("market")[["year","month"]].agg({"year":"count"})
    categories=base.market.unique().tolist()
    missing=base.groupby("market").size()
    assert missing.eq(120).all(),f"Missing category month(s): {missing.to_dict()}"
    annual=base.groupby(["year","market"]).visitors.sum().unstack("market")
    # A quality gate: group categories must sum back to the national total.
    diff=annual.sum(axis=1)-national
    print("Category sum minus national count by year:",diff.to_dict())
    assert (diff.abs()/national < 0.002).all(),"INE market groups do not reconcile with national totals"
    shares=annual.div(national,axis=0)*100
    top3=shares[list(sorted(set(COUNTRIES)&set(shares.columns)))].apply(
        lambda row: row.nlargest(3).sum(),axis=1)
    rank=shares[list(sorted(set(COUNTRIES)&set(shares.columns)))].apply(
        lambda row: " + ".join(row.nlargest(3).index.tolist()),axis=1)
    concentration=pd.DataFrame({
        "year":list(YEARS),
        "total_visitors":national.reindex(YEARS).values,
        "top_three_country_share_pct":top3.reindex(YEARS).values,
        "top_three_countries":rank.reindex(YEARS).values,
        "hhi_aggregate_market_groups":((shares/100)**2).sum(axis=1).reindex(YEARS).values,
        "effective_market_groups":(1/((shares/100)**2).sum(axis=1)).reindex(YEARS).values,
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
    concentration.to_csv(OUT/"country_concentration_results.csv",index=False)
    seasonality.to_csv(OUT/"seasonality_results.csv",index=False)
    shares.to_csv(OUT/"country_market_shares.csv",index_label="year")
    print("\nCOUNTRY CONCENTRATION")
    print(concentration.round(3).to_string(index=False))
    print("\nSEASONALITY")
    print(seasonality.round(3).to_string(index=False))
    print("\nCOMPARISONS 2019 vs 2025")
    for name,frame,fields in (
        ("Country concentration",concentration,["top_three_country_share_pct","hhi_aggregate_market_groups","UK_pct","France_pct","Germany_pct"]),
        ("Seasonality",seasonality,["june_august_pct","july_august_pct","may_september_pct","winter_nov_feb_pct"])):
        a=frame.set_index("year")
        print(name)
        for field in fields:
            old,new=float(a.loc[2019,field]),float(a.loc[2025,field])
            print(f"  {field}: 2019={old:.3f}, 2025={new:.3f}, change={new-old:+.3f} {'points' if field.endswith('_pct') else 'index units'}")
    summary={"source":SOURCE,"years":"2016-2025 complete calendar years","country_group_count":len(categories),"caveats":[
        "INE publishes some aggregate regions alongside individual source countries; HHI is by published market groups, not an all-country HHI.",
        "Measures count visitor arrivals, not tourism spending, economic loss, or causal vulnerability.",
        "2020-2021 are pandemic-distorted; compare 2019 with 2025 and inspect full trend.",
        "Peak season is a share, not a direct measure of weather/disruption risk.",
    ]}
    (OUT/"concentration_seasonality_metadata.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

if __name__=="__main__":
    evaluate(fetch())
