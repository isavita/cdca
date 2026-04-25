# Historical Baseline: October 2024 to April 2026

## Inputs

- `data/raw/cik_historical/october_2024_parliamentary.zip`
- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/build_historical_baseline.py
```

## Generated Outputs

- `data/processed/historical_baselines.csv`
- `outputs/tables/historical_station_swing_2024_2026.csv`
- `outputs/tables/historical_swing_leads_2024_2026.csv`
- `outputs/tables/historical_region_swing_2024_2026.csv`
- `outputs/tables/historical_summary_2024_2026.json`
- `outputs/figures/historical_region_pb_minus_2024_top_2026.svg`

## Method

This is a conservative nearest-prior baseline using exact polling-section ID matches between the official 27 October 2024 archive and the 19 April 2026 data. It does not assume that Progressive Bulgaria has a single direct predecessor. It reports comparisons to:

- the strongest 2024 party in the same station;
- 2024 PP-DB;
- 2024 PP-DB plus GERB-SDS as a broad non-identical reference pool.

## Summary

- 2024 stations parsed: `12,920`
- 2026 stations: `12,721`
- Exact section matches: `12,353`
- Historical swing lead stations: `550`
- Weighted turnout-delta / PB-minus-2024-top-share correlation: `0.438`

## Top Regions by PB 2026 Minus 2024 Top-Party Share

| Region | Name | Matched sections | Turnout delta | PB 2026 | 2024 top-party weighted share | PB minus 2024 top-party share | Swing leads |
|---|---|---:|---:|---:|---:|---:|---:|
| 31 | 31. ЯМБОЛ | 236 | 14.9% | 55.0% | 29.3% | 25.6% | 24 |
| 17 | 17. ПЛОВДИВ област | 540 | 16.2% | 54.4% | 33.3% | 21.1% | 124 |
| 15 | 15. ПЛЕВЕН | 392 | 11.6% | 51.8% | 31.2% | 20.7% | 16 |
| 04 | 04. ВЕЛИКО ТЪРНОВО | 417 | 13.9% | 52.8% | 32.5% | 20.3% | 29 |
| 19 | 19. РУСЕ | 335 | 11.9% | 49.3% | 30.3% | 19.0% | 9 |
| 21 | 21. СЛИВЕН | 298 | 10.8% | 52.0% | 36.5% | 15.5% | 25 |
| 16 | 16. ПЛОВДИВ град | 472 | 13.8% | 46.3% | 31.3% | 15.0% | 39 |
| 27 | 27. СТАРА ЗАГОРА | 493 | 11.8% | 49.4% | 35.4% | 14.0% | 13 |
| 10 | 10. КЮСТЕНДИЛ | 285 | 11.3% | 48.3% | 34.6% | 13.7% | 5 |
| 32 | 32. Извън страната | 197 | -3.8% | 44.7% | 31.5% | 13.2% | 3 |
| 08 | 08. ДОБРИЧ | 376 | 8.0% | 50.0% | 36.9% | 13.1% | 6 |
| 07 | 07. ГАБРОВО | 234 | 14.1% | 47.8% | 34.8% | 13.1% | 10 |

## Top Station Swing Leads

Definition: at least 50 valid votes in 2026, turnout at least 20 percentage points above 2024, and Progressive Bulgaria share at least 20 percentage points above the strongest 2024 party share in the same station.

| Section | Region | Place | Turnout 2024 | Turnout 2026 | PB 2026 | 2024 top party | 2024 top share | PB minus 2024 top share |
|---|---|---|---:|---:|---:|---|---:|---:|
| 293300039 | 29 | с.Славяново | 28.0% | 52.3% | 87.4% | ГЕРБ-СДС | 21.9% | 65.4% |
| 172500028 | 17 | с.Чалъкови | 6.7% | 39.8% | 81.1% | БСП – ОБЕДИНЕНА ЛЕВИЦА | 26.2% | 54.9% |
| 173300007 | 17 | гр.Съединение | 13.2% | 33.8% | 78.7% | БСП – ОБЕДИНЕНА ЛЕВИЦА | 23.8% | 54.9% |
| 041400001 | 04 | гр.Златарица | 26.8% | 47.1% | 78.3% | ДПС-Ново начало | 23.5% | 54.8% |
| 014000061 | 01 | с.Яново | 41.2% | 66.0% | 76.7% | ГЕРБ-СДС | 22.0% | 54.7% |
| 152300009 | 15 | с.Староселци | 30.6% | 51.4% | 80.2% | БСП – ОБЕДИНЕНА ЛЕВИЦА | 26.7% | 53.6% |
| 020900022 | 02 | гр.Карнобат | 16.0% | 37.7% | 72.8% | ДПС-Ново начало | 21.4% | 51.4% |
| 171700016 | 17 | с.Граф Игнатиево | 35.3% | 61.5% | 72.7% | ГЕРБ-СДС | 22.3% | 50.4% |
| 174300012 | 17 | с.Анево | 25.4% | 53.5% | 69.2% | ВЪЗРАЖДАНЕ | 19.5% | 49.7% |
| 171700020 | 17 | с.Калековец | 16.0% | 42.6% | 72.5% | ДПС-Ново начало | 23.1% | 49.4% |
| 021500027 | 02 | с.Оризаре | 29.0% | 50.8% | 72.7% | ДПС-Ново начало | 23.5% | 49.2% |
| 021500019 | 02 | с.Гюльовца | 36.0% | 57.7% | 74.3% | ВЪЗРАЖДАНЕ | 25.7% | 48.6% |

## Interpretation

The historical pass is useful for prioritization, but it should not be treated as a direct fraud test. Exact section IDs can still hide boundary changes, and a new national political alignment can legitimately produce large station-level swings. The strongest historical leads are most useful when they overlap with matched-control leads, spatial clusters, validation issues, or protocol-review priorities.
