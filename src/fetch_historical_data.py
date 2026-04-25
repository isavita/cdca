#!/usr/bin/env python3
"""Attempt to fetch official historical CIK open-data archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HISTORICAL_ARCHIVES = [
    {
        "label": "October 2024 parliamentary election",
        "candidates": [
            "https://results.cik.bg/pe202410/opendata/export.zip",
            "https://results.cik.bg/pi202410/opendata/export.zip",
        ],
    },
    {
        "label": "June 2024 parliamentary election",
        "candidates": [
            "https://results.cik.bg/europe2024/opendata/export.zip",
            "https://results.cik.bg/ns202406/opendata/export.zip",
            "https://results.cik.bg/pi202406/opendata/export.zip",
        ],
    },
    {
        "label": "April 2023 parliamentary election",
        "candidates": [
            "https://results.cik.bg/ns2023/opendata/export.zip",
            "https://results.cik.bg/ns202304/opendata/export.zip",
        ],
    },
    {
        "label": "October 2022 parliamentary election",
        "candidates": [
            "https://results.cik.bg/ns2022/opendata/export.zip",
            "https://results.cik.bg/ns202210/opendata/export.zip",
        ],
    },
    {
        "label": "November 2021 parliamentary election",
        "candidates": [
            "https://results.cik.bg/pi202111/opendata/export.zip",
            "https://results.cik.bg/ns202111/opendata/export.zip",
        ],
    },
    {
        "label": "July 2021 parliamentary election",
        "candidates": [
            "https://results.cik.bg/pi202107/opendata/export.zip",
            "https://results.cik.bg/ns202107/opendata/export.zip",
        ],
    },
    {
        "label": "April 2021 parliamentary election",
        "candidates": [
            "https://results.cik.bg/pi202104/opendata/export.zip",
            "https://results.cik.bg/ns202104/opendata/export.zip",
        ],
    },
]


def sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def fetch_url(url: str, timeout: int) -> tuple[dict[str, Any], bytes | None]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; cdca-election-audit/1.0)",
            "Accept": "application/zip,application/octet-stream,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
            return (
                {
                    "url": url,
                    "status": int(response.status),
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(data),
                    "sha256": sha256_bytes(data),
                    "error": "",
                },
                data,
            )
    except urllib.error.HTTPError as exc:
        return (
            {
                "url": url,
                "status": int(exc.code),
                "content_type": exc.headers.get("Content-Type") if exc.headers else None,
                "content_length": 0,
                "sha256": "",
                "error": f"HTTPError: {exc.reason}",
            },
            None,
        )
    except Exception as exc:  # noqa: BLE001 - manifest should capture acquisition failures.
        return (
            {
                "url": url,
                "status": None,
                "content_type": None,
                "content_length": 0,
                "sha256": "",
                "error": f"{type(exc).__name__}: {exc}",
            },
            None,
        )


def safe_name(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(",", "")
        .replace("election", "")
        .strip("_")
    )


def fetch_historical(output_dir: Path, timeout: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "archives": [],
    }
    for archive in HISTORICAL_ARCHIVES:
        result: dict[str, Any] = {
            "label": archive["label"],
            "downloaded": False,
            "selected_url": "",
            "path": "",
            "attempts": [],
        }
        for url in archive["candidates"]:
            attempt, data = fetch_url(url, timeout=timeout)
            result["attempts"].append(attempt)
            if data and attempt["status"] == 200 and data[:2] == b"PK":
                path = output_dir / f"{safe_name(archive['label'])}.zip"
                path.write_bytes(data)
                result["downloaded"] = True
                result["selected_url"] = url
                result["path"] = str(path)
                break
        manifest["archives"].append(result)
    (output_dir / "historical_fetch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def write_note(docs_dir: Path, manifest: dict[str, Any]) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    downloaded = [row for row in manifest["archives"] if row["downloaded"]]
    blocked = [row for row in manifest["archives"] if not row["downloaded"]]
    note = f"""# Historical Data Acquisition Attempt

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/fetch_historical_data.py
```

## Summary

- Historical elections requested: `{len(manifest["archives"])}`
- Archives downloaded: `{len(downloaded)}`
- Archives not downloaded: `{len(blocked)}`
- Manifest: `data/raw/cik_historical/historical_fetch_manifest.json`

## Result

The automated fetch attempted official `results.cik.bg` open-data archive URLs for prior parliamentary elections. The October 2024 archive downloaded successfully and is used as the nearest-prior historical baseline. Older archive URLs attempted here either timed out or returned 404 in this environment, so the historical swing analysis is limited to October 2024 versus April 2026 exact section matches.

This is a data-access limitation, not a finding about the election. The current report and website therefore scope historical conclusions to the verified October 2024 archive and the verified 2026 official station data.

## Attempted Elections

| Election | Downloaded | Attempted URLs/statuses |
|---|---:|---|
"""
    for row in manifest["archives"]:
        attempts = "; ".join(f"{attempt['url']} ({attempt['status'] or attempt['error']})" for attempt in row["attempts"])
        note += f"| {row['label']} | {'yes' if row['downloaded'] else 'no'} | {attempts} |\n"
    (docs_dir / "historical_data_attempt_2026.md").write_text(note, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/cik_historical"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument("--timeout", type=int, default=20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = fetch_historical(args.output_dir.resolve(), timeout=args.timeout)
    write_note(args.docs_dir.resolve(), manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
