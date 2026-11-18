"""Spain tourism: data-first international finance dashboard."""
from datetime import datetime, timezone
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sources import SPECS, load_snapshot
from story_sections import render_story

st.set_page_config(page_title='Spain | Tourism & External Exposure',page_icon='🇪🇸',layout='wide')
ROOT=Path(__file__).resolve().parent
st.markdown('''<style>
.stApp{background:#f5f7f8;color:#163142}.block-container{max-width:1400px;padding-top:1.5rem}
.hero{background:linear-gradient(110deg,#112d40,#23566b);padding:27px 34px;border-radius:16px;color:white;margin:4px 0 18px}
.hero h1{font-size:2rem;color:white;margin:4px 0}.hero small{color:#c9e3e7;letter-spacing:.11em;font-weight:700}
.hero p{color:#e3f0f2;margin-bottom:0;max-width:950px}.panel{background:white;border:1px solid #e1e9ea;border-radius:13px;padding:14px 18px;margin:4px 0}
.muted{color:#5f7180;font-size:.84rem}.metric-val{font-size:2rem;color:#14364a;font-weight:800}.eyebrow{letter-spacing:.12em;color:#577786;font-size:.74rem;font-weight:800}
.section{font-size:1.1rem;font-weight:800;color:#15374a;padding-top:14px}
.story-chapter{font-size:1.19rem;font-weight:800;color:#15374a;margin:22px 0 7px;padding:12px 0 6px;border-top:1px solid #d7e2e6}
.narrative-lead{background:#eaf3f3;border-left:4px solid #16848c;border-radius:9px;padding:18px 21px;margin:8px 0 20px;color:#183c4c;line-height:1.65}
.narrative-conclusion{background:#f0f4f6;border-radius:12px;padding:18px 22px;margin:16px 0 25px;line-height:1.65;color:#183c4c}
div[data-testid="stMetric"]{background:white;border:1px solid #e3e9ed;padding:16px;border-radius:12px}
</style>''',unsafe_allow_html=True)
st.markdown('''<div class="hero"><small>COUNTRY INTELLIGENCE / INTERNATIONAL FINANCE</small>
<h1>Spain · Tourism & External Exposure</h1><p>Is Spain's growing reliance on international tourism strengthening its economy or increasing vulnerability to external shocks?</p></div>''',unsafe_allow_html=True)

snapshot=load_snapshot(ROOT/'data')
series=snapshot.get('series',{})
failures=snapshot.get('errors',{})
last=snapshot.get('last_successful_refresh_utc')
updated=snapshot.get('updated_this_run',[])
complete=len(series)==len(SPECS) and last is not None

# All frequencies store a calendar year at the start of their period:
# 2024 (annual), 2024-Q2 (quarterly), 2024-09 (monthly).
available_years = [
    int(str(obs['period'])[:4])
    for entry in series.values()
    for obs in entry.get('observations', [])
    if str(obs.get('period', ''))[:4].isdigit()
]
earliest_year = min(available_years) if available_years else 2015
latest_year = max(available_years) if available_years else datetime.now(timezone.utc).year
default_start_year = max(earliest_year, latest_year - 7)

def observations_in_years(observations, start_year, end_year):
    """Keep all observations belonging to selected inclusive calendar years."""
    return [
        obs for obs in observations
        if str(obs.get('period', ''))[:4].isdigit()
        and start_year <= int(str(obs['period'])[:4]) <= end_year
    ]

with st.sidebar:
    st.markdown('## Data & controls')
    st.write('**Latest full-source refresh**')
    st.write(last or 'Not yet completed')
    st.caption('Timestamps are UTC. The date of the statistical observation appears on each chart separately.')
    st.write('**Source completeness**')
    st.progress(len(series)/len(SPECS),text=f'{len(series)} of {len(SPECS)} source series available')
    show_raw=st.checkbox('Show full source observations',value=False)
    selected_years = st.slider(
        'Calendar years shown',
        min_value=earliest_year,
        max_value=latest_year,
        value=(default_start_year, latest_year),
        step=1,
        help='Applied to all six charts and the three summary metrics. Years are inclusive.'
    )
    start_year, end_year = selected_years
    st.caption(f'Showing observations from {start_year} through {end_year}. '
               'Series with no observations in this range will be clearly marked.')
    st.info('Scheduled refresh: GitHub Actions every Monday. A page reload reads the latest committed snapshot; it does not contact sources directly.')
    if st.button('Reload saved snapshot'):
        st.rerun()
    st.divider()
    st.markdown('**Methods**')
    st.caption('No interpolation, synthetic history, mixing of frequencies, or automatic conversion of nominal spending into real growth. All figures are descriptive, not causal estimates.')

if failures:
    with st.expander(f'⚠️ {len(failures)} data-source issue(s) from last retrieval — inspect before submission',expanded=not complete):
        for key,error in failures.items(): st.warning(f'**{SPECS[key]["title"]}:** {error}')
if not series:
    st.error('No verified historical series has been retrieved yet. Run `python refresh.py` and commit `data/snapshot.json`. The dashboard intentionally does not fabricate series.')
    st.info('Use `python refresh.py --discover` to inspect INE table IDs, then set exact INE series IDs in `sources.py`. Eurostat requests use explicit dimension filters.')

def parse_date(period):
    p=str(period)
    try:
        if '-Q' in p:
            yr,q=p.split('-Q');return pd.Timestamp(int(yr),1+3*(int(q)-1),1)
        if '-' in p: return pd.Timestamp(p+'-01')
        return pd.Timestamp(int(p),1,1)
    except Exception:return pd.NaT


def graph(key):
    spec=SPECS[key]
    entry=series.get(key, {})
    obs=entry.get('observations',[])
    with st.container(border=True):
        st.markdown(f'**{spec["title"]}**')
        if key == 'tourism_gdp':
            st.caption('INE historical series DCE89: statistical bases differ in 2015, 2016–2020, '
                       'and 2021 onward. Use caution when comparing levels across these breaks.')
        if obs:
            df=pd.DataFrame(obs)
            df['date']=df.period.map(parse_date)
            df=df.dropna(subset=['date']).sort_values('date')
            window=df[df.date.dt.year.between(start_year, end_year)]
            if window.empty:
                first_period=obs[0]['period']
                last_period=obs[-1]['period']
                st.info(f'No observations for {start_year}–{end_year}. '
                        f'This series currently covers {first_period} through {last_period}.')
                st.caption(f'{spec["unit"]} | {spec["freq"]} | '
                           f'[{spec["source"]}]({spec["url"]}) | '
                           f'Latest published observation: {last_period}')
                with st.expander('Why this indicator?'):
                    st.write(spec['why'])
                    st.caption(f'Last source retrieval: {entry.get("refreshed_utc","none")}')
                return
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=window.date,y=window.value,mode='lines+markers',
                                     line=dict(color='#147a86',width=2.5),marker=dict(size=4),name=spec['title'],
                                     hovertemplate='%{x|%Y-%m}: %{y:,.2f}<extra></extra>'))
            fig.update_layout(height=240,margin=dict(l=2,r=8,t=5,b=8),
                              paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                              xaxis=dict(showgrid=False,range=[f'{start_year}-01-01',f'{end_year}-12-31']),
                              yaxis=dict(gridcolor='#e9eef2',title=spec['unit']),showlegend=False)
            st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
            latest=window.iloc[-1]
            source_latest=obs[-1]['period']
            st.caption(f'**{latest["value"]:,.2f}** · {latest["period"]} (latest in selected range) | '
                       f'{spec["unit"]} | {spec["freq"]} | [{spec["source"]}]({spec["url"]})'
                       f' | Source latest: {source_latest}')
            if key not in updated and failures.get(key):
                st.caption('⚠️ Last update failed; this series is retained from an earlier snapshot.')
        else:
            st.warning('Series unavailable — official source retrieval or configuration required.')
            st.caption(f'{spec["unit"]} | {spec["freq"]} | [{spec["source"]}]({spec["url"]})')
        with st.expander('Why this indicator?'):
            st.write(spec['why'])
            st.caption(f'Last source retrieval: {entry.get("refreshed_utc","none")}')


def render_original_sources():
    present_cols=st.columns(3)
    for i,key in enumerate(('arrivals','spending','tourism_gdp')):
        spec=SPECS[key]; row=series.get(key,{}); data=row.get('observations',[])
        visible=observations_in_years(data,start_year,end_year)
        latest=visible[-1] if visible else None
        with present_cols[i]:
            if latest:
                st.metric(spec['title'],f'{latest["value"]:,.2f}',help=spec['unit'])
                st.caption(f'{spec["unit"]} · {latest["period"]} · {spec["source"]} · selected range')
            elif data:
                st.metric(spec['title'],'No data in range')
                st.caption(f'Available through {data[-1]["period"]} · {spec["source"]}')
            else:
                st.metric(spec['title'],'No verified data')
                st.caption(f'{spec["unit"]} · {spec["source"]}')



    st.markdown('<div class="section">01 / Tourism demand</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a: graph('arrivals')
    with b: graph('spending')
    st.markdown('<div class="section">02 / Domestic economic reliance</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a: graph('tourism_gdp')
    with b: graph('gdp_growth')
    st.markdown('<div class="section">03 / External financial position</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a: graph('travel_balance')
    with b: graph('current_account')


render_story(series, SPECS, start_year, end_year)

with st.expander('Original six source charts and headline readings', expanded=False):
    st.caption('Source-level evidence, filtered to the selected inclusive calendar years.')
    render_original_sources()

st.markdown('<div class="section">Data dictionary & independent validation</div>',unsafe_allow_html=True)
rows=[]
for key,spec in SPECS.items():
    entry=series.get(key,{})
    obs=entry.get('observations',[])
    lastobs=obs[-1] if obs else {}
    rows.append({'Indicator':spec['title'],'Units':spec['unit'],'Frequency':spec['freq'],
                 'Publisher':spec['source'],'Latest period':lastobs.get('period','Unavailable'),
                 'Latest value':lastobs.get('value'),'Last series update (UTC)':entry.get('refreshed_utc','—'),
                 'Status':'Available' if obs else 'Source unavailable'})
table=pd.DataFrame(rows)
st.dataframe(table,hide_index=True,use_container_width=True)

with st.expander('How to independently verify one observation per series'):
    st.markdown('Use the **Data dictionary** table above to read the period and latest value. Open each publisher link below, filter to the exact period, unit, and geography, and record the observed published value in `data/verification.csv`. Confirm all six against official data before treating refresh as verified.')
    for key,spec in SPECS.items():
        st.markdown(f'- [{spec["title"]}: {spec["source"]}]({spec["url"]})')
    ver_path=ROOT/'data'/'verification.csv'
    if ver_path.exists():
        st.dataframe(pd.read_csv(ver_path),hide_index=True,use_container_width=True)

if show_raw:
    all_obs=[]
    for key,entry in series.items():
        for o in entry.get('observations',[]):all_obs.append({'indicator':key,**o})
    if all_obs: st.dataframe(pd.DataFrame(all_obs),hide_index=True,use_container_width=True)
    st.download_button('Download historical observations (CSV)',pd.DataFrame(all_obs).to_csv(index=False).encode('utf-8'),'spain_tourism_observations.csv','text/csv')

st.markdown('---')
st.caption('Important: tourism spending is nominal and differs from tourism value added; the current account contains goods, services, income, and transfers. The travel-services balance is a narrower balance-of-payments concept than all tourism activity. Comparisons among monthly, quarterly, and annual charts do not establish causation.')
