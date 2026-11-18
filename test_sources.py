"""Offline unit tests; do not substitute for a successful network refresh."""
from unittest.mock import patch
import pandas as pd
from sources import eurostat_series, validate, SourceError

def test_eurostat_single_series_jsonstat_index():
    result={'id':['geo','time'],'size':[1,3], 'dimension':{'time':{'category':{'index':{'2025-Q1':0,'2025-Q2':1,'2025-Q3':2}}}}, 'value':{'0':1.1,'2':2.3}}
    with patch('sources.http_json',return_value=result):
        df=eurostat_series('mock',{'geo':'ES'})
    assert df.to_dict('records')==[{'period':'2025-Q1','value':1.1},{'period':'2025-Q3','value':2.3}]

def test_ambiguous_dimensions_raise():
    result={'id':['geo','time'],'size':[2,1], 'dimension':{'time':{'category':{'index':{'2025-Q1':0}}}},'value':{'0':1}}
    with patch('sources.http_json',return_value=result):
        try:
            eurostat_series('mock',{'geo':'ES'})
        except SourceError as exc:
            assert 'ambiguous' in str(exc)
        else: raise AssertionError('Must reject ambiguous data')

def test_duplicate_dates_raise():
    try:validate('arrivals',pd.DataFrame([{'period':'2026-01','value':5},{'period':'2026-01','value':6}]))
    except SourceError:pass
    else:raise AssertionError('Must reject duplicate date')

if __name__=='__main__':
    test_eurostat_single_series_jsonstat_index()
    test_ambiguous_dimensions_raise()
    test_duplicate_dates_raise()
    print('3 offline parser/validation tests passed')
