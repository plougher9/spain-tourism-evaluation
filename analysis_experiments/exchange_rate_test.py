"""Standalone ECB exchange-rate / INE FRONTUR arrival correlations. No dashboard changes."""
from __future__ import annotations
import csv
import io
import json
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr

ROOT=Path(__file__).resolve().parents[1]
BASE="https://www.ine.es/jaxiT3/files/t/csv_bdsc/10822.csv"
FX="https://data-api.ecb.europa.eu/service/data/EXR/M.USD+GBP.EUR.SP00.A"
OUT=ROOT/"analysis_experiments"
OUT.mkdir(exist_ok=True)

def download(url, params=None, headers=None):
    response=requests.get(url,params=params,headers=headers,timeout=90)
    response.raise_for_status()
    print("Fetched",response.url,"bytes",len(response.content))
    return response.content

def arrivals():
    raw=download(BASE).decode("utf-8-sig")
    rows=list(csv.DictReader(io.StringIO(raw), delimiter=";"))
    names={"Reino Unido":"UK","Estados Unidos de América":"US","Alemania":"Germany"}
    table=[]
    for r in rows:
        if r.get("País de residencia") not in names or r.get("Tipo de dato")!="Dato base":
            continue
        p=r["Periodo"]; value=r.get("Total","").strip()
        if not value or value in {".","..","-"}:continue
        if len(p)!=7 or "M" not in p: continue
        period=pd.Period(p.replace("M","-"),freq="M")
        if not (2016<=period.year<=2025):continue
        num=int(value.replace(".",""))
        table.append((period,names[r["País de residencia"]],num))
    frame=pd.DataFrame(table,columns=["period","market","arrivals"]).pivot(index="period",columns="market",values="arrivals").sort_index()
    assert len(frame)==120 and (frame[["UK","US","Germany"]].loc["2019"]>0).all().all(),frame.describe()
    assert 19_000_000 < frame["UK"].loc["2025"].sum() < 19_200_000
    return frame

def exchange_rates():
    raw=download(FX,{"startPeriod":"2015-01","endPeriod":"2025-12"},headers={"Accept":"text/csv"})
    f=pd.read_csv(io.BytesIO(raw))
    print("ECB columns",f.columns.tolist())
    f=f[f["CURRENCY"].isin(["GBP","USD"])].copy()
    f["period"]=pd.PeriodIndex(f["TIME_PERIOD"].astype(str),freq="M")
    f["value"]=pd.to_numeric(f["OBS_VALUE"],errors="coerce")
    result=f.pivot_table(index="period",columns="CURRENCY",values="value",aggfunc="last").sort_index()
    assert len(result.loc["2016":"2025"])==120 and result.loc["2019",["GBP","USD"]].notna().all().all()
    return result

def correlations(arr,fx):
    joined=arr.join(fx,how="inner").sort_index()
    data=pd.DataFrame(index=joined.index)
    # Positive FX change means euro APPRECIATION: foreign visitors pay more.
    for col in ["GBP","USD"]:
        data["fx_"+col]=np.log(joined[col]).diff(12)*100
    for col in ["UK","US","Germany"]:
        x=joined[col].where(joined[col]>0)
        data["arr_"+col]=np.log(x).diff(12)*100
    # Germany comparator: difference-in-year-over-year-log-change removes
    # common destination shocks (imperfect benchmark).
    data["relative_UK"]=data["arr_UK"]-data["arr_Germany"]
    data["relative_US"]=data["arr_US"]-data["arr_Germany"]
    data=data.replace([np.inf,-np.inf],np.nan)
    data.loc["2016":"2025"].to_csv(OUT/"monthly_yoy_data.csv",index_label="month")
    results=[]
    for market,currency in [("UK","GBP"),("US","USD")]:
        for dep in ["arr_"+market,"relative_"+market]:
            for lag in (0,3,6,12):
                frame=pd.DataFrame({"x":data["fx_"+currency].shift(lag),"y":data[dep]}).dropna()
                for sample in ("all","excl_2020_2021","pre_2020","post_2022"):
                    k=frame.index.year
                    if sample=="excl_2020_2021":subset=frame[~k.isin([2020,2021])]
                    elif sample=="pre_2020":subset=frame[k<=2019]
                    elif sample=="post_2022":subset=frame[k>=2023]
                    else:subset=frame
                    if len(subset)<18:continue
                    r,p=pearsonr(subset["x"],subset["y"])
                    results.append(dict(market=market,currency="EUR/"+currency,outcome=dep,lag_months=lag,sample=sample,n=len(subset),r=round(float(r),4),p_value=round(float(p),5),start=str(subset.index.min()),end=str(subset.index.max())))
    result=pd.DataFrame(results)
    result.to_csv(OUT/"correlations.csv",index=False)
    (OUT/"summary.json").write_text(json.dumps({"sources":{"INE":BASE,"ECB":FX},"definition":"Pearson r on monthly year-over-year log changes; positive FX is euro appreciation. Lag = exchange rate observed months before arrivals. Germany difference is a descriptive comparator.","results":results},indent=2),encoding="utf-8")
    for sample in ["excl_2020_2021","pre_2020","post_2022"]:
        print("\n",sample)
        print(result[(result["sample"]==sample)&(result["outcome"].str.startswith("arr_"))][["market","lag_months","n","r","p_value"]].to_string(index=False))
    print("\nGermany-relative, nonpandemic:")
    print(result[(result["sample"]=="excl_2020_2021")&(result["outcome"].str.startswith("relative"))][["market","lag_months","n","r","p_value"]].to_string(index=False))
    print("Output files saved to",OUT)

if __name__=="__main__":
    correlations(arrivals(),exchange_rates())
