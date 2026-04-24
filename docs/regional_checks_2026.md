# Regional Checks

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_regional_checks.py
```

## Generated Outputs

Figures:

- `outputs/figures/regional_progressive_bulgaria_share_2026.svg`
- `outputs/figures/regional_turnout_2026.svg`
- `outputs/figures/regional_turnout_pb_weighted_corr_2026.svg`

Tables:

- `outputs/tables/regional_summary_2026.csv`
- `outputs/tables/regional_attention_summary_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`
- `outputs/tables/regional_lead_stations_2026.csv`
- `outputs/tables/regional_strong_lead_stations_2026.csv`
- `outputs/tables/regional_checks_summary_2026.json`

## Summary

- Regions checked: `32`
- Stations checked: `12,721`
- Absolute high-turnout/high-share stations: `10`
- Relative high-turnout/high-share stations: `27`
- Positive regional residual lead stations: `425`
- Broad regional lead stations written to table: `446`
- Stronger multi-signal lead stations with score >= 2: `58`

Definitions:

- `relative_high_turnout_high_share`: turnout is at least 20 percentage points above the region turnout and Progressive Bulgaria share is at least 20 percentage points above the region share, with at least 50 valid candidate-list votes.
- `positive_residual_lead`: at least 50 Progressive Bulgaria votes above regional expectation and a binomial-style standardized residual of at least 4. This is a ranking heuristic, not a formal proof test.

## Highest Progressive Bulgaria Regional Shares

| Region | Name | Stations | Turnout | Progressive Bulgaria share |
|---|---|---:|---:|---:|
| 31 | 31. ЯМБОЛ | 237 | 47.668% | 54.954% |
| 17 | 17. ПЛОВДИВ област | 546 | 47.800% | 54.390% |
| 06 | 06. ВРАЦА | 328 | 52.121% | 53.586% |
| 04 | 04. ВЕЛИКО ТЪРНОВО | 419 | 48.973% | 52.784% |
| 21 | 21. СЛИВЕН | 298 | 39.342% | 51.994% |
| 15 | 15. ПЛЕВЕН | 397 | 46.830% | 51.843% |
| 13 | 13. ПАЗАРДЖИК | 367 | 45.591% | 51.132% |
| 08 | 08. ДОБРИЧ | 377 | 39.700% | 49.990% |

## Lowest Progressive Bulgaria Regional Shares

| Region | Name | Stations | Turnout | Progressive Bulgaria share |
|---|---|---:|---:|---:|
| 09 | 09. КЪРДЖАЛИ | 542 | 29.534% | 24.327% |
| 23 | 23. СОФИЯ 23 МИР | 636 | 59.470% | 32.565% |
| 24 | 24. СОФИЯ 24 МИР | 502 | 41.569% | 35.055% |
| 32 | 32. Извън страната | 493 | 89.572% | 38.038% |
| 18 | 18. РАЗГРАД | 215 | 36.409% | 38.610% |
| 01 | 01. БЛАГОЕВГРАД | 561 | 48.298% | 39.837% |
| 28 | 28. ТЪРГОВИЩЕ | 265 | 40.727% | 40.196% |
| 25 | 25. СОФИЯ 25 МИР | 516 | 52.286% | 41.976% |

## Highest Weighted Turnout/Share Correlations

| Region | Name | Stations | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|---:|
| 32 | 32. Извън страната | 493 | 0.259 | 38.038% |
| 20 | 20. СИЛИСТРА | 231 | 0.224 | 44.210% |
| 08 | 08. ДОБРИЧ | 377 | 0.220 | 49.990% |
| 30 | 30. ШУМЕН | 318 | 0.205 | 41.985% |
| 29 | 29. ХАСКОВО | 479 | 0.181 | 49.751% |
| 09 | 09. КЪРДЖАЛИ | 542 | 0.145 | 24.327% |
| 18 | 18. РАЗГРАД | 215 | 0.051 | 38.610% |
| 21 | 21. СЛИВЕН | 298 | 0.031 | 51.994% |

## Lowest Weighted Turnout/Share Correlations

| Region | Name | Stations | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|---:|
| 05 | 05. ВИДИН | 255 | -0.475 | 43.912% |
| 14 | 14. ПЕРНИК | 259 | -0.440 | 48.426% |
| 31 | 31. ЯМБОЛ | 237 | -0.384 | 54.954% |
| 06 | 06. ВРАЦА | 328 | -0.353 | 53.586% |
| 22 | 22. СМОЛЯН | 273 | -0.345 | 49.015% |
| 01 | 01. БЛАГОЕВГРАД | 561 | -0.332 | 39.837% |
| 07 | 07. ГАБРОВО | 234 | -0.307 | 47.837% |
| 13 | 13. ПАЗАРДЖИК | 367 | -0.303 | 51.132% |

## Regions With Most Regional Leads

| Region | Name | Attention score | Relative high-turnout/high-share | Positive residual leads | Validation issue stations |
|---|---|---:|---:|---:|---:|
| 32 | 32. Извън страната | 72 | 0 | 70 | 13 |
| 01 | 01. БЛАГОЕВГРАД | 60 | 5 | 54 | 1 |
| 09 | 09. КЪРДЖАЛИ | 56 | 10 | 45 | 9 |
| 30 | 30. ШУМЕН | 29 | 1 | 26 | 9 |
| 24 | 24. СОФИЯ 24 МИР | 25 | 1 | 23 | 4 |
| 23 | 23. СОФИЯ 23 МИР | 24 | 0 | 23 | 2 |
| 29 | 29. ХАСКОВО | 24 | 0 | 23 | 4 |
| 20 | 20. СИЛИСТРА | 19 | 2 | 16 | 0 |
| 02 | 02. БУРГАС | 19 | 0 | 18 | 1 |
| 28 | 28. ТЪРГОВИЩЕ | 18 | 2 | 15 | 4 |
| 18 | 18. РАЗГРАД | 17 | 2 | 15 | 0 |
| 17 | 17. ПЛОВДИВ област | 15 | 1 | 13 | 4 |

## Initial Interpretation

The regional checks still do not show a broad high-turnout/high-Progressive-Bulgaria pattern. Most regions with strong turnout/share relationships are negative, and only a few regions have weighted positive correlations above 0.20.

The next useful step is matched controls inside municipalities or neighboring settlements. The regional residual table gives a ranked list of stations to compare locally, but by itself it is not evidence of fraud because real local political geography can create large station-level residuals.
