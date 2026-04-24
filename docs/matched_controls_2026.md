# Matched Controls

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_matched_controls.py
```

## Generated Outputs

- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/matched_control_leads_2026.csv`
- `outputs/tables/matched_control_strong_leads_2026.csv`
- `outputs/tables/matched_control_group_summary_2026.csv`
- `outputs/tables/matched_control_summary_2026.json`

## Method

Each station is compared to up to `30` nearest peers by registered-voter size from the most local available group with at least `5` controls.

Domestic priority:

1. same region, same municipality code, same voting mode;
2. same region and municipality code;
3. same region and voting mode;
4. same region.

Abroad priority:

1. same country and voting mode;
2. same country;
3. same abroad voting mode;
4. all abroad stations.

## Summary

- Stations checked: `12,721`
- Stations with controls: `12,634`
- Stations without sufficient controls: `87`
- Matched positive residual leads: `245`
- Matched relative high-turnout/high-share leads: `22`
- Strong matched leads with score >= 2: `230`

Score distribution:

| Score | Stations |
|---:|---:|
| 0 | 11,016 |
| 1 | 1,475 |
| 2 | 175 |
| 3 | 46 |
| 4 | 5 |
| 5 | 4 |

## Control Group Coverage

| Control group | Stations | Positive residual leads | Relative high-turnout/high-share leads | Score >= 2 |
|---|---:|---:|---:|---:|
| domestic_same_municipality_voting_mode | 11,843 | 209 | 20 | 207 |
| abroad_same_country_voting_mode | 406 | 31 | 0 | 20 |
| domestic_same_municipality | 371 | 5 | 2 | 3 |
| no_sufficient_controls | 87 | 0 | 0 | 0 |
| domestic_same_region_voting_mode | 14 | 0 | 0 | 0 |

## Top Strong Matched Leads

| Section | Region | Place | Control group | PB share | Control PB share | PB votes above control expectation | Score |
|---|---|---|---|---:|---:|---:|---:|
| 091400012 | 09 | с.Чакаларово | domestic_same_municipality_voting_mode | 73.7% | 33.7% | 135.1 | 5 |
| 090200028 | 09 | с.Падина | domestic_same_municipality_voting_mode | 46.7% | 21.2% | 85.1 | 5 |
| 170100090 | 17 | с.Боянци | domestic_same_municipality_voting_mode | 77.0% | 48.5% | 54.4 | 5 |
| 091400017 | 09 | с.Горно Къпиново | domestic_same_municipality_voting_mode | 78.3% | 34.0% | 50.9 | 5 |
| 013300056 | 01 | с.Михнево | domestic_same_municipality_voting_mode | 66.9% | 46.9% | 105.4 | 4 |
| 244614074 | 24 | гр.София | domestic_same_municipality_voting_mode | 49.9% | 32.2% | 66.4 | 4 |
| 091600037 | 09 | гр.Кърджали | domestic_same_municipality_voting_mode | 52.9% | 21.0% | 65.1 | 4 |
| 062700034 | 06 | с.Оселна | domestic_same_municipality_voting_mode | 87.1% | 59.7% | 57.6 | 4 |
| 182900017 | 18 | с.Самуил | domestic_same_municipality | 95.1% | 73.0% | 17.9 | 4 |
| 320870307 | 32 | Нидерландия, Хага | abroad_same_country_voting_mode | 67.2% | 32.9% | 314.4 | 3 |
| 320920361 | 32 | Обединено кралство, Мейдстоун | abroad_same_country_voting_mode | 59.0% | 45.9% | 205.1 | 3 |
| 291900002 | 29 | с.Минерални бани | domestic_same_municipality_voting_mode | 68.5% | 15.1% | 166.2 | 3 |
| 320020013 | 32 | Австрия, Виена | abroad_same_country_voting_mode | 53.8% | 27.9% | 149.9 | 3 |
| 090800030 | 09 | с.Припек | domestic_same_municipality_voting_mode | 36.9% | 5.1% | 129.1 | 3 |
| 234623003 | 23 | с.Казичене | domestic_same_municipality_voting_mode | 56.5% | 32.0% | 101.4 | 3 |
| 234615002 | 23 | гр.София | domestic_same_municipality_voting_mode | 54.5% | 30.7% | 100.4 | 3 |
| 181400013 | 18 | гр.Исперих | domestic_same_municipality_voting_mode | 47.6% | 24.4% | 99.1 | 3 |
| 011100001 | 01 | гр.Гоце Делчев | domestic_same_municipality_voting_mode | 48.5% | 31.4% | 94.8 | 3 |
| 091500003 | 09 | гр.Крумовград | domestic_same_municipality_voting_mode | 56.4% | 25.1% | 90.5 | 3 |
| 174000006 | 17 | гр.Перущица | domestic_same_municipality_voting_mode | 90.8% | 58.1% | 89.0 | 3 |

## Largest Positive Matched Residuals

| Section | Region | Place | Control group | PB share | Control PB share | PB votes above control expectation | Score |
|---|---|---|---|---:|---:|---:|---:|
| 321180443 | 32 | Турция, Чорлу | abroad_same_country_voting_mode | 54.9% | 14.4% | 678.2 | 2 |
| 321180442 | 32 | Турция, Чорлу | abroad_same_country_voting_mode | 37.8% | 15.7% | 322.8 | 2 |
| 320870307 | 32 | Нидерландия, Хага | abroad_same_country_voting_mode | 67.2% | 32.9% | 314.4 | 3 |
| 320920361 | 32 | Обединено кралство, Мейдстоун | abroad_same_country_voting_mode | 59.0% | 45.9% | 205.1 | 3 |
| 320920354 | 32 | Обединено кралство, Лондон | abroad_same_country_voting_mode | 56.2% | 46.0% | 186.2 | 1 |
| 320270085 | 32 | Германия, Лудвигсхафен | abroad_same_country_voting_mode | 67.6% | 41.2% | 168.6 | 2 |
| 291900002 | 29 | с.Минерални бани | domestic_same_municipality_voting_mode | 68.5% | 15.1% | 166.2 | 3 |
| 320920351 | 32 | Обединено кралство, Лондон | abroad_same_country_voting_mode | 56.5% | 46.1% | 163.2 | 1 |
| 320140045 | 32 | Белгия, Гент | abroad_same_country_voting_mode | 64.1% | 43.4% | 150.6 | 2 |
| 320020013 | 32 | Австрия, Виена | abroad_same_country_voting_mode | 53.8% | 27.9% | 149.9 | 3 |
| 321180429 | 32 | Турция, Ескишехир | abroad_same_country_voting_mode | 37.2% | 16.4% | 149.4 | 1 |
| 091400012 | 09 | с.Чакаларово | domestic_same_municipality_voting_mode | 73.7% | 33.7% | 135.1 | 5 |
| 321180444 | 32 | Турция, Ялова | abroad_same_country_voting_mode | 29.6% | 16.4% | 131.2 | 1 |
| 090800030 | 09 | с.Припек | domestic_same_municipality_voting_mode | 36.9% | 5.1% | 129.1 | 3 |
| 273700002 | 27 | гр.Гурково | domestic_same_municipality | 70.6% | 44.1% | 108.8 | 2 |
| 013300056 | 01 | с.Михнево | domestic_same_municipality_voting_mode | 66.9% | 46.9% | 105.4 | 4 |
| 291900001 | 29 | с.Минерални бани | domestic_same_municipality_voting_mode | 53.4% | 17.1% | 105.3 | 1 |
| 320270104 | 32 | Германия, Регенсбург | abroad_same_country_voting_mode | 54.7% | 41.7% | 103.8 | 1 |
| 320270087 | 32 | Германия, Майнц | abroad_same_country_voting_mode | 53.3% | 41.7% | 103.3 | 1 |
| 234623003 | 23 | с.Казичене | domestic_same_municipality_voting_mode | 56.5% | 32.0% | 101.4 | 3 |

## Initial Interpretation

Matched controls are stricter than regional residuals because they compare stations against local peers. Stations that remain high after this step are better candidates for manual review, especially when they also appear in the regional lead table or have protocol/administrative issues.

These matched-control leads are still not fraud findings. The next step is to examine whether the leads cluster by municipality/settlement and whether they overlap with voting method changes, complaints, RIK decisions, or scanned protocol issues.
