# 2026 Validation Pass

## Inputs

Processed from:

- `data/interim/cik_2026/tables/sections_19.04.2026.txt`
- `data/interim/cik_2026/tables/protocols_19.04.2026.txt`
- `data/interim/cik_2026/tables/votes_19.04.2026.txt`
- `data/interim/cik_2026/tables/cik_parties_19.04.2026.txt`
- `data/interim/cik_2026/tables/local_parties_19.04.2026.txt`

Commands:

```sh
python3 src/preprocess.py
python3 src/validate_totals.py
```

## Generated Local Files

Processed CSVs:

- `data/processed/cik_2026/parties.csv`
- `data/processed/cik_2026/sections.csv`
- `data/processed/cik_2026/protocols.csv`
- `data/processed/cik_2026/votes_long.csv`
- `data/processed/cik_2026/polling_stations_2026.csv`

Validation outputs:

- `outputs/tables/party_totals_2026.csv`
- `outputs/tables/region_party_totals_2026.csv`
- `outputs/tables/validation_issues.csv`
- `outputs/tables/validation_summary_2026.json`

## Structural Checks

- Sections: `12,721`
- Protocols: `12,721`
- Polling-station result rows: `12,721`
- Long party-vote rows: `305,577`
- Duplicate section IDs in sections: `0`
- Duplicate section IDs in protocols: `0`
- Sections, protocols, and votes cover the same section-ID set.
- Every party-vote row satisfies `valid_votes = paper_votes + machine_votes`.

## National Totals From Official Text Tables

- Registered voters: `6,894,792`
- Voters signed as voted: `3,360,330`
- Ballots found: `3,360,218`
- Valid votes for candidate lists from protocol fields: `3,240,039`
- Valid votes for candidate lists from party/list vote tables: `3,240,156`
- Protocol minus party/list vote-table difference: `-117`
- Progressive Bulgaria votes: `1,444,920`
- Progressive Bulgaria share of party/list vote-table valid votes: `44.594%`
- Progressive Bulgaria share using protocol valid-vote denominator: `44.596%`
- Signed-voter turnout: `48.737%`

Top parties by valid candidate-list votes:

| Party ID | Party | Votes | Share |
|---:|---|---:|---:|
| 21 | PROGRESSIVE BULGARIA | 1,444,920 | 44.59% |
| 15 | GERB-SDS | 433,755 | 13.39% |
| 7 | PP-DB | 408,846 | 12.62% |
| 17 | DPS | 230,693 | 7.12% |
| 8 | Vazrazhdane | 137,940 | 4.26% |

Note: the project stores original Bulgarian party names in the generated CSV outputs.

## Protocol-Level Issues Detected

These are arithmetic/data-quality leads, not fraud conclusions:

- Station vote-sum mismatches: `8`
- Protocol paper arithmetic mismatches: `1`
- Protocol machine arithmetic mismatches: `33`
- Signed-voters vs ballots-found mismatches: `98`
- Turnout greater than registered voters: `0`
- Total validation issue rows: `140`

For party-share analysis, `polling_stations_2026.csv` uses the summed party-vote table as the candidate-vote denominator and keeps the protocol candidate-vote total as `total_valid_candidate_votes_protocol` for audit comparison.

## Remaining Validation Work

- Cross-check national and regional totals against the regional `ns01.xlsx` through `ns32.xlsx` spreadsheets. Completed in `docs/spreadsheet_crosscheck_2026.md`.
- Cross-check headline national totals against CIK web result pages if accessible without manual browser interaction.
- Review the 140 protocol-level issues to classify them as clerical, explainable, or unresolved.
