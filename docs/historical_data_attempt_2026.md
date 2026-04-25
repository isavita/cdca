# Historical Data Acquisition Attempt

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/fetch_historical_data.py
```

## Summary

- Historical elections requested: `7`
- Archives downloaded: `1`
- Archives not downloaded: `6`
- Manifest: `data/raw/cik_historical/historical_fetch_manifest.json`

## Result

The automated fetch attempted official `results.cik.bg` open-data archive URLs for prior parliamentary elections. The October 2024 archive downloaded successfully and is used as the nearest-prior historical baseline. Older archive URLs attempted here either timed out or returned 404 in this environment, so the historical swing analysis is limited to October 2024 versus April 2026 exact section matches.

This is a data-access limitation, not a finding about the election. The current report and website therefore scope historical conclusions to the verified October 2024 archive and the verified 2026 official station data.

## Attempted Elections

| Election | Downloaded | Attempted URLs/statuses |
|---|---:|---|
| October 2024 parliamentary election | yes | https://results.cik.bg/pe202410/opendata/export.zip (200) |
| June 2024 parliamentary election | no | https://results.cik.bg/europe2024/opendata/export.zip (TimeoutError: The read operation timed out); https://results.cik.bg/ns202406/opendata/export.zip (404); https://results.cik.bg/pi202406/opendata/export.zip (404) |
| April 2023 parliamentary election | no | https://results.cik.bg/ns2023/opendata/export.zip (404); https://results.cik.bg/ns202304/opendata/export.zip (404) |
| October 2022 parliamentary election | no | https://results.cik.bg/ns2022/opendata/export.zip (404); https://results.cik.bg/ns202210/opendata/export.zip (404) |
| November 2021 parliamentary election | no | https://results.cik.bg/pi202111/opendata/export.zip (404); https://results.cik.bg/ns202111/opendata/export.zip (404) |
| July 2021 parliamentary election | no | https://results.cik.bg/pi202107/opendata/export.zip (404); https://results.cik.bg/ns202107/opendata/export.zip (404) |
| April 2021 parliamentary election | no | https://results.cik.bg/pi202104/opendata/export.zip (404); https://results.cik.bg/ns202104/opendata/export.zip (404) |
