# Anomaly Scoring and Protocol Review Sample

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`
- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/lead_geo_cluster_members_2026.csv`
- `outputs/tables/voting_method_lead_stations_2026.csv`
- `outputs/tables/historical_station_swing_2024_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/score_anomalies.py
```

## Generated Outputs

- `outputs/tables/anomaly_scores_2026.csv`
- `outputs/tables/suspicious_stations_2026.csv`
- `outputs/tables/protocol_review_sample_2026.csv`
- `outputs/tables/anomaly_score_summary_2026.json`
- `outputs/figures/anomaly_score_distribution_2026.svg`

## Summary

- Stations scored: `12,721`
- Category 0, normal/no flag: `11,792`
- Category 1, mild statistical outlier: `716`
- Category 2, strong statistical lead: `179`
- Category 3, statistical lead with corroborating flag: `34`
- Category 4, priority manual review: `0`
- Historical swing lead stations: `550`
- Protocol review sample size: `150`

## Top Scored Stations

| Section | Region | Place | Method | Category | Score | PB share | PB votes above matched expectation | Evidence summary |
|---|---|---|---|---:|---:|---:|---:|---|
| 091400017 | 09 | с.Горно Къпиново | paper_only | 3 | 10 | 78.3% | 50.9 | matched-control score 5; +50.9 PB votes vs matched expectation; high turnout and high PB share vs controls; regional score 5; geo cluster 2; paper-only method lead; large 2026 swing vs exact 2024 section |
| 091400012 | 09 | с.Чакаларово | mixed_machine_paper | 3 | 8 | 73.7% | 135.1 | matched-control score 5; +135.1 PB votes vs matched expectation; high turnout and high PB share vs controls; regional score 3; geo cluster 2 |
| 234615002 | 23 | гр.София | mixed_machine_paper | 3 | 7 | 54.5% | 100.4 | matched-control score 3; +100.4 PB votes vs matched expectation; regional score 2; geo cluster 6; large 2026 swing vs exact 2024 section |
| 244614074 | 24 | гр.София | mixed_machine_paper | 3 | 7 | 49.9% | 66.4 | matched-control score 4; +66.4 PB votes vs matched expectation; regional score 2; geo cluster 6; validation issue: signed_voters_ballots_found_mismatch |
| 320920361 | 32 | Обединено кралство, Мейдстоун | mixed_machine_paper | 3 | 6 | 59.0% | 205.1 | matched-control score 3; +205.1 PB votes vs matched expectation; regional score 2; validation issue: protocol_machine_arithmetic_mismatch |
| 234623003 | 23 | с.Казичене | mixed_machine_paper | 3 | 6 | 56.5% | 101.4 | matched-control score 3; +101.4 PB votes vs matched expectation; regional score 2; geo cluster 6 |
| 091400011 | 09 | с.Чакаларово | mixed_machine_paper | 3 | 6 | 69.6% | 69.8 | matched-control score 3; +69.8 PB votes vs matched expectation; high turnout and high PB share vs controls; regional score 2; geo cluster 2 |
| 091600037 | 09 | гр.Кърджали | mixed_machine_paper | 3 | 6 | 52.9% | 65.1 | matched-control score 4; +65.1 PB votes vs matched expectation; regional score 2; geo cluster 3 |
| 091400016 | 09 | с.Долно Къпиново | paper_only | 3 | 6 | 77.6% | 54.7 | matched-control score 3; +54.7 PB votes vs matched expectation; regional score 3; geo cluster 2; paper-only method lead |
| 244605066 | 24 | гр.София | paper_only | 3 | 6 | 60.2% | 30.1 | matched-control score 2; regional score 2; geo cluster 7; paper-only method lead; large 2026 swing vs exact 2024 section |
| 244622001 | 24 | гр. София,Кв. Враждебна | mixed_machine_paper | 3 | 5 | 57.2% | 89.4 | matched-control score 2; +89.4 PB votes vs matched expectation; geo cluster 7; large 2026 swing vs exact 2024 section |
| 234623005 | 23 | с.Казичене | mixed_machine_paper | 3 | 5 | 53.5% | 84.0 | matched-control score 3; +84.0 PB votes vs matched expectation; regional score 2; geo cluster 6 |
| 172500027 | 17 | с.Чалъкови | mixed_machine_paper | 3 | 5 | 76.4% | 76.2 | matched-control score 2; +76.2 PB votes vs matched expectation; geo cluster 5; large 2026 swing vs exact 2024 section |
| 082700002 | 08 | гр.Тервел | mixed_machine_paper | 3 | 5 | 61.6% | 73.6 | matched-control score 2; +73.6 PB votes vs matched expectation; high turnout and high PB share vs controls; geo cluster 1 |
| 172800004 | 17 | с.Чешнегирово | mixed_machine_paper | 3 | 5 | 73.2% | 71.7 | matched-control score 2; +71.7 PB votes vs matched expectation; geo cluster 5; large 2026 swing vs exact 2024 section |
| 244622023 | 24 | гр.Бухово | mixed_machine_paper | 3 | 5 | 59.3% | 64.5 | matched-control score 2; +64.5 PB votes vs matched expectation; geo cluster 8; large 2026 swing vs exact 2024 section |
| 082700003 | 08 | гр.Тервел | mixed_machine_paper | 3 | 5 | 61.7% | 63.8 | matched-control score 3; +63.8 PB votes vs matched expectation; high turnout and high PB share vs controls; geo cluster 1 |
| 234615084 | 23 | гр.София | mixed_machine_paper | 3 | 5 | 47.0% | 61.1 | matched-control score 2; +61.1 PB votes vs matched expectation; geo cluster 6; large 2026 swing vs exact 2024 section |
| 091400001 | 09 | с.Кирково | mixed_machine_paper | 3 | 5 | 54.8% | 60.2 | matched-control score 2; +60.2 PB votes vs matched expectation; regional score 2; geo cluster 2 |
| 082700006 | 08 | гр.Тервел | mixed_machine_paper | 3 | 5 | 59.5% | 60.2 | matched-control score 3; +60.2 PB votes vs matched expectation; high turnout and high PB share vs controls; geo cluster 1 |

## Review Sample Method

The protocol review sample prioritizes stations with high anomaly categories, validation issues, coordinate-cluster membership, large matched-control residuals, and strong matched-control scores. The generated sample includes CIK search links plus candidate protocol HTML/PDF URLs for manual verification. The candidate protocol URLs should be treated as navigational aids because the CIK site may change routing or require browser interaction.

## Interpretation

The score is an auditable triage score, not a fraud label. The strongest statistical leads are places where multiple independent statistical indicators agree, especially when they are clustered or have protocol/validation flags. The score should now be used to guide manual protocol checks, complaint matching, and historical baseline review.
