# Spain | Tourism & External Exposure

**Research question:** How does international tourism strengthen Spain's economy, and where does it leave the country vulnerable to external shocks?

## Visitor-country concentration (Part 4)

Part 4 now includes a compact, year-filtered exhibit of the **three largest individual countries' share of international arrivals**, plus the **UK share**. This is a structural-risk indicator: a lower top-three share suggests broader diversification and potentially less reliance on a few tourism markets. The UK remains a significant visitor origin, so pound/euro movements can affect British travellers' purchasing power even as Spain diversifies. **No currency-tourism causal relationship is claimed**; exploratory EUR/GBP and EUR/USD correlations were inconsistent across sample periods. France and Germany use the euro and do not carry the same bilateral EUR/GBP exposure.

The official observations come from [INE FRONTUR, country of residence](https://www.ine.es/jaxiT3/files/t/csv_bdsc/10822.csv), aggregated from complete calendar years and saved to `data/visitor_concentration.json`. In 2019, the top three markets accounted for 48.28% of arrivals; in 2025, 45.35%. The UK share moved from 21.57% to 19.71%. These are *arrival* shares—not spending or net travel balance shares. Some smaller individual countries are not reported consistently for all months, so the standalone script only ranks individual markets with complete observations; it does not invent missing countries' figures or compute a purported all-country HHI. To refresh, run `python analysis_experiments/concentration_seasonality_test.py`; the separate GitHub workflow can also be used. The original six source series and finance indicators remain unchanged.

## Reader's guide: four-chapter argument

The reader-facing dashboard is organized in this order:

1. **01 · How important is tourism to Spain's finances?** An annual euro-denominated balance-of-payments component chart uses a shared zero axis: travel and other services appear as independent positive bars, while goods/income/transfers appear below zero when negative. A separate total bar explains net travel, other services, and the remainder (goods plus income and transfers) summing to the reported current-account balance. A **Remove travel contribution / Restore travel contribution** button removes the net travel balance *arithmetically* and changes the displayed total and explanation. In 2025 the accounting result changes from +€54.829B to −€15.631B. This is **not** a no-tourism economic forecast. The exact component math stays visible under the chart; multi-year lines are optional.
2. **02 · Is Spain becoming more dependent on tourism?** INE tourism share of GDP is shown with statistical-revision caveats, rather than presuming record tourism earnings imply increasing GDP dependence.
3. **03 · Is Spain earning more per visitor after inflation?** Two connected charts first compare annual visitor arrivals and nominal spending (both indexed to 2019 = 100), then compare nominal and consumer-price-adjusted **spending per visitor** as percentage changes versus 2019. The first chart shows spending outpacing visitor numbers; the second tests how much of the per-visitor increase remains after broad Spanish inflation. The two lines in the first chart are **not additive stacked quantities**. Each chart has its own **Show the math** dropdown: the first spells out the 2019-based arrival/spending indices and shows how dividing the two indices relates to nominal spending per visitor; the second calculates nominal and HICP-adjusted spending per visitor. The explanation distinguishes general price inflation from tourism-specific inflation and shows their multiplicative relationship. This proxy is not a tourism-specific deflator.
4. **04 · When does tourism create vulnerability—and when does it provide resilience?** The annual travel-services chart contrasts the COVID-19 collapse with recovery during the 2022 energy-price shock. A second, compact chart shows the top-three source countries' share of arrivals and the large remaining UK share, explaining geographic diversification and potential pound/euro exposure. The more detailed Eurostat goods-versus-travel-versus-current-account comparison lives under **Explore further**; these balance-of-payments categories are not additive.
**After Chapter 4:** An optional **Explore further** section offers supporting comparisons, the hypothetical travel-surplus stress illustration and a separately dated Banco de España release. The full synthesis and interpretation belong in the assignment's ≤500-word memo, rather than a repeated overall-analysis chapter in the app.

All charts label their axis units and periods, and the year slider limits visible history. The 2025 financial benchmark and the explicit 2019-based Chapter 3 comparisons remain fixed reference analyses; the Part 4 concentration comparison follows the selected range. Original official-source data, refresh processes, and verification controls remain unchanged. The chart renderer uses server-side images rather than browser-side Plotly for the four main exhibits, retaining the earlier performance fix. The tourism GDP chart has padded horizontal bounds and no overlapping single-series legend, so the first visible year (often 2019) is readable.

## Analytical findings: quality of growth and external financial role

The dashboard now tests two hypotheses **before** the original shock narrative:

**1. Is Spain obtaining more value per visitor after inflation?** Annual INE EGATUR tourist expenditure in euros is divided by annual INE FRONTUR visitor arrivals to calculate *nominal spending per international visitor*. Annual [Eurostat all-items HICP](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table) is used to derive a **consumer-price-adjusted proxy expressed in 2019 euros**: nominal spending per visitor × HICP(2019)/HICP(year). It uses only complete 12-month arrival/spending years. This proxy is **not an official tourism-services price deflator**, not tourism value added, and may not track tourists' actual purchase basket. It is a useful inflation sensitivity, not a precise real-tourism measure.

**2. Does net travel meaningfully support Spain's external position?** The original annual Eurostat travel-services balance (`bop_its6_det`, SD, BAL, € billion) is compared with the [Eurostat annual balance-of-payments current account](https://ec.europa.eu/eurostat/databrowser/view/bop_c6_a/default/table), converted from million euros to € billion and restricted to the same years. The dashboard also reads Eurostat total international services balance. Travel as a share of total *net services balance* is shown when that balance is positive. The chart's **current account excluding net travel** means current account minus net travel balance. It is an *accounting remainder*, **not** a hypothetical economy without tourism and not a causal estimate. This remainder includes goods, other services, primary and secondary income.

The supplemental Eurostat observations are stored in `data/analysis.json` and updated by the independent `.github/workflows/refresh-analysis.yml` workflow on Mondays and on manual dispatch. The original six-source refresh is unchanged. If a supplemental source fails, existing valid observations are retained and an explicit error is saved; missing figures are not guessed. The spending-per-visitor comparison uses an interactive Altair chart; other main exhibits use server-side Matplotlib rendering. Chapter 3's visible history respects the selected inclusive years, while growth is explicitly measured against the fixed 2019 baseline. Part 4 concentration changes compare the selected first and last available observations.

Using the November 18, 2026 snapshot, the 2019–2025 nominal spending-per-visitor increase is roughly **26.5%**, but only **4.1%** using Spain's consumer-price proxy. In 2025 the travel surplus (€70.46 billion) is about **62.1%** of the total services surplus (€113.48 billion); total current-account balance is €54.829 billion, giving an arithmetic remainder of **−€15.631 billion**. These findings should be refreshed and rechecked against the latest publisher values before submission.

## Dashboard narrative and interaction

The current application is a **four-chapter evidence dashboard**, not the earlier standalone five-chart prototype. Brief chapter-level interpretations remain beside each chart, while the integrated answer to the research question, limitations and AI-use disclosure belong in the separate required memo (maximum 500 words). There is deliberately no standalone overall-analysis section in the app. Chapter 1 explains the annual Eurostat balance-of-payments bridge and offers an accounting-only **Remove travel contribution** toggle. Chapter 2 examines INE's tourism share of GDP and its statistical-revision breaks. Chapter 3 contrasts arrivals, nominal spending and an HICP-adjusted spending-per-visitor proxy. Chapter 4 compares the COVID-19 and 2022 energy-price shocks, then tests source-market concentration from official INE arrivals.

The year-range control filters the relevant annual charts and the new source-market comparison. Chapter 4's concentration change is calculated **from the first available year in the selected range to its last year** (for example, 2016 to 2025: 53.3% to 45.4%, or −7.9 percentage points). It is not fixed to 2019. The headline 2025 balance-of-payments benchmark and Chapter 3's 2019-based inflation/index comparisons remain explicitly fixed analytical references even when the visible history is filtered. The original six official source series are retained, but redundant raw source charts are no longer part of the main page.

The full-data dictionary, official links and source-check guidance are collapsed into **Data dictionary & independent validation** below the narrative. **Explore further** keeps the goods-versus-current-account comparison, an arithmetic stress illustration and a separately dated Banco de España rolling-balance release available without distracting from the four-chapter argument.

### Conclusions and evidence boundaries

**Financial contribution:** The 2025 €70.46 billion net travel-services surplus exceeds the €54.83 billion current-account surplus. Subtracting travel produces an accounting remainder, not a no-tourism forecast.

**Purchasing-power quality:** From 2019 to 2025, nominal spending per visitor increased about 26.5%, versus approximately 4.1% adjusted by Spain-wide HICP. HICP is a general consumer-price proxy, not a tourism price deflator or a measure of tourism GDP/value added.

**Dependence and shocks:** Tourism-GDP estimates do not establish continuously growing reliance, especially across revisions. The COVID collapse shows vulnerability to a direct travel shock; the recovery in 2022 alongside energy-price pressures shows a different historical response, not proof of causal offset.

**Structural resilience with remaining exposure:** The three largest individual source markets' share of arrivals fell from 53.3% in 2016 to 45.4% in 2025. This suggests geographic diversification, while the UK's 19.7% share in 2025 still creates *potential* purchasing-power exposure to EUR/GBP movements. Arrival shares cannot establish expenditure concentration or exchange-rate-driven demand effects. Earlier exploratory FX correlations varied by period and are not presented as a core finding.

### Automated quality check

The additional `.github/workflows/validate-dashboard.yml` workflow validates Python syntax, derived-year calculations, and a Streamlit page render on changes to dashboard code. This check is **separate** from the scheduled official-data refresh.

## 2022 energy-price shock and tourism resilience

Part 4 features an annotated annual net travel-services history (COVID-19 and the 2022 energy crisis), followed by the visitor-country concentration analysis. An optional **Explore further** comparison groups Eurostat BPM6 **goods, travel and current-account balances**. Official goods balances are fetched independently from `bop_c6_a` as `bop_item=G`, and stored in `data/analysis.json`. If this optional indicator is unavailable, the grouping is withheld instead of substituting an unverified estimate. The 2022 contrast shows tourism earnings recovering despite external financial pressure, but the **goods balance is not the energy balance**: goods include energy and non-energy trade. The goods series is an additional officially retrieved Eurostat indicator.

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

## INE monthly reference-period correction (November 18, 2026)

The INE Tempus monthly observations are timestamped at **midnight in mainland Spain**. Interpreting these timestamps in UTC instead of `Europe/Madrid` can incorrectly label a September observation as August. `sources.py` now uses Spain's local calendar month, and the official-data refresh reloaded the saved series. September 2026 FRONTUR reports **10,139,650 international arrivals** and EGATUR reports approximately **€14.488 billion in nominal tourist spending**, independently confirmed by the corresponding INE September releases. Correcting all affected month labels also corrects the calendar-year spending and arrivals aggregates and therefore Part 3 derived growth rates. The 2019–2025 changes are now approximately **26.5% nominal** and **4.1% HICP-adjusted** spending per visitor. The separately sourced rolling August 2026 Banco de España financial release is not affected.

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
