"""Scheduled official-source retrieval. Run: python refresh.py [--discover]."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from sources import SPECS, SourceError, discover_ine, load_snapshot, retrieve, validate

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'
DATA.mkdir(exist_ok=True)

def refresh():
    snapshot=load_snapshot(DATA)
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    errors={}
    updated=[]
    for key,spec in SPECS.items():
        try:
            df=validate(key, retrieve(key))
            snapshot['series'][key]={
                'observations':[{'period':row.period,'value':round(float(row.value),7)} for row in df.itertuples(index=False)],
                'source':spec['source'], 'source_url':spec['url'], 'refreshed_utc':now,
                'latest_observation':str(df.iloc[-1]['period']),
            }
            updated.append(key)
            print(f'OK {key:18} {len(df):4} observations latest {df.iloc[-1].period}: {df.iloc[-1].value:.5f}')
        except Exception as exc:
            errors[key]=str(exc)
            print(f'FAILED {key}: {exc}',file=sys.stderr)
    snapshot['errors']=errors
    snapshot['last_attempt_utc']=now
    snapshot['last_successful_refresh_utc']=now if not errors else snapshot.get('last_successful_refresh_utc')
    snapshot['last_partial_refresh_utc']=now if updated else snapshot.get('last_partial_refresh_utc')
    snapshot['updated_this_run']=updated
    temp=DATA/'snapshot.tmp'
    temp.write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    temp.replace(DATA/'snapshot.json')
    # Machine-readable verification file; manually check latest observation
    # against linked publisher table and record confirmation in verification.csv.
    with (DATA/'latest_observations.csv').open('w',encoding='utf-8') as file:
        file.write('metric,source,latest_period,latest_value,source_url,refresh_time_utc\n')
        for key,series in snapshot.get('series',{}).items():
            if not series.get('observations'): continue
            obs=series['observations'][-1]
            file.write(f'{key},{series["source"]},{obs["period"]},{obs["value"]},{series["source_url"]},{series["refreshed_utc"]}\n')
    print(f'Updated {len(updated)}/{len(SPECS)} series; last complete refresh: {snapshot.get("last_successful_refresh_utc")}')
    # An incomplete refresh cannot pass silently in scheduled CI; old series
    # are explicitly retained and labeled stale, not treated as updated.
    return 0 if not errors else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--discover',action='store_true',help='List candidate INE tables and IDs')
    args=ap.parse_args()
    if args.discover:
        discover_ine()
    else:
        raise SystemExit(refresh())
