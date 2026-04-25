# Party Pattern Comparison

## Inputs

- `data/processed/cik_2026/votes_long.csv`
- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_party_patterns.py
```

## Generated Outputs

- `outputs/tables/party_national_summary_2026.csv`
- `outputs/tables/party_turnout_bins_2026.csv`
- `outputs/tables/station_party_leaders_2026.csv`
- `outputs/tables/party_pattern_summary_2026.json`
- `outputs/figures/party_turnout_correlation_2026.svg`

## Progressive Bulgaria Context

- National vote share: `44.59%`
- Vote rank: `1`
- Weighted turnout/share correlation: `-0.125`
- Correlation rank among parties, descending: `24`
- High-turnout/high-share stations under the same 80% turnout and 70% party-share rule: `10`

## Top Parties by Votes

| Rank | Party | Votes | Share | Weighted turnout/share r | High-turnout/high-share stations |
|---:|---|---:|---:|---:|---:|
| 1 | ПРОГРЕСИВНА БЪЛГАРИЯ | 1,444,920 | 44.6% | -0.125 | 10 |
| 2 | ГЕРБ-СДС | 433,755 | 13.4% | -0.011 | 8 |
| 3 | КОАЛИЦИЯ ПРОДЪЛЖАВАМЕ ПРОМЯНАТА – ДЕМОКРАТИЧНА БЪЛГАРИЯ | 408,846 | 12.6% | 0.360 | 2 |
| 4 | Движение за права и свободи - ДПС | 230,693 | 7.1% | -0.200 | 53 |
| 5 | ВЪЗРАЖДАНЕ | 137,940 | 4.3% | 0.193 | 0 |
| 6 | ПП МЕЧ | 104,506 | 3.2% | -0.010 | 0 |
| 7 | ПП ВЕЛИЧИЕ | 100,572 | 3.1% | 0.228 | 0 |
| 8 | БСП – ОБЕДИНЕНА ЛЕВИЦА | 97,753 | 3.0% | -0.014 | 1 |
| 9 | СИЯНИЕ | 93,559 | 2.9% | 0.124 | 0 |
| 10 | АЛИАНС ЗА ПРАВА И СВОБОДИ – АПС | 50,759 | 1.6% | -0.090 | 0 |
| 11 | ПП ИМА ТАКЪВ НАРОД | 23,861 | 0.7% | 0.036 | 0 |
| 12 | АНТИКОРУПЦИОНЕН БЛОК | 18,999 | 0.6% | 0.141 | 0 |
| 13 | СИНЯ БЪЛГАРИЯ | 18,640 | 0.6% | 0.110 | 0 |
| 14 | БЪЛГАРИЯ МОЖЕ | 17,263 | 0.5% | 0.139 | 0 |

## Highest Positive Turnout/Share Correlations

| Party | Share | Weighted r | Domestic weighted r | Abroad weighted r |
|---|---:|---:|---:|---:|
| КОАЛИЦИЯ ПРОДЪЛЖАВАМЕ ПРОМЯНАТА – ДЕМОКРАТИЧНА БЪЛГАРИЯ | 12.6% | 0.360 | 0.288 | 0.244 |
| ПП ВЕЛИЧИЕ | 3.1% | 0.228 | 0.018 | 0.293 |
| ВЪЗРАЖДАНЕ | 4.3% | 0.193 | 0.162 | 0.232 |
| АНТИКОРУПЦИОНЕН БЛОК | 0.6% | 0.141 | 0.166 | 0.199 |
| БЪЛГАРИЯ МОЖЕ | 0.5% | 0.139 | 0.153 | 0.191 |
| СИЯНИЕ | 2.9% | 0.124 | 0.247 | 0.358 |
| ПРЯКА ДЕМОКРАЦИЯ | 0.3% | 0.120 | 0.075 | 0.153 |
| СИНЯ БЪЛГАРИЯ | 0.6% | 0.110 | 0.184 | 0.168 |
| Партия на ЗЕЛЕНИТЕ | 0.1% | 0.085 | 0.059 | 0.070 |
| ПП НАЦИЯ | 0.3% | 0.077 | 0.030 | 0.163 |

## Most Negative Turnout/Share Correlations

| Party | Share | Weighted r | Domestic weighted r | Abroad weighted r |
|---|---:|---:|---:|---:|
| Движение за права и свободи - ДПС | 7.1% | -0.200 | -0.266 | -0.408 |
| ПРОГРЕСИВНА БЪЛГАРИЯ | 44.6% | -0.125 | -0.081 | 0.259 |
| АЛИАНС ЗА ПРАВА И СВОБОДИ – АПС | 1.6% | -0.090 | -0.175 | -0.490 |
| ИК Тодор Тодоров Батков -Тодор Тодоров Батков | 0.1% | -0.067 | -0.067 |  |
| КП ТРЕТИ МАРТ | 0.1% | -0.059 | -0.050 | -0.109 |
| МОЯ БЪЛГАРИЯ | 0.1% | -0.030 | -0.051 | -0.055 |
| НД НЕПОКОРНА БЪЛГАРИЯ | 0.2% | -0.023 | 0.014 | -0.074 |
| Съпротива | 0.1% | -0.021 | -0.059 | -0.103 |
| БСП – ОБЕДИНЕНА ЛЕВИЦА | 3.0% | -0.014 | 0.128 | 0.149 |
| ГЕРБ-СДС | 13.4% | -0.011 | 0.211 | 0.265 |

## Initial Interpretation

Progressive Bulgaria's national result is unusual politically, but the turnout/share statistic is not a simple pro-winner stuffing pattern: its station-level weighted turnout/share correlation is negative overall. Other parties have stronger positive correlations with turnout. That does not clear every local anomaly, but it weakens the hypothesis of a broad nationwide mechanism where turnout and Progressive Bulgaria share rise together.
