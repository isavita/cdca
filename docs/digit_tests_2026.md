# Digit Diagnostics

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `data/processed/cik_2026/votes_long.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_digit_tests.py
```

## Generated Outputs

- `outputs/tables/digit_test_summary_2026.csv`
- `outputs/tables/digit_test_digit_counts_2026.csv`
- `outputs/tables/digit_test_summary_2026.json`
- `outputs/figures/digit_test_progressive_bulgaria_last_digit_2026.svg`

## Summary

- Series tested: `14`
- Tests run: `28`
- Tests with p-value below 0.01: `23`

## Progressive Bulgaria Tests

| Series | Test | Sample | Chi-square | p-value | Max digit-share deviation |
|---|---|---:|---:|---:|---:|
| progressive_bulgaria_station_votes | first_digit_benford | 12,699 | 4023.38 | 0 | 24.36% |
| progressive_bulgaria_station_votes | last_digit_uniform | 12,699 | 6.48 | 0.6914 | 0.35% |

## Lowest P-Value Diagnostics

| Series | Test | Sample | Chi-square | p-value | Max digit-share deviation |
|---|---|---:|---:|---:|---:|
| party_11_АЛИАНС ЗА ПРАВА И СВОБОДИ – АПС | last_digit_uniform | 7,343 | 13425.04 | 0 | 37.75% |
| station_voters_signed | first_digit_benford | 12,721 | 5212.91 | 0 | 14.96% |
| station_total_valid_votes | first_digit_benford | 12,721 | 5034.23 | 0 | 14.15% |
| station_registered_voters | first_digit_benford | 12,721 | 8569.12 | 0 | 19.73% |
| progressive_bulgaria_station_votes | first_digit_benford | 12,699 | 4023.38 | 0 | 24.36% |
| party_8_ВЪЗРАЖДАНЕ | first_digit_benford | 12,110 | 1931.41 | 0 | 15.45% |
| party_8_ВЪЗРАЖДАНЕ | last_digit_uniform | 12,110 | 1193.19 | 0 | 7.61% |
| party_7_КОАЛИЦИЯ ПРОДЪЛЖАВАМЕ ПРОМЯНАТА – ДЕМОКРАТИЧНА Б | first_digit_benford | 12,340 | 127.42 | 0 | 2.01% |
| party_7_КОАЛИЦИЯ ПРОДЪЛЖАВАМЕ ПРОМЯНАТА – ДЕМОКРАТИЧНА Б | last_digit_uniform | 12,340 | 714.94 | 0 | 4.73% |
| party_5_БСП – ОБЕДИНЕНА ЛЕВИЦА | first_digit_benford | 12,136 | 814.88 | 0 | 9.58% |
| party_4_ПП МЕЧ | first_digit_benford | 11,610 | 1544.75 | 0 | 14.59% |
| party_5_БСП – ОБЕДИНЕНА ЛЕВИЦА | last_digit_uniform | 12,136 | 1271.98 | 0 | 7.25% |

## Interpretation

Digit tests are low-priority diagnostics here. Zero counts are excluded from the last-digit tests. Polling-station vote counts are constrained by station size, party geography, turnout, and local political support, so Benford or last-digit deviations are not fraud evidence on their own. These results are only useful if they line up with stronger evidence such as protocol mismatches, administrative complaints, coherent local clusters, or unexplained historical swings.
