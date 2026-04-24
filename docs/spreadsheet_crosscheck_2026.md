# 2026 Spreadsheet Cross-Check

## Inputs

Spreadsheet archive:

- `data/raw/cik_2026/spreadsheet.zip`
- Contains `ns01.xlsx` through `ns32.xlsx`.

Compared against processed text-table data in:

- `data/processed/cik_2026/sections.csv`
- `data/processed/cik_2026/protocols.csv`
- `data/processed/cik_2026/votes_long.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/crosscheck_spreadsheets.py
```

## Generated Local Files

- `outputs/tables/spreadsheet_crosscheck_summary_2026.json`
- `outputs/tables/spreadsheet_workbook_summaries_2026.csv`
- `outputs/tables/spreadsheet_vote_crosscheck_2026.csv`
- `outputs/tables/spreadsheet_vote_mismatches_2026.csv`
- `outputs/tables/spreadsheet_vote_name_mismatches_2026.csv`
- `outputs/tables/spreadsheet_national_party_totals_2026.csv`
- `outputs/tables/spreadsheet_section_mismatches_2026.csv`
- `outputs/tables/spreadsheet_protocol_field_totals_2026.csv`
- `outputs/tables/spreadsheet_protocol_mismatches_2026.csv`

## Findings

### Workbook Coverage

- Workbooks read: `32`
- Region workbooks covered: `01` through `32`
- Spreadsheet section rows: `12,721`
- Spreadsheet protocol sections: `12,721`
- Spreadsheet vote rows: `533,323`
  - Paper vote rows: `305,577`
  - Machine vote rows: `227,746`

### Section Cross-Check

- Text-table sections: `12,721`
- Spreadsheet sections: `12,721`
- Section ID mismatches: `0`
- Compared section fields also matched:
  - region ID;
  - mobile-section flag;
  - ship-section flag;
  - machine-voting flag.

### Party Vote Cross-Check

The spreadsheet vote sheets match `votes.txt` exactly by region, party/list number, and paper/machine split.

- Region-party/list rows compared: `769`
- Numeric vote mismatches: `0`
- Text-table valid votes: `3,240,156`
- Spreadsheet valid votes: `3,240,156`
- Difference: `0`
- Text-table paper votes: `1,697,603`
- Spreadsheet paper votes: `1,697,603`
- Difference: `0`
- Text-table machine votes: `1,542,553`
- Spreadsheet machine votes: `1,542,553`
- Difference: `0`

Progressive Bulgaria in the spreadsheet vote totals:

- Votes: `1,444,920`
- Share of valid candidate-list votes from vote tables: `44.5941%`

One non-numeric name difference was found:

| Region | Party/List No. | Text-table name | Spreadsheet name | Votes |
|---|---:|---|---|---:|
| 22 | 25 | ИК Тодор Тодоров Батков -Тодор Тодоров Батков | ИК Тодор Тодоров Батков | 2,093 |

The vote totals for that list match exactly: `1,260` paper votes and `833` machine votes.

### Protocol-Point Cross-Check

The spreadsheet protocol-point sheets match `protocols.txt` exactly for all compared fields.

| Field | Text total | Spreadsheet total | Difference |
|---|---:|---:|---:|
| received_paper_ballots | 5,348,499 | 5,348,499 | 0 |
| registered_voters_initial | 6,627,747 | 6,627,747 | 0 |
| voters_added_election_day | 267,045 | 267,045 | 0 |
| voters_signed | 3,360,330 | 3,360,330 | 0 |
| unused_paper_ballots | 3,541,104 | 3,541,104 | 0 |
| destroyed_paper_ballots | 19,233 | 19,233 | 0 |
| paper_ballots_found | 1,788,630 | 1,788,630 | 0 |
| invalid_paper_ballots | 69,222 | 69,222 | 0 |
| paper_none_votes | 21,809 | 21,809 | 0 |
| valid_paper_candidate_votes | 1,697,602 | 1,697,602 | 0 |
| machine_ballots_found | 1,571,588 | 1,571,588 | 0 |
| machine_none_votes | 28,924 | 28,924 | 0 |
| valid_machine_candidate_votes | 1,542,437 | 1,542,437 | 0 |

Section-level protocol field mismatches: `0`

## Important Caveat

This cross-check confirms that the official regional spreadsheets and official machine-readable text tables agree with each other.

It does not clear the protocol-level arithmetic/data-quality issues already detected. In particular:

- Party/list vote totals from `votes.txt` and the spreadsheets sum to `3,240,156`.
- Protocol valid candidate-list vote fields sum to `3,240,039`.
- Difference: `-117` protocol votes relative to the party/list vote tables.
- Paper candidate-list votes differ by `-1` at protocol-field total level: `1,697,602` protocol vs `1,697,603` party/list vote table.
- Machine candidate-list votes differ by `-116` at protocol-field total level: `1,542,437` protocol vs `1,542,553` party/list vote table.
- This difference is explained by the 8 station-level protocol-vs-party-vote mismatches already recorded in `outputs/tables/validation_issues.csv`.

The 8 station-level mismatches are:

| Section | Protocol total/paper/machine | Party/list table total/paper/machine |
|---|---:|---:|
| 010300070 | 265 / 132 / 133 | 266 / 132 / 134 |
| 030603289 | 184 / 55 / 129 | 185 / 55 / 130 |
| 143200007 | 260 / 134 / 126 | 261 / 134 / 127 |
| 192700162 | 334 / 117 / 217 | 231 / 118 / 113 |
| 244607062 | 434 / 149 / 285 | 425 / 149 / 276 |
| 261700005 | 358 / 164 / 194 | 418 / 164 / 254 |
| 261800008 | 206 / 206 / 0 | 380 / 206 / 174 |
| 264300005 | 370 / 168 / 202 | 362 / 168 / 194 |

So the spreadsheet export is consistent with the text export, but both still preserve the same underlying protocol-level anomalies.
