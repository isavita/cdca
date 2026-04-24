#!/usr/bin/env python3
"""Extract canonical CIK text tables from an official open-data archive."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


EXPECTED_TABLE_SUFFIXES = (
    "cik_parties_19.04.2026.txt",
    "local_candidates_19.04.2026.txt",
    "local_parties_19.04.2026.txt",
    "preferences_19.04.2026.txt",
    "protocols_19.04.2026.txt",
    "readme_19.04.2026.txt",
    "sections_19.04.2026.txt",
    "votes_19.04.2026.txt",
)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_tables(archive: Path, output_dir: Path, force: bool) -> int:
    if not archive.exists():
        print(f"Archive not found: {archive}", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    table_dir = output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[dict[str, Any]] = []
    found_suffixes: set[str] = set()

    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        machine_zip_count = sum(
            1
            for info in infos
            if info.filename.startswith("suemg/")
            and info.filename.endswith(".zip")
            and info.filename != "suemg/ca.zip"
        )
        machine_region_dirs = sorted(
            {
                parts[1]
                for info in infos
                if info.filename.startswith("suemg/")
                for parts in [info.filename.split("/")]
                if len(parts) >= 3 and parts[1].isdigit()
            }
        )

        for suffix in EXPECTED_TABLE_SUFFIXES:
            matches = [info for info in infos if info.filename.endswith(suffix)]
            if len(matches) != 1:
                print(f"Expected exactly one archive entry ending in {suffix}, found {len(matches)}", file=sys.stderr)
                continue

            info = matches[0]
            destination = table_dir / suffix
            if destination.exists() and not force:
                extracted.append(
                    {
                        "archive_entry": info.filename,
                        "path": str(destination),
                        "bytes": destination.stat().st_size,
                        "sha256": sha256_file(destination),
                        "extracted": False,
                        "reason": "already exists; pass --force to overwrite",
                    }
                )
                found_suffixes.add(suffix)
                continue

            with zf.open(info) as source, destination.open("wb") as target:
                target.write(source.read())

            extracted.append(
                {
                    "archive_entry": info.filename,
                    "path": str(destination),
                    "bytes": destination.stat().st_size,
                    "sha256": sha256_file(destination),
                    "extracted": True,
                }
            )
            found_suffixes.add(suffix)

    missing = sorted(set(EXPECTED_TABLE_SUFFIXES) - found_suffixes)
    manifest = {
        "archive": str(archive),
        "archive_sha256": sha256_file(archive),
        "extracted_at_utc": utc_now(),
        "output_dir": str(output_dir),
        "table_dir": str(table_dir),
        "expected_table_count": len(EXPECTED_TABLE_SUFFIXES),
        "extracted_table_count": len(extracted),
        "missing_tables": missing,
        "machine_zip_count": machine_zip_count,
        "machine_region_dirs": machine_region_dirs,
        "tables": extracted,
    }
    write_json(output_dir / "extract_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if missing else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path("data/raw/cik_2026/export.zip"),
        help="Path to the official CIK export.zip archive.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/interim/cik_2026"),
        help="Directory for extracted table files and manifest.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing extracted tables.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return extract_tables(args.archive.resolve(), args.output_dir.resolve(), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
