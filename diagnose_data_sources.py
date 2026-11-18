"""Diagnostic-only source inspection; never changes dashboard observations."""
import requests

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
INE = "https://servicios.ine.es/wstempus/js/ES/"
S = requests.Session()
S.headers["User-Agent"] = "SpainTourismDashboard/1.0 educational data validation"

def get(url, params=None):
    try:
        r=S.get(url,params=params,timeout=35)
        print(f"URL: {r.url} | HTTP {r.status_code} | bytes={len(r.content)}")
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        print(f"REQUEST FAILED: {type(exc).__name__}: {exc}")
        return None

def show_eurostat(dataset, filters):
    print(f"\\n=== {dataset} WITHOUT PARTNER FILTER ===")
    raw=get(BASE+dataset, {"lang":"en","sinceTimePeriod":"2025",**filters})
    if not isinstance(raw,dict): return
    print("dimensions:",list(zip(raw.get("id",[]),raw.get("size",[]))))
    for dimension in raw.get("id",[]):
        if dimension not in ("partner","bop_item","unit","currency","s_adj","stk_flow"):
            continue
        cat=raw.get("dimension",{}).get(dimension,{}).get("category",{})
        idx=cat.get("index",{})
        labels=cat.get("label",{})
        print(dimension, [(key,labels.get(key,"")) for key in list(idx)[:35]] if isinstance(idx,dict) else idx)
    vals=raw.get("value",{})
    print("nonempty observations:",len(vals))

def show_ine(tid):
    print(f"\\n=== INE TABLE {tid} SERIES ===")
    raw=get(INE+f"SERIES_TABLA/{tid}")
    if not isinstance(raw,list): return
    print("series count:",len(raw))
    for x in raw[:100]:
        print(" ",x.get("Id"),str(x.get("Nombre",""))[:190])

def main():
    show_eurostat("tipsbp41",{"geo":"ES","freq":"Q","unit":"PC_GDP","s_adj":"NSA","stk_flow":"BAL","bop_item":"CA"})
    show_eurostat("bop_its6_det",{"geo":"ES","freq":"A","currency":"MIO_EUR","bop_item":"SD","stk_flow":"BAL"})
    for tid in (10821,10841):
        show_ine(tid)

if __name__=="__main__":
    main()
