# Data Acquisition Notes

## 2026 CIK Open Data

Official source:

- `https://results.cik.bg/pe202604/opendata/index.html`
- Direct archives used by the fetch script:
  - `https://results.cik.bg/pe202604/opendata/export.zip`
  - `https://results.cik.bg/pe202604/opendata/spreadsheet.zip`

Local raw archive:

- `data/raw/cik_2026/export.zip`
- SHA-256: `40da58a58d220b0080cacc7fe8f391dd1726262630fb807c558b5a8a4b3a7f4a`
- Size: `26,762,696` bytes
- Server `Last-Modified`: `Thu, 23 Apr 2026 11:13:39 GMT`

Local spreadsheet archive:

- `data/raw/cik_2026/spreadsheet.zip`
- SHA-256: `f7d356e3b9dce0093abb343ba8f6839372af291b7ec7fcf3394e21fd3c4f7884`
- Size: `31,778,168` bytes
- Server `Last-Modified`: `Thu, 23 Apr 2026 11:16:13 GMT`
- Contains `ns01.xlsx` through `ns32.xlsx`.

Local metadata:

- `data/raw/cik_2026/source.json`
- `data/raw/cik_2026/download_manifest.json`

Extracted staging tables:

- `data/interim/cik_2026/tables/cik_parties_19.04.2026.txt`
- `data/interim/cik_2026/tables/local_candidates_19.04.2026.txt`
- `data/interim/cik_2026/tables/local_parties_19.04.2026.txt`
- `data/interim/cik_2026/tables/preferences_19.04.2026.txt`
- `data/interim/cik_2026/tables/protocols_19.04.2026.txt`
- `data/interim/cik_2026/tables/readme_19.04.2026.txt`
- `data/interim/cik_2026/tables/sections_19.04.2026.txt`
- `data/interim/cik_2026/tables/votes_19.04.2026.txt`

Archive contents observed so far:

- 8 canonical text tables.
- 32 regional spreadsheet files.
- 12,721 rows in each of `sections`, `protocols`, and `votes`.
- 24 parties/coalitions in `cik_parties`.
- 9,402 machine-voting ZIP files under `suemg/`.
- Machine-voting files cover region directories `01` through `32`.

Notes:

- Direct shell access to the CIK open-data HTML page returned a Cloudflare challenge, but the direct official archive URLs downloaded successfully.
- The archive contains a Cyrillic directory name encoded in a way that appears mangled in ZIP listings. The extraction script identifies the canonical table files by their ASCII filename suffixes and writes stable local filenames.
- The downloaded archive is the canonical raw source. Extracted tables under `data/interim/` are convenience copies for validation and parsing.

## Commands

```sh
python3 src/fetch_cik_data.py --election pe202604
python3 src/extract_cik_tables.py
```
