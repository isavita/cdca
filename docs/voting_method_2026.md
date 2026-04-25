# Voting Method Analysis

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_voting_method.py
```

## Generated Outputs

- `outputs/tables/voting_method_summary_2026.csv`
- `outputs/tables/voting_method_region_summary_2026.csv`
- `outputs/tables/voting_method_municipality_contrasts_2026.csv`
- `outputs/tables/voting_method_abroad_contrasts_2026.csv`
- `outputs/tables/voting_method_lead_stations_2026.csv`
- `outputs/tables/voting_method_summary_2026.json`
- `outputs/figures/voting_method_progressive_bulgaria_share_2026.svg`

## Summary

- Stations checked: `12,721`
- Mixed machine/paper stations: `9,484`
- Paper-only stations: `3,237`
- Municipalities with both voting modes: `253`
- Abroad countries/places with both voting modes: `20`
- Strong matched-control leads in mixed machine/paper stations: `198`
- Strong matched-control leads in paper-only stations: `32`

## National Method Summary

| Scope | Method | Stations | Turnout | PB share | Strong lead rate | Validation issue stations |
|---|---|---:|---:|---:|---:|---:|
| all | mixed_machine_paper | 9484 | 47.5% | 44.9% | 2.1% | 122 |
| all | paper_only | 3237 | 65.9% | 41.3% | 1.0% | 5 |
| domestic | mixed_machine_paper | 9354 | 46.7% | 45.3% | 2.0% | 111 |
| domestic | paper_only | 2874 | 59.2% | 40.8% | 0.8% | 3 |
| abroad | mixed_machine_paper | 130 | 87.8% | 34.4% | 7.7% | 11 |
| abroad | paper_only | 363 | 91.8% | 42.5% | 2.8% | 2 |

## Largest Municipal Paper-Only PB-Share Differences

These rows compare paper-only stations with mixed machine/paper stations inside the same region and municipality. They are leads for review, not proof of method manipulation.

| Region | Municipality | Mixed stations | Paper stations | Mixed PB share | Paper PB share | Paper-minus-mixed PB share | Paper lead rate minus mixed |
|---|---|---:|---:|---:|---:|---:|---:|
| 27 | 22 | 15 | 2 | 39.2% | 55.4% | 16.2% | -6.7% |
| 01 | 49 | 7 | 10 | 36.4% | 50.0% | 13.6% | 0.0% |
| 28 | 23 | 10 | 2 | 21.9% | 32.6% | 10.7% | 0.0% |
| 23 | 46 | 606 | 30 | 32.4% | 40.9% | 8.4% | 0.0% |
| 02 | 21 | 16 | 5 | 53.2% | 61.6% | 8.4% | -6.2% |
| 15 | 27 | 8 | 2 | 54.7% | 62.4% | 7.7% | -12.5% |
| 30 | 21 | 11 | 3 | 24.9% | 32.5% | 7.7% | -9.1% |
| 11 | 17 | 6 | 2 | 38.6% | 46.3% | 7.7% | 0.0% |
| 19 | 05 | 19 | 4 | 29.3% | 35.6% | 6.3% | -5.3% |
| 29 | 30 | 21 | 9 | 22.0% | 27.7% | 5.7% | 11.1% |
| 27 | 37 | 5 | 6 | 49.0% | 54.8% | 5.7% | -20.0% |
| 22 | 10 | 11 | 2 | 34.6% | 40.3% | 5.7% | -9.1% |

## Largest Municipal Paper-Only Lead-Rate Differences

| Region | Municipality | Mixed stations | Paper stations | Mixed lead rate | Paper lead rate | Difference | Paper PB share |
|---|---|---:|---:|---:|---:|---:|---:|
| 18 | 29 | 14 | 4 | 0.0% | 25.0% | 25.0% | 63.4% |
| 04 | 26 | 17 | 6 | 0.0% | 16.7% | 16.7% | 61.4% |
| 01 | 52 | 13 | 6 | 0.0% | 16.7% | 16.7% | 39.2% |
| 01 | 42 | 20 | 6 | 0.0% | 16.7% | 16.7% | 30.9% |
| 29 | 30 | 21 | 9 | 0.0% | 11.1% | 11.1% | 27.7% |
| 12 | 12 | 8 | 9 | 0.0% | 11.1% | 11.1% | 45.2% |
| 22 | 11 | 15 | 6 | 6.7% | 16.7% | 10.0% | 60.5% |
| 29 | 18 | 4 | 11 | 0.0% | 9.1% | 9.1% | 16.4% |
| 29 | 28 | 30 | 13 | 0.0% | 7.7% | 7.7% | 38.6% |
| 17 | 12 | 13 | 7 | 7.7% | 14.3% | 6.6% | 51.6% |
| 28 | 24 | 33 | 18 | 0.0% | 5.6% | 5.6% | 60.2% |
| 09 | 35 | 21 | 20 | 0.0% | 5.0% | 5.0% | 11.3% |

## Abroad Method Contrasts

| Country/place | Mixed stations | Paper stations | Mixed PB share | Paper PB share | Paper-minus-mixed PB share | Paper lead rate minus mixed |
|---|---:|---:|---:|---:|---:|---:|
| Германия | 1 | 1 | 44.7% | 60.7% | 16.1% | 0.0% |
| Турция | 4 | 2 | 13.7% | 29.4% | 15.7% | 0.0% |
| Швейцария | 1 | 1 | 22.6% | 37.1% | 14.5% | 0.0% |
| Чехия | 1 | 2 | 26.8% | 39.0% | 12.2% | 0.0% |
| Италия | 2 | 1 | 33.1% | 42.7% | 9.6% | 0.0% |
| Белгия | 1 | 2 | 44.2% | 53.6% | 9.4% | 0.0% |
| Германия | 1 | 2 | 35.2% | 44.2% | 9.0% | 0.0% |
| Германия | 3 | 2 | 32.5% | 41.1% | 8.6% | 0.0% |
| Канада | 1 | 4 | 25.1% | 31.9% | 6.8% | 0.0% |
| Белгия | 3 | 3 | 27.3% | 31.1% | 3.8% | 0.0% |
| Германия | 1 | 1 | 49.3% | 53.0% | 3.6% | 0.0% |
| Испания | 1 | 4 | 34.8% | 37.9% | 3.1% | 0.0% |

## Initial Interpretation

Voting method is confounded by station size and geography: paper-only stations are usually smaller or abroad-specific, so raw national differences should not be read as causal. The more useful rows are local contrasts where both methods exist in the same municipality or abroad country/place. Any paper-only locality with large Progressive Bulgaria differences should be checked against station size, local political geography, protocol scans, and whether the paper-only status was expected or caused by a machine issue.
