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
API_INE = 'https://servicios.ine.es/wstempus/jsCache/ES/'
HEADERS = {'User-Agent': 'SpainTourismDashboard/1.0 (education; official-public-statistics)'}
TIMEOUT = 35

SPECS = {
 'arrivals': dict(title='International tourist arrivals', unit='million visitors', freq='Monthly', source='INE · FRONTUR', url='https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736176996&idp=1254735576863', why='Measures demand from non-resident visitors.'),
 'spending': dict(title='International tourist spending', unit='€ billion, nominal', freq='Monthly', source='INE · EGATUR', url='https://www.ine.es/dyngs/INEbase/en/operacion.htm?c=Estadistica_C&cid=1254736177002&idp=1254735576863', why='Measures nominal revenue from foreign travelers.'),
 'tourism_gdp': dict(title='Tourism share of GDP', unit='% of GDP', freq='Annual', source='INE · Tourism Satellite Account', url='https://www.ine.es/consul/serie.do?L=1&d=true&s=DCE89', why='Measures how much of Spanish value added is tourism-related.'),
 'gdp_growth': dict(title='Real GDP growth', unit='%, year over year', freq='Quarterly', source='Eurostat · namq_10_gdp', url='https://ec.europa.eu/eurostat/databrowser/view/namq_10_gdp/default/table', why='Provides the economy-wide growth benchmark.'),
 'travel_balance': dict(title='Travel-services trade balance', unit='€ billion', freq='Annual', source='Eurostat · bop_its6_det', url='https://ec.europa.eu/eurostat/databrowser/view/bop_its6_det/default/table', why='Measures travel receipts from non-residents minus residents’ travel spending abroad.'),
 'current_account': dict(title='Current account balance', unit='% of GDP', freq='Quarterly', source='Eurostat · tipsbp41', url='https://ec.europa.eu/eurostat/databrowser/view/tipsbp41/default/table', why='Shows Spain’s overall international current-account position.'),
}

# Specify verified INE series IDs here after running `python refresh.py --discover`.
# When unspecified, the refresh process attempts strict, unambiguous auto discovery.
INE_SERIES_IDS = {'arrivals': '286', 'spending': '585', 'tourism_gdp': 'DCE89'}

# Published historical observations from INE SDG 8.9.1.2, official series DCE89.
# https://www.ine.es/consul/serie.do?L=1&d=true&s=DCE89
# These are real published values, not model-generated estimates.
# INE states: 2015 uses Base 2010; 2016–2020 use Statistical Revision 2019;
# 2021 onwards use Statistical Revision 2024. Comparison across the breaks
# requires caution. The current Tourism Satellite Account table covers 2021+.
INE_TOURISM_GDP_HISTORY = {
    '2015': 11.1,
    '2016': 11.3,
    '2017': 12.1,
    '2018': 12.2,
    '2019': 12.6,
    '2020': 6.0,
}

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
    data = http_json(API_INE + f'SERIES_TABLA/{table_id}')
    if not isinstance(data, list):
        raise SourceError(f'INE table {table_id}: invalid series list')
    return data


def _ine_series_id(metric):
    if INE_SERIES_IDS.get(metric):
        return str(INE_SERIES_IDS[metric])
    op = {'arrivals':'FRONTUR', 'spending':'EGATUR', 'tourism_gdp':'CSTE'}[metric]
    patterns = {
      'arrivals': [r'turistas', r'total|nacional'],
      'spending': [r'gasto total', r'total|nacional'],
      'tourism_gdp': [r'aportacion.*turismo.*pib|turismo.*pib', r'porcentaje|%'],
    }[metric]
    matches=[]
    for table in _ine_operations(op):
        tid = table.get('Id')
        name = _clean(table.get('Nombre', ''))
        if not tid or (metric=='arrivals' and not re.search('turistas|movimientos',name)) or (metric=='spending' and not re.search('gasto',name)) or (metric=='tourism_gdp' and not re.search('turismo|pib|aportacion', name)):
            continue
        try:
            series = _ine_series_metadata(tid)
        except Exception:
            continue
        for item in series:
            label = _clean(item.get('Nombre', ''))
            # Conservative auto-discovery: reject geographic breakouts, growth rates,
            # average spend, other sub-populations, and nationalities.
            banned = ('variacion','tasa anual','aleman','francia','reino unido',
                      'cataluna','andalucia','canarias','alojamiento','medio','pernoct')
            if any(b in label for b in banned): continue
            if all(re.search(pattern, name+' '+label) for pattern in patterns):
                matches.append((str(item.get('Id','')), label, name))
    # Don't auto-select a potentially wrong measure if IDs aren't uniquely identified.
    unique = {m[0]:m for m in matches if m[0]}
    if len(unique) != 1:
        sample = [f'{x[0]}: {x[1][:80]}' for x in list(unique.values())[:8]]
        raise SourceError(f'INE {metric}: expected exactly one matching series, found {len(unique)}. '
                          f'Run refresh.py --discover and set INE_SERIES_IDS in sources.py. Candidates: {sample}')
    return next(iter(unique))


def ine_series(metric):
    """Fetch specific INE table data; integer metadata IDs are not series codes."""
    table_ids = {'arrivals': 10821, 'spending': 10841, 'tourism_gdp': 72969}
    raw = http_json(API_INE + f'DATOS_TABLA/{table_ids[metric]}', {'nult': 180})
    if not isinstance(raw, list):
        raise SourceError(f'INE {metric}: table response is not a list')
    # INE DATOS_TABLA returns Nombre and Data, but may omit the Id field.
    # Select the exact published total-series label, not any subgroup/variation.
    expected_names = {
        'arrivals': 'turista. total nacional. dato base.',
        'spending': 'total. turista. gasto total. total nacional. dato base.',
        'tourism_gdp': 'producto interior bruto turistico, precios corrientes: porcentaje sobre el pib',
    }
    expected = _clean(expected_names[metric]).rstrip('.')
    matches = [
        item for item in raw
        if _clean(item.get('Nombre', '')).rstrip('.') == expected
    ]
    if len(matches) != 1:
        sample = [str(x.get('Nombre', ''))[:140] for x in raw[:30]]
        raise SourceError(
            f'INE {metric}: expected exact named series once, found {len(matches)}. '
            f'Candidates: {sample}'
        )
    selected = matches[0]
    observations = selected.get('Data', selected.get('data', []))
    if not isinstance(observations, list):
        raise SourceError(f'INE {metric}: missing Data list')
    items = []
    for item in observations:
        val = item.get('Valor')
        if val is None:
            continue
        try:
            if metric == 'tourism_gdp':
                # INE annual satellite-account observations can have NombrePeriodo
                # such as "2024(A)" rather than a Fecha timestamp.
                label = str(item.get('NombrePeriodo', ''))
                year = re.search(r'\b(?:19|20)\d{2}\b', label)
                if not year:
                    continue
                period = year.group()
            else:
                stamp = item.get('Fecha')
                if stamp is None:
                    continue
                dt = datetime.fromtimestamp(int(stamp) / 1000, tz=timezone.utc)
                period = dt.strftime('%Y-%m')
            items.append({'period': period, 'value': float(val)})
        except (ValueError, TypeError, OSError):
            continue
    if not items:
        sample = observations[:3]
        raise SourceError(
            f'INE {metric}: selected series has no valid observations; '
            f'observation count={len(observations)}, sample={sample!r}'
        )
    df = pd.DataFrame(items).drop_duplicates('period').sort_values('period')
    if metric == 'tourism_gdp':
        # The modern INE table has only 2021+; supplement its verified history
        # from INE's consolidated DCE89 series. Live table takes precedence if
        # INE later expands its historical coverage.
        history = pd.DataFrame(
            [{'period': year, 'value': value}
             for year, value in INE_TOURISM_GDP_HISTORY.items()]
        )
        df = (pd.concat([history, df], ignore_index=True)
              .drop_duplicates('period', keep='last')
              .sort_values('period')
              .reset_index(drop=True))
    if metric == 'arrivals':
        df['value'] /= 1_000_000
    elif metric == 'spending':
        df['value'] /= 1000
    if metric == 'tourism_gdp' and not df['value'].between(1, 40).all():
        raise SourceError('INE tourism GDP: implausible percentage; check series dimensions')
    return df


def retrieve(metric):
    if metric in ('arrivals','spending','tourism_gdp'):
        return ine_series(metric)
    if metric=='gdp_growth':
        return eurostat_series('namq_10_gdp', {'geo':'ES','freq':'Q','unit':'CLV_PCH_SM','s_adj':'SCA','na_item':'B1G'})
    if metric=='travel_balance':
        return eurostat_series('bop_its6_det', {'geo':'ES','freq':'A','currency':'MIO_EUR',
            'bop_item':'SD','stk_flow':'BAL','partner':'WRL_REST'}, scale=.001)
    if metric=='current_account':
        return eurostat_series('tipsbp41', {'geo':'ES','freq':'Q','unit':'PC_GDP',
            's_adj':'NSA','stk_flow':'BAL','bop_item':'CA','partner':'WRL_REST'})
    raise KeyError(metric)


def validate(metric, df):
    if df.empty or df['period'].duplicated().any(): raise SourceError(f'{metric}: empty/duplicate periods')
    if not pd.to_numeric(df.value,errors='coerce').notna().all(): raise SourceError(f'{metric}: non-numeric values')
    thresholds={'arrivals':(0,25),'spending':(0,40),'tourism_gdp':(0,40),
                'gdp_growth':(-40,40),'travel_balance':(-100,150),'current_account':(-35,35)}
    lo,hi=thresholds[metric]
    if not df.value.between(lo,hi).all(): raise SourceError(f'{metric}: out-of-range value; verify source/unit')
    return df.sort_values('period').reset_index(drop=True)


def load_snapshot(folder='data'):
    path = Path(folder) / 'snapshot.json'
    if path.exists():
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise SourceError('Snapshot must be a JSON object')
        data.setdefault('series', {})
        data.setdefault('errors', {})
        return data
    return {
        'last_successful_refresh_utc': None,
        'last_attempt_utc': None,
        'series': {},
        'errors': {},
    }
