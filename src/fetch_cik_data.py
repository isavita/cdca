#!/usr/bin/env python3
"""Download official CIK election open-data archives with checksums."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
)

DEFAULT_ELECTIONS: dict[str, dict[str, str]] = {
    "pe202604": {
        "label": "Bulgaria parliamentary election, 19 April 2026",
        "output_dir": "data/raw/cik_2026",
        "opendata_page": "https://results.cik.bg/pe202604/opendata/index.html",
        "export_url": "https://results.cik.bg/pe202604/opendata/export.zip",
        "spreadsheet_url": "https://results.cik.bg/pe202604/opendata/spreadsheet.zip",
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "*/*",
        },
    )


def download(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()

    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent, delete=False
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        with urllib.request.urlopen(build_request(url), timeout=120) as response:
            with tmp_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            headers = dict(response.headers.items())
            status = response.status

        tmp_path.replace(destination)
        return {
            "url": url,
            "path": str(destination),
            "started_at_utc": started_at,
            "finished_at_utc": utc_now(),
            "status": status,
            "headers": headers,
            "bytes": destination.stat().st_size,
            "sha256": sha256_file(destination),
        }
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_election(election_id: str, root: Path, force: bool) -> int:
    if election_id not in DEFAULT_ELECTIONS:
        known = ", ".join(sorted(DEFAULT_ELECTIONS))
        print(f"Unknown election {election_id!r}. Known elections: {known}", file=sys.stderr)
        return 2

    config = DEFAULT_ELECTIONS[election_id]
    output_dir = root / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "download_manifest.json"
    source_path = output_dir / "source.json"
    archives = [
        ("export.zip", config["export_url"]),
        ("spreadsheet.zip", config["spreadsheet_url"]),
    ]

    write_json(
        source_path,
        {
            "election_id": election_id,
            "label": config["label"],
            "opendata_page": config["opendata_page"],
            "archives": [{"filename": filename, "url": url} for filename, url in archives],
            "noted_at_utc": utc_now(),
        },
    )

    archive_results: list[dict[str, Any]] = []
    failures = 0

    for filename, url in archives:
        archive_path = output_dir / filename
        if archive_path.exists() and not force:
            archive_results.append(
                {
                    "downloaded": False,
                    "reason": "archive already exists; pass --force to re-download",
                    "url": url,
                    "path": str(archive_path),
                    "bytes": archive_path.stat().st_size,
                    "sha256": sha256_file(archive_path),
                    "checked_at_utc": utc_now(),
                }
            )
            continue

        try:
            result = download(url, archive_path)
        except urllib.error.HTTPError as exc:
            print(f"HTTP error downloading {url}: {exc}", file=sys.stderr)
            archive_results.append({"downloaded": False, "url": url, "path": str(archive_path), "error": str(exc)})
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"Network error downloading {url}: {exc}", file=sys.stderr)
            archive_results.append({"downloaded": False, "url": url, "path": str(archive_path), "error": str(exc)})
            failures += 1
            continue

        result["downloaded"] = True
        archive_results.append(result)

    manifest = {
        "election_id": election_id,
        "label": config["label"],
        "opendata_page": config["opendata_page"],
        "archives": archive_results,
    }
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--election",
        default="pe202604",
        help="CIK election identifier to fetch. Default: pe202604.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Default: current working directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the archive already exists.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return fetch_election(args.election, args.root.resolve(), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
