# Lead Clusters

## Inputs

- `outputs/tables/matched_control_results_2026.csv`
- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_lead_clusters.py
```

## Generated Outputs

- `outputs/tables/lead_cluster_municipality_2026.csv`
- `outputs/tables/lead_cluster_settlement_2026.csv`
- `outputs/tables/lead_cluster_abroad_2026.csv`
- `outputs/tables/lead_geo_clusters_2026.csv`
- `outputs/tables/lead_geo_cluster_members_2026.csv`
- `outputs/tables/lead_cluster_summary_2026.json`
- `outputs/figures/lead_clusters_by_municipality_2026.svg`

## Method

The primary lead definition is `matched_control_score >= 2` from the matched-control step. This script aggregates those stations by municipality code, settlement, abroad country/place, and a simple DBSCAN-style domestic coordinate cluster. The coordinate cluster uses a 5 km radius and requires at least 3 strong-lead stations.

These are follow-up leads, not fraud findings. A coherent cluster is more useful than an isolated station, but it still needs corroboration from protocol scans, complaints, local context, voting-method changes, or historical baselines.

## Summary

- Stations checked: `12,721`
- Strong matched-control leads: `230`
- Municipalities with at least one strong lead: `107`
- Settlements with at least one strong lead: `149`
- Abroad country/place groups with at least one strong lead: `27`
- Domestic strong leads with usable coordinates: `209`
- Coordinate clusters found: `10`
- Domestic strong leads inside coordinate clusters: `73`
- Domestic strong leads treated as coordinate noise/isolated: `136`

## Top Municipality Concentrations

| Municipality | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
| 23/46 | 636 | 21 | 3.3% | 1343.5 | 3 | 0 | 234623003; 234615002; 234623005; 234623024; 234615001; 234623007; 234616001; 234616009; 234615122; 234623010 |
| 24/46 | 502 | 16 | 3.2% | 1049.5 | 4 | 1 | 244614074; 244622001; 244606072; 244614058; 244622002; 244622012; 244605044; 244622013; 244614072; 244622023 |
| 09/14 | 80 | 9 | 11.2% | 616.7 | 5 | 0 | 091400012; 091400017; 091400034; 091400011; 091400016; 091400018; 091400001; 091400040; 091400002 |
| 09/16 | 170 | 9 | 5.3% | 482.2 | 4 | 0 | 091600037; 091600013; 091600043; 091600018; 091600017; 091600038; 091600026; 091600056; 091600160 |
| 25/46 | 516 | 9 | 1.7% | 460.2 | 3 | 0 | 254621023; 254620015; 254620038; 254619062; 254621001; 254621024; 254621011; 254621031; 254624019 |
| 16/22 | 482 | 7 | 1.5% | 340.1 | 3 | 0 | 162202059; 162203039; 162203044; 162202056; 162206056; 162202055; 162205099 |
| 03/06 | 412 | 4 | 1.0% | 273.3 | 3 | 0 | 030603193; 030600387; 030605377; 030605364 |
| 29/34 | 154 | 4 | 2.6% | 246.5 | 3 | 0 | 293400051; 293400008; 293400076; 293400052 |
| 01/33 | 90 | 3 | 3.3% | 206.9 | 4 | 0 | 013300056; 013300049; 013300047 |
| 09/15 | 86 | 3 | 3.5% | 203.0 | 3 | 0 | 091500003; 091500057; 091500004 |
| 08/27 | 33 | 3 | 9.1% | 197.6 | 3 | 0 | 082700003; 082700006; 082700002 |
| 02/04 | 343 | 3 | 0.9% | 195.7 | 2 | 0 | 020400326; 020400327; 020400144 |

## Top Settlement Concentrations

| Settlement | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
| 24/46 гр.София | 465 | 9 | 1.9% | 562.6 | 4 | 1 | 244614074; 244606072; 244614058; 244605044; 244614072; 244614060; 244614016; 244614027; 244605066 |
| 23/46 гр.София | 577 | 9 | 1.6% | 553.5 | 3 | 0 | 234615002; 234615001; 234616001; 234616009; 234615084; 234615078; 234615115; 234616015; 234608048 |
| 09/16 гр.Кърджали | 80 | 9 | 11.2% | 482.2 | 4 | 0 | 091600037; 091600013; 091600043; 091600018; 091600017; 091600038; 091600026; 091600056; 091600160 |
| 16/22 гр.Пловдив | 482 | 7 | 1.5% | 340.1 | 3 | 0 | 162202059; 162203039; 162203044; 162202056; 162206056; 162202055; 162205099 |
| 23/46 с.Казичене | 5 | 5 | 100.0% | 360.4 | 3 | 0 | 234623003; 234623005; 234623007; 234623006; 234623004 |
| 29/34 гр.Хасково | 116 | 4 | 3.4% | 246.5 | 3 | 0 | 293400051; 293400008; 293400076; 293400052 |
| 08/27 гр.Тервел | 8 | 3 | 37.5% | 197.6 | 3 | 0 | 082700003; 082700006; 082700002 |
| 24/46 гр. София,Кв. Ботунец | 6 | 3 | 50.0% | 195.8 | 2 | 0 | 244622012; 244622013; 244622011 |
| 03/06 гр.Варна | 402 | 3 | 0.7% | 183.9 | 3 | 0 | 030603193; 030605377; 030605364 |
| 25/46 гр.София | 441 | 3 | 0.7% | 169.1 | 3 | 0 | 254620015; 254620038; 254619062 |
| 30/30 гр.Шумен | 102 | 3 | 2.9% | 59.6 | 2 | 2 | 303000032; 303000063; 303000079 |
| 09/14 с.Чакаларово | 2 | 2 | 100.0% | 204.9 | 5 | 0 | 091400012; 091400011 |

## Abroad Country Concentrations

| Abroad country | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
| Германия | 70 | 6 | 8.6% | 485.5 | 3 | 1 | 320270068; 320270085; 320270080; 320270079; 320270061; 320270058 |
| Испания | 67 | 3 | 4.5% | 169.4 | 3 | 0 | 320480174; 320480213; 320480229 |
| Турция | 27 | 2 | 7.4% | 1001.0 | 2 | 0 | 321180443; 321180442 |
| Нидерландия | 24 | 2 | 8.3% | 364.4 | 3 | 0 | 320870307; 320870305 |
| Обединено кралство | 28 | 2 | 7.1% | 269.4 | 3 | 1 | 320920361; 320920347 |
| Италия | 27 | 2 | 7.4% | 82.8 | 2 | 0 | 320490260; 320490250 |
| Белгия | 17 | 1 | 5.9% | 150.6 | 2 | 0 | 320140045 |
| Австрия | 17 | 1 | 5.9% | 149.9 | 3 | 0 | 320020013 |
| Франция | 19 | 1 | 5.3% | 84.0 | 3 | 0 | 321250465 |

## Abroad Place Concentrations

| Abroad place | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
| Турция / Турция, Чорлу | 2 | 2 | 100.0% | 1001.0 | 2 | 0 | 321180443; 321180442 |
| Нидерландия / Нидерландия, Хага | 4 | 2 | 50.0% | 364.4 | 3 | 0 | 320870307; 320870305 |
| Обединено кралство / Обединено кралство, Мейдстоун | 1 | 1 | 100.0% | 205.1 | 3 | 1 | 320920361 |
| Германия / Германия, Лудвигсхафен | 1 | 1 | 100.0% | 168.6 | 2 | 0 | 320270085 |
| Белгия / Белгия, Гент | 2 | 1 | 50.0% | 150.6 | 2 | 0 | 320140045 |
| Австрия / Австрия, Виена | 8 | 1 | 12.5% | 149.9 | 3 | 0 | 320020013 |
| Франция / Франция, Сент-Етиен | 1 | 1 | 100.0% | 84.0 | 3 | 0 | 321250465 |
| Германия / Германия, Кобленц | 1 | 1 | 100.0% | 80.5 | 2 | 0 | 320270080 |
| Германия / Германия, Касел | 1 | 1 | 100.0% | 80.0 | 2 | 0 | 320270079 |
| Испания / Испания, Памплона | 2 | 1 | 50.0% | 73.9 | 2 | 0 | 320480213 |
| Обединено кралство / Обединено кралство, Арма | 1 | 1 | 100.0% | 64.3 | 2 | 0 | 320920347 |
| Италия / Италия, Чезена | 1 | 1 | 100.0% | 63.8 | 2 | 0 | 320490260 |

## Coordinate Clusters

| Cluster | Strong leads | Regions | Places | PB votes above matched expectation | Max score | Sections |
|---:|---:|---|---|---:|---:|---|
| 6 | 25 | 23; 24 | гр. София,Кв. Горубляне; гр.София; с.Казичене; с.Кокаляне; с.Кривина; с.Панчарево | 1587.8 | 4 | 244614074; 234623003; 234615002; 234623005; 234615001; 234623007; 234616001; 244614058; 234616009; 234615122; 244614072; 234623006; 234623001; 234615084; 234623004; 234615078; 234623021; 244614060; 234623019; 244614016 |
| 3 | 9 | 09 | гр.Кърджали | 482.2 | 4 | 091600037; 091600013; 091600043; 091600018; 091600017; 091600038; 091600026; 091600056; 091600160 |
| 7 | 8 | 24; 25 | гр. София,Кв. Враждебна; гр.София | 520.4 | 3 | 254620015; 254620038; 254619062; 244622001; 244606072; 244622002; 244605044; 244605066 |
| 4 | 7 | 16 | гр.Пловдив | 340.1 | 3 | 162202059; 162203039; 162203044; 162202056; 162206056; 162202055; 162205099 |
| 2 | 6 | 09 | с.Горно Кирково; с.Горно Къпиново; с.Долно Къпиново; с.Кирково; с.Чакаларово | 397.2 | 5 | 091400012; 091400017; 091400011; 091400016; 091400001; 091400002 |
| 8 | 5 | 24 | гр. София,Кв. Ботунец; гр.Бухово | 320.3 | 2 | 244622012; 244622013; 244622023; 244622022; 244622011 |
| 9 | 4 | 29 | гр.Хасково | 246.5 | 3 | 293400051; 293400008; 293400076; 293400052 |
| 5 | 3 | 17 | с.Чалъкови; с.Чешнегирово | 207.9 | 2 | 172500027; 172800004; 172500028 |
| 1 | 3 | 08 | гр.Тервел | 197.6 | 3 | 082700003; 082700006; 082700002 |
| 10 | 3 | 30 | гр.Шумен | 59.6 | 2 | 303000032; 303000063; 303000079 |

## Initial Interpretation

The local-cluster view separates broad concentration from isolated station outliers. Groups with several strong matched-control leads should be prioritized for manual protocol and complaint review, especially where multiple nearby stations share the same pattern. Groups with a single strong station remain useful leads, but are weaker statistical evidence unless corroborated by another independent signal.
