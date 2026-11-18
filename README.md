# Spain | Tourism & External Exposure

**Research question:** Is Spain's growing reliance on international tourism strengthening its economy or increasing vulnerability to external shocks?

## Analytical findings: quality of growth and external financial role

The dashboard now tests two hypotheses **before** the original shock narrative:

**1. Is Spain obtaining more value per visitor after inflation?** Annual INE EGATUR tourist expenditure in euros is divided by annual INE FRONTUR visitor arrivals to calculate *nominal spending per international visitor*. Annual [Eurostat all-items HICP](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table) is used to derive a **consumer-price-adjusted proxy expressed in 2019 euros**: nominal spending per visitor × HICP(2019)/HICP(year). It uses only complete 12-month arrival/spending years. This proxy is **not an official tourism-services price deflator**, not tourism value added, and may not track tourists' actual purchase basket. It is a useful inflation sensitivity, not a precise real-tourism measure.

**2. Does net travel meaningfully support Spain's external position?** The original annual Eurostat travel-services balance (`bop_its6_det`, SD, BAL, € billion) is compared with the [Eurostat annual balance-of-payments current account](https://ec.europa.eu/eurostat/databrowser/view/bop_c6_a/default/table), converted from million euros to € billion and restricted to the same years. The dashboard also reads Eurostat total international services balance. Travel as a share of total *net services balance* is shown when that balance is positive. The chart's **current account excluding net travel** means current account minus net travel balance. It is an *accounting remainder*, **not** a hypothetical economy without tourism and not a causal estimate. This remainder includes goods, other services, primary and secondary income.

The supplemental Eurostat observations are stored in `data/analysis.json` and updated by the independent `.github/workflows/refresh-analysis.yml` workflow on Mondays and on manual dispatch. The original six-source refresh is unchanged. If a supplemental source fails, existing valid observations are retained and an explicit error is saved; missing figures are not guessed. The new visitor-yield chart is rendered server-side to prevent browser-side chart freezes. Both analytical charts respect the sidebar's selected inclusive calendar years; their last available observations and displayed summary cards update with the selection. Historical reference benchmarks remain fixed and explicitly labeled.

Using the November 18, 2026 snapshot, the 2019–2025 nominal spending-per-visitor increase is roughly **26.8%**, but only **4.4%** using Spain's consumer-price proxy. In 2025 the travel surplus (€70.46 billion) is about **62.1%** of the total services surplus (€113.48 billion); total current-account balance is €54.829 billion, giving an arithmetic remainder of **−€15.631 billion**. These findings should be refreshed and rechecked against the latest publisher values before submission.

## Dashboard narrative and interaction

The main page now leads with an evidence-based interpretation organized into five exhibits:

1. **Growth (2019 = 100):** compare annual international tourist arrivals with *nominal* visitor spending. Only full 12-month years enter this chart. Fixed 2019 baselines remain constant as the visible date range changes.
2. **COVID-era shock:** show the Eurostat annual balance of travel-services exports less imports. Highlight the 2019–2020 collapse and subsequent recovery.
3. **Economic dependence:** present INE tourism share of GDP, carefully labeling the 2015, 2016–2020 and 2021+ methodological breaks.
4. **International finance:** place real GDP growth and current-account balance in context, without claiming they are caused solely by tourism.
5. **Sensitivity analysis:** vary a hypothetical **percentage reduction in the net travel-services surplus** for a chosen historical year. The scenario is a simple accounting illustration: `stressed surplus = observed travel surplus × (1 − shock%)`. It is **not a forecast**, a direct estimate of travel receipts, or a modeled impact on GDP/current account.

The sidebar's inclusive calendar-year range filters both new analytical charts and the original dashboard charts. The spending-per-visitor chart starts in 2016 because 2015 monthly arrivals/spending observations are incomplete; the annual external-accounts comparison starts in 2015. The spending-per-visitor index always uses 2019 = 100 even when 2019 is outside the visible window. The historic 2020 shock headline remains a fixed benchmark and is labeled as such. The six original source charts remain accessible in the **Original six source charts and headline readings** expander. The source dictionary, official publisher links, refresh timestamps and verification guidance are retained below.

### Automated quality check

The additional `.github/workflows/validate-dashboard.yml` workflow validates Python syntax, derived-year calculations, and a Streamlit page render on changes to dashboard code. This check is **separate** from the scheduled official-data refresh.

## 2022 energy-price shock and tourism resilience

The narrative adds a separately labeled **2022 energy-price shock / tourism resilience** exhibit, contrasting full-year INE EGATUR nominal tourism spending and Eurostat travel-services surplus in 2021 and 2022. The indexed spending/visitor chart and the annual travel-balance chart also identify 2022. These observations are calculated dynamically from the six existing official series, and no energy-import data or extra indicator has been invented.

Historical context is based on the [IMF 2022 Article IV report, published in January 2023](https://www.imf.org/en/publications/cr/issues/2023/01/19/spain-2022-article-iv-consultation-press-release-staff-report-and-statement-by-the-528338), which describes tourism and services recovery alongside higher energy import costs. **Interpretation limitation:** the charts alone do not measure Spain's energy import bill, isolate causal effects, or prove exactly how much of the energy shock tourism offset. This comparison illustrates a different transmission channel from the 2020 pandemic shock.

## Latest published tourism balance (separate from annual history)

A separately labeled **Banco de España release snapshot** shows a rolling 12-month tourism surplus of **€74.9 billion** for the 12 months ending **August 2026**, compared with **€71.1 billion** for the 12 months ending August 2025. The same release reports the rolling tourism surplus at **4.3% of GDP**. Original release: [Banco de España, published October 30, 2026](https://www.bde.es/wbe/es/noticias-eventos/actualidad-banco-espana/balanza-de-pagos-mensual-agosto-2026.html).

The published values and citation are stored in `data/bde_travel_rolling12.json` and displayed in the international-finance section. **This release snapshot is not automatically updated** by the scheduled six-series data workflow. It is not 2026 annual data and must not be spliced into the 2015–2025 annual Eurostat travel balance. The reported **4.3% is a tourism balance relative to GDP**, not tourism's contribution to GDP (last INE Satellite Account year: 2024). Review and update this snapshot when a newer Banco de España release is independently verified.

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
