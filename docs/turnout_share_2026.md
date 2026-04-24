# Turnout vs Progressive Bulgaria Share

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_turnout_share.py
```

## Generated Outputs

Figures:

- `outputs/figures/turnout_vs_progressive_bulgaria_share_2026.svg`
- `outputs/figures/turnout_vs_progressive_bulgaria_share_domestic_2026.svg`
- `outputs/figures/turnout_vs_progressive_bulgaria_share_abroad_2026.svg`
- `outputs/figures/progressive_bulgaria_share_by_turnout_bin_2026.svg`

Tables:

- `outputs/tables/turnout_share_group_summary_2026.csv`
- `outputs/tables/turnout_share_region_summary_2026.csv`
- `outputs/tables/turnout_bins_2026.csv`
- `outputs/tables/high_turnout_high_progressive_bulgaria_2026.csv`
- `outputs/tables/extreme_turnout_stations_2026.csv`
- `outputs/tables/turnout_share_summary_2026.json`

## National Pattern

- Stations analyzed: `12,721`
- Registered voters: `6,894,792`
- Signed turnout: `48.737%`
- Progressive Bulgaria votes: `1,444,920`
- Progressive Bulgaria share of party/list valid votes: `44.594%`
- Unweighted Pearson correlation between station turnout and Progressive Bulgaria share: `-0.098`
- Unweighted Spearman correlation: `-0.152`
- Valid-vote-weighted correlation: `-0.125`

## Domestic vs Abroad

| Group | Stations | Turnout | Progressive Bulgaria Share | Pearson r | Weighted r |
|---|---:|---:|---:|---:|---:|
| Domestic | `12,228` | `47.397%` | `44.995%` | `-0.092` | `-0.081` |
| Abroad | `493` | `89.572%` | `38.038%` | `0.188` | `0.259` |

## Voting Method Split

| Group | Stations | Turnout | Progressive Bulgaria Share | Pearson r | Weighted r |
|---|---:|---:|---:|---:|---:|
| Mixed machine/paper | `9,484` | `47.486%` | `44.927%` | `0.009` | `-0.123` |
| Paper only | `3,237` | `65.872%` | `41.273%` | `0.013` | `0.006` |

## Turnout Bins

| Turnout bin | Stations | Progressive Bulgaria share |
|---|---:|---:|
| 0-20% | 285 | 42.149% |
| 20-30% | 678 | 36.155% |
| 30-40% | 1,183 | 42.580% |
| 40-50% | 2,677 | 49.530% |
| 50-60% | 4,740 | 46.112% |
| 60-70% | 1,489 | 39.323% |
| 70-80% | 527 | 34.136% |
| 80-90% | 282 | 29.252% |
| 90-100% | 860 | 40.431% |

## High-Turnout / High-Share Leads

Threshold used for this first pass:

- turnout >= `80%`
- Progressive Bulgaria share >= `70%`
- valid candidate-list votes >= `50`

Stations meeting threshold: `10`

Scope split:

| Scope | Stations | Valid candidate-list votes | Progressive Bulgaria votes |
|---|---:|---:|---:|
| abroad | 5 | 1,055 | 856 |
| domestic | 5 | 547 | 433 |

These rows are leads for later contextual review, not fraud findings. They are written to `outputs/tables/high_turnout_high_progressive_bulgaria_2026.csv`.

Extreme-turnout stations using turnout >= `95%` or <= `5%`: `672`. These are written to `outputs/tables/extreme_turnout_stations_2026.csv`.

Extreme-turnout scope split:

| Turnout bucket | Scope | Stations |
|---|---|---:|
| <=5% | domestic | 19 |
| >=95% | abroad | 264 |
| >=95% | domestic | 389 |

## Regional Correlations

Highest valid-vote-weighted turnout/share correlations:

| Region | Name | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|
| 32 | 32. Извън страната | 0.259 | 38.038% |
| 20 | 20. СИЛИСТРА | 0.224 | 44.210% |
| 08 | 08. ДОБРИЧ | 0.220 | 49.990% |
| 30 | 30. ШУМЕН | 0.205 | 41.985% |
| 29 | 29. ХАСКОВО | 0.181 | 49.751% |
| 09 | 09. КЪРДЖАЛИ | 0.145 | 24.327% |
| 18 | 18. РАЗГРАД | 0.051 | 38.610% |
| 21 | 21. СЛИВЕН | 0.031 | 51.994% |

Lowest valid-vote-weighted turnout/share correlations:

| Region | Name | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|
| 05 | 05. ВИДИН | -0.475 | 43.912% |
| 14 | 14. ПЕРНИК | -0.440 | 48.426% |
| 31 | 31. ЯМБОЛ | -0.384 | 54.954% |
| 06 | 06. ВРАЦА | -0.353 | 53.586% |
| 22 | 22. СМОЛЯН | -0.345 | 49.015% |
| 01 | 01. БЛАГОЕВГРАД | -0.332 | 39.837% |
| 07 | 07. ГАБРОВО | -0.307 | 47.837% |
| 13 | 13. ПАЗАРДЖИК | -0.303 | 51.132% |

## Initial Interpretation

This first pass does not by itself prove anything about fraud. It establishes the turnout/share surface that later tests should control for by region, voting method, and historical baseline.

The national pattern is not a simple high-turnout/high-Progressive-Bulgaria pattern: the national Pearson correlation is negative, the valid-vote-weighted correlation is negative, and the 80-90% turnout bin has a lower Progressive Bulgaria share than the national average. The abroad stations behave differently and need separate treatment because their registered-voter denominators and turnout mechanics are not directly comparable with domestic sections.
