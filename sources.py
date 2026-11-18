"""Official-source data access for Spain's tourism and external-finance dashboard.
No synthetic time series, no silent last-value carry-forward.
"""
from __future__ import annotations
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

API_EU = 'https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/'
API_INE = 'https://servicios.ine.es/wstempus/js/ES/'
HEADERS = {'User-Agent': 'SpainTourismDashboard/1.0 (education; official-public-statistics)'}
TIMEOUT = 35

SPECS = {
 'arrivals': dict(title='International tourist arrivals', unit='million visitors', freq='Monthly', source='INE · FRONTUR', url='https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736176996&idp=1254735576863', why='Measures demand from non-resident visitors.'),
 'spending': dict(title='International tourist spending', unit='€ billion, nominal', freq='Monthly', source='INE · EGATUR', url='https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736177002&idp=1254735576863', why='Measures nominal revenue from foreign travelers.'),
 'tourism_gdp': dict(title='Tourism share of GDP', unit='% of GDP', freq='Annual', source='INE · Tourism Satellite Account', url='https://www.ine.es/dynt3/inebase/es/index.htm?capsel=12165&padre=12162', why='Measures how much of Spanish value added is tourism-related.'),
 'gdp_growth': dict(title='Real GDP growth', unit='%, year over year', freq='Quarterly', source='Eurostat · namq_10_gdp', url='https://ec.europa.eu/eurostat/databrowser/view/namq_10_gdp/default/table', why='Provides the economy-wide growth benchmark.'),
 'travel_balance': dict(title='Travel-services trade balance', unit='€ billion', freq='Annual', source='Eurostat · bop_its6_det', url='https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table', why='Measures travel receipts from non-residents minus residents’ travel spending abroad.'),
 'current_account': dict(title='Current account balance', unit='% of GDP', freq='Quarterly', source='Eurostat · tipsbp41', url='https://ec.europa.eu/eurostat/databrowser/view/tipsbp41/default/table', why='Shows Spain’s overall international current-account position.'),
}

# Specify verified INE series IDs here after running `python refresh.py --discover`.
# When unspecified, the refresh process attempts strict, unambiguous auto discovery.
INE_SERIES_IDS = {'arrivals': None, 'spending': None, 'tourism_gdp': None}

class SourceError(RuntimeError):
    pass


def http_json(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _clean(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', s).strip()


def eurostat_series(dataset, filters, scale=1.0):
    """Read one fully specified Eurostat JSON-stat series; reject ambiguous dimensions."""
    raw = http_json(API_EU + dataset, {'lang': 'en', 'sinceTimePeriod': '2015', **filters})
    dims = raw.get('id', [])
    size = raw.get('size', [])
    if 'time' not in dims:
        raise SourceError(f'{dataset}: API response has no time dimension')
    extras = [(d, n) for d,n in zip(dims,size) if d != 'time' and n != 1]
    if extras:
        raise SourceError(f'{dataset}: ambiguous series dimensions: {extras}; refine filters')
    time_dim = raw['dimension']['time']['category']['index']
    periods = [None]*len(time_dim)
    if isinstance(time_dim, dict):
        for label, i in time_dim.items(): periods[i] = label
    else:
        periods = list(time_dim)
    values = raw.get('value', {})
    records=[]
    for i, period in enumerate(periods):
        v = values.get(str(i), values.get(i)) if isinstance(values, dict) else (values[i] if i < len(values) else None)
        if v is not None:
            records.append({'period': str(period), 'value': float(v)*scale})
    if not records:
        raise SourceError(f'{dataset}: no observations returned')
    return pd.DataFrame(records)


def _ine_operations(op):
    # INE supports operation-code lookups through its public Tempus service.
    result = http_json(API_INE + 'TABLAS_OPERACION/' + op)
    if not isinstance(result, list):
        raise SourceError(f'INE {op}: invalid list of tables')
    return result


def discover_ine():
    """Print candidates so a human can audit the exact original source series."""
    for op in ('FRONTUR', 'EGATUR', 'CSTE'):
        try:
            tables = _ine_operations(op)
            print(f'\n{op} table choices:')
            for x in tables[:100]:
                print('  ', x.get('Id'), x.get('Nombre', '')[:110])
        except Exception as exc:
            print(f'{op} discovery failed: {exc}')


def _ine_series_metadata(table_id):
