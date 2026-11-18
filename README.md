# Spain | Tourism & External Exposure

**Research question:** Is Spain's growing reliance on international tourism strengthening its economy or increasing vulnerability to external shocks?

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

**IMPORTANT — first-run data setup:** This is an *honest source-connected starter*, not a pre-populated validated dashboard. Source requests cannot be executed in the authoring environment. The app initially has no fabricated data. Review the first refresh logs. Three INE series may need explicit IDs: run `python refresh.py --discover`, inspect the official national-total series, and add its ID to `INE_SERIES_IDS` in `sources.py`. Refresh again until all six series succeed. Check all outputs and units against the publishers before submitting. Eurostat filters may require adjustment if the publisher changes dimension codes. A failed refresh exits nonzero and lists the cause.

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
- EGATUR nominal visitor spending is not value added, not real spending, and not identical to Eurostat BPM6 travel credits.
- Tourism's GDP contribution is a broad satellite-account measure and should not be confused with the narrower services-account travel balance.
- GDP growth and the current account are influenced by many non-tourism factors.
- Source tables may be revised; recorded verification values must include an observation date.
- The INE APIs sometimes encode periods as timestamps; inspect the exact source period frequency and units for the chosen series.

## Deliverables

Submit the deployed Streamlit link, repository code, these setup/refresh instructions, one-observation-per-series verification evidence, successful scheduled/manual refresh evidence, and a memo of at most 500 words answering the research question, limitations, and your use of AI.
