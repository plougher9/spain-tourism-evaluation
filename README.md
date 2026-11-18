# Spain | Tourism & External Exposure

**Research question:** Is Spain's growing reliance on international tourism strengthening its economy or increasing vulnerability to external shocks?

## Dashboard narrative and interaction

The main page now leads with an evidence-based interpretation organized into five exhibits:

1. **Growth (2019 = 100):** compare annual international tourist arrivals with *nominal* visitor spending. Only full 12-month years enter this chart. Fixed 2019 baselines remain constant as the visible date range changes.
2. **COVID-era shock:** show the Eurostat annual balance of travel-services exports less imports. Highlight the 2019–2020 collapse and subsequent recovery.
3. **Economic dependence:** present INE tourism share of GDP, carefully labeling the 2015, 2016–2020 and 2021+ methodological breaks.
4. **International finance:** place real GDP growth and current-account balance in context, without claiming they are caused solely by tourism.
5. **Sensitivity analysis:** vary a hypothetical **percentage reduction in the net travel-services surplus** for a chosen historical year. The scenario is a simple accounting illustration: `stressed surplus = observed travel surplus × (1 − shock%)`. It is **not a forecast**, a direct estimate of travel receipts, or a modeled impact on GDP/current account.

The sidebar's inclusive calendar-year range filters the charts; the historic 2020 shock headline remains a fixed benchmark and is labeled as such. The six original source charts remain accessible in the **Original six source charts and headline readings** expander. The source dictionary, official publisher links, refresh timestamps and verification guidance are retained below.

### Automated quality check

The additional `.github/workflows/validate-dashboard.yml` workflow validates Python syntax, derived-year calculations, and a Streamlit page render on changes to dashboard code. This check is **separate** from the scheduled official-data refresh.

## Six indicators

| Series | Frequency | Original source |
|---|---|---|
| International tourist arrivals (millions) | Monthly | Spain INE FRONTUR |
| International tourist spending (€ billion, nominal) | Monthly | Spain INE EGATUR |
| Tourism's share of GDP (%) | Annual | Spain INE Tourism Satellite Account |
| Real GDP growth (YoY %) | Quarterly | Eurostat namq_10_gdp |
| Travel-services balance (€ billion) | Annual | Eurostat bop_its6_det |
| Current-account balance (% GDP) | Quarterly | Eurostat tipsbp41 |

The arrival series measures foreign demand; spending measures nominal foreign receipts; GDP share measures domestic reliance; GDP growth is the macroeconomic context; the travel balance and current account link tourism to balance-of-payments risks. These indicators support a descriptive assessment, not a causal attribution.

## Install and run

```bash
pip install -r requirements.txt
python refresh.py
streamlit run app.py
```

**Live data:** The dashboard retrieves six official datasets. Spain's tourism share of GDP combines the current INE Tourism Satellite Account table (2021 onward) with published historical observations for 2015–2020 from INE official SDG series [DCE89](https://www.ine.es/consul/serie.do?L=0&d=true&s=DCE89). Historical observations are documented official figures (not synthetic); scheduled refreshes retain them. Check current workflow logs and independently verify one published observation per dataset before submission. A failed refresh exits nonzero, records the failure and retains older valid series rather than fabricating data.

## GitHub Actions automation

`.github/workflows/refresh.yml` runs on Mondays at 08:18 UTC and also offers **Actions → Refresh Spain tourism dashboard data → Run workflow**. It retrieves all series, performs numeric/range/duplicate validation, and commits `data/snapshot.json` plus `data/latest_observations.csv`. Streamlit redeploys when the repository updates. The timestamp **last successful refresh** advances only if *all six* series pass; failure keeps previously available series and marks errors rather than replacing them with made-up figures. Scheduled workflows may be delayed or disabled in inactive public repositories; monitor runs.

## Verify refresh for the assignment

1. In the GitHub **Actions** tab, manually dispatch the refresh workflow. Save a screenshot of a successful run including the run timestamp and commit.
2. Check that the app's *last successful refresh* advances to the new timestamp and that updated observations appear.
3. Open each linked official data source. Match the *latest observation period*, *unit*, *geography*, and *published value*. Record one observation for each series in `data/verification.csv`.
4. Save evidence of six publisher comparisons and the successful workflow run. If any series fails, fix the series ID/filter instead of claiming verification.
5. Summarize the findings and limitations in the required memo (500 words maximum).

## Methodological notes

- Series are different frequencies. Do not interpret a 2024 tourism-to-GDP share as a 2026 share.
- **Tourism GDP methodological break:** INE DCE89 documents Base 2010 for 2015, Statistical Revision 2019 for 2016–2020, and Statistical Revision 2024 for 2021 onward. Long-run comparisons across these years are descriptive and may reflect both genuine economic change and statistical revisions. The source's historical observations are explicitly documented and preserved by refreshes.
- EGATUR nominal visitor spending is not value added, not real spending, and not identical to Eurostat BPM6 travel credits.
- Tourism's GDP contribution is a broad satellite-account measure and should not be confused with the narrower services-account travel balance.
- GDP growth and the current account are influenced by many non-tourism factors.
- Source tables may be revised; recorded verification values must include an observation date.
- The INE APIs sometimes encode periods as timestamps; inspect the exact source period frequency and units for the chosen series.

## Deliverables

Submit the deployed Streamlit link, repository code, these setup/refresh instructions, one-observation-per-series verification evidence, successful scheduled/manual refresh evidence, and a memo of at most 500 words answering the research question, limitations, and your use of AI.
