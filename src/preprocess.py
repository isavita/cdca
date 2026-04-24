#!/usr/bin/env python3
"""Normalize CIK open-data text tables into analysis-ready CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROGRESSIVE_BULGARIA_PARTY_ID = 21

PROTOCOL_COLUMNS = [
    "form_no",
    "section_id",
    "admin_id",
    "serial_numbers",
    "blank_5",
    "blank_6",
    "received_paper_ballots",
    "registered_voters_initial",
    "voters_added_election_day",
    "voters_signed",
    "unused_paper_ballots",
    "destroyed_paper_ballots",
    "paper_ballots_found",
    "invalid_paper_ballots",
    "paper_none_votes",
    "valid_paper_candidate_votes",
    "machine_ballots_found",
    "machine_none_votes",
    "valid_machine_candidate_votes",
]


def read_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.reader(handle, delimiter=";")]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: str | int | None, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    value = value.strip()
    if value == "":
        return default
    return int(value)


def to_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return float(value)


def ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def parse_parties(tables_dir: Path) -> tuple[list[dict[str, Any]], dict[int, str], dict[tuple[int, int], str]]:
    cik_parties = []
    national_names: dict[int, str] = {}
    for row in read_rows(tables_dir / "cik_parties_19.04.2026.txt"):
        party_id = to_int(row[0])
        party_name = row[1]
        cik_parties.append({"party_id": party_id, "party_name": party_name, "scope": "national", "admin_id": ""})
        national_names[party_id] = party_name

    local_names: dict[tuple[int, int], str] = {}
    for row in read_rows(tables_dir / "local_parties_19.04.2026.txt"):
        admin_id = to_int(row[0])
        party_id = to_int(row[2])
        party_name = row[3]
        local_names[(admin_id, party_id)] = party_name

    return cik_parties, national_names, local_names


def party_name_for(admin_id: int, party_id: int, national_names: dict[int, str], local_names: dict[tuple[int, int], str]) -> str:
    return local_names.get((admin_id, party_id), national_names.get(party_id, ""))


def parse_sections(tables_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for row in read_rows(tables_dir / "sections_19.04.2026.txt"):
        if len(row) < 11:
            raise ValueError(f"Section row has too few fields: {row}")
        section_id = row[0]
        region_id = section_id[:2]
        # A few address fields contain an extra semicolon before coordinates.
        # The first five and last five fields are stable, so rebuild address from the middle.
        address = ";".join(row[5:-5]).rstrip(";")
        longitude, latitude, is_mobile, is_ship, machines_count = row[-5:]
        rows.append(
            {
                "section_id": section_id,
                "region_id": region_id,
                "municipality_code": section_id[2:4],
                "admin_area_code": section_id[4:6],
                "precinct_code": section_id[6:9],
                "is_abroad": int(region_id == "32"),
                "admin_id": to_int(row[1]),
                "admin_name": row[2],
                "ekatte": row[3],
                "place_name": row[4],
                "address": address,
                "longitude": to_float(longitude),
                "latitude": to_float(latitude),
                "is_mobile": to_int(is_mobile),
                "is_ship": to_int(is_ship),
                "machines_count": to_int(machines_count),
            }
        )
    return rows


def parse_protocols(tables_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for raw in read_rows(tables_dir / "protocols_19.04.2026.txt"):
        padded = raw + [""] * (len(PROTOCOL_COLUMNS) - len(raw))
        record = dict(zip(PROTOCOL_COLUMNS, padded, strict=False))
        numeric_columns = [column for column in PROTOCOL_COLUMNS if column not in {"section_id", "serial_numbers", "blank_5", "blank_6"}]
        for column in numeric_columns:
            record[column] = to_int(record[column])

        valid_paper = record["valid_paper_candidate_votes"]
        valid_machine = record["valid_machine_candidate_votes"]
        paper_none = record["paper_none_votes"]
        machine_none = record["machine_none_votes"]
        paper_found = record["paper_ballots_found"]
        machine_found = record["machine_ballots_found"]
        registered = record["registered_voters_initial"] + record["voters_added_election_day"]

        record.update(
            {
                "registered_voters": registered,
                "has_machine_protocol": int(record["form_no"] in {26, 30}),
                "is_abroad_form": int(record["form_no"] in {28, 30}),
                "total_none_votes": paper_none + machine_none,
                "total_valid_candidate_votes": valid_paper + valid_machine,
                "total_ballots_found": paper_found + machine_found,
                "turnout": ratio(record["voters_signed"], registered),
                "valid_candidate_vote_rate": ratio(valid_paper + valid_machine, paper_found + machine_found),
            }
        )
        rows.append(record)
    return rows


def parse_votes(
    tables_dir: Path,
    national_names: dict[int, str],
    local_names: dict[tuple[int, int], str],
) -> list[dict[str, Any]]:
    rows = []
    for raw in read_rows(tables_dir / "votes_19.04.2026.txt"):
        form_no = to_int(raw[0])
        section_id = raw[1]
        admin_id = to_int(raw[2])
        vote_fields = raw[3:]
        if len(vote_fields) % 4 != 0:
            raise ValueError(f"Vote row for section {section_id} has incomplete party groups")

        for index in range(0, len(vote_fields), 4):
            party_id = to_int(vote_fields[index])
            valid_votes = to_int(vote_fields[index + 1])
            paper_votes = to_int(vote_fields[index + 2])
            machine_votes = to_int(vote_fields[index + 3])
            rows.append(
                {
                    "form_no": form_no,
                    "section_id": section_id,
                    "admin_id": admin_id,
                    "party_id": party_id,
                    "party_name": party_name_for(admin_id, party_id, national_names, local_names),
                    "valid_votes": valid_votes,
                    "paper_votes": paper_votes,
                    "machine_votes": machine_votes,
                }
            )
    return rows


def build_station_results(
    sections: list[dict[str, Any]],
    protocols: list[dict[str, Any]],
    votes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    protocols_by_section = {row["section_id"]: row for row in protocols}
    vote_sums_by_section: dict[str, dict[str, int]] = {}
    progressive_by_section: dict[str, int] = {}

    for vote in votes:
        section_id = vote["section_id"]
        sums = vote_sums_by_section.setdefault(section_id, {"valid_votes": 0, "paper_votes": 0, "machine_votes": 0})
        sums["valid_votes"] += vote["valid_votes"]
        sums["paper_votes"] += vote["paper_votes"]
        sums["machine_votes"] += vote["machine_votes"]
        if vote["party_id"] == PROGRESSIVE_BULGARIA_PARTY_ID:
            progressive_by_section[section_id] = vote["valid_votes"]

    station_rows = []
    for section in sections:
        section_id = section["section_id"]
        protocol = protocols_by_section.get(section_id, {})
        vote_sums = vote_sums_by_section.get(section_id, {"valid_votes": 0, "paper_votes": 0, "machine_votes": 0})
        progressive_votes = progressive_by_section.get(section_id, 0)
        protocol_valid_candidate_votes = to_int(protocol.get("total_valid_candidate_votes"))
        vote_table_valid_candidate_votes = vote_sums["valid_votes"]
        total_ballots_found = to_int(protocol.get("total_ballots_found"))
        voting_mode = "mixed_machine_paper" if to_int(protocol.get("has_machine_protocol")) else "paper_only"

        station_rows.append(
            {
                **section,
                "form_no": protocol.get("form_no", ""),
                "voting_mode": voting_mode,
                "registered_voters": protocol.get("registered_voters", ""),
                "registered_voters_initial": protocol.get("registered_voters_initial", ""),
                "voters_added_election_day": protocol.get("voters_added_election_day", ""),
                "voters_signed": protocol.get("voters_signed", ""),
                "total_ballots_found": total_ballots_found,
                "invalid_paper_ballots": protocol.get("invalid_paper_ballots", ""),
                "total_none_votes": protocol.get("total_none_votes", ""),
                "total_valid_candidate_votes": vote_table_valid_candidate_votes,
                "total_valid_candidate_votes_protocol": protocol_valid_candidate_votes,
                "valid_votes_from_votes_table": vote_sums["valid_votes"],
                "valid_vote_protocol_minus_votes_table": protocol_valid_candidate_votes - vote_table_valid_candidate_votes,
                "paper_votes_from_votes_table": vote_sums["paper_votes"],
                "machine_votes_from_votes_table": vote_sums["machine_votes"],
                "turnout": protocol.get("turnout", ""),
                "valid_candidate_vote_rate": protocol.get("valid_candidate_vote_rate", ""),
                "progressive_bulgaria_votes": progressive_votes,
                "progressive_bulgaria_share": ratio(progressive_votes, vote_table_valid_candidate_votes),
                "progressive_bulgaria_share_of_ballots_found": ratio(progressive_votes, total_ballots_found),
            }
        )
    return station_rows


def preprocess(tables_dir: Path, output_dir: Path) -> None:
    parties, national_names, local_names = parse_parties(tables_dir)
    sections = parse_sections(tables_dir)
    protocols = parse_protocols(tables_dir)
    votes = parse_votes(tables_dir, national_names, local_names)
    station_results = build_station_results(sections, protocols, votes)

    write_csv(output_dir / "parties.csv", parties, ["party_id", "party_name", "scope", "admin_id"])
    write_csv(
        output_dir / "sections.csv",
        sections,
        [
            "section_id",
            "region_id",
            "municipality_code",
            "admin_area_code",
            "precinct_code",
            "is_abroad",
            "admin_id",
            "admin_name",
            "ekatte",
            "place_name",
            "address",
            "longitude",
            "latitude",
            "is_mobile",
            "is_ship",
            "machines_count",
        ],
    )
    write_csv(
        output_dir / "protocols.csv",
        protocols,
        [
            *PROTOCOL_COLUMNS,
            "registered_voters",
            "has_machine_protocol",
            "is_abroad_form",
            "total_none_votes",
            "total_valid_candidate_votes",
            "total_ballots_found",
            "turnout",
            "valid_candidate_vote_rate",
        ],
    )
    write_csv(
        output_dir / "votes_long.csv",
        votes,
        ["form_no", "section_id", "admin_id", "party_id", "party_name", "valid_votes", "paper_votes", "machine_votes"],
    )
    write_csv(
        output_dir / "polling_stations_2026.csv",
        station_results,
        [
            "section_id",
            "region_id",
            "municipality_code",
            "admin_area_code",
            "precinct_code",
            "is_abroad",
            "admin_id",
            "admin_name",
            "ekatte",
            "place_name",
            "address",
            "longitude",
            "latitude",
            "is_mobile",
            "is_ship",
            "machines_count",
            "form_no",
            "voting_mode",
            "registered_voters",
            "registered_voters_initial",
            "voters_added_election_day",
            "voters_signed",
            "total_ballots_found",
            "invalid_paper_ballots",
            "total_none_votes",
            "total_valid_candidate_votes",
            "total_valid_candidate_votes_protocol",
            "valid_votes_from_votes_table",
            "valid_vote_protocol_minus_votes_table",
            "paper_votes_from_votes_table",
            "machine_votes_from_votes_table",
            "turnout",
            "valid_candidate_vote_rate",
            "progressive_bulgaria_votes",
            "progressive_bulgaria_share",
            "progressive_bulgaria_share_of_ballots_found",
        ],
    )

    manifest = {
        "tables_dir": str(tables_dir),
        "output_dir": str(output_dir),
        "rows": {
            "parties": len(parties),
            "sections": len(sections),
            "protocols": len(protocols),
            "votes_long": len(votes),
            "polling_stations_2026": len(station_results),
        },
    }
    (output_dir / "preprocess_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tables-dir",
        type=Path,
        default=Path("data/interim/cik_2026/tables"),
        help="Directory containing extracted CIK text tables.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/cik_2026"),
        help="Directory for normalized CSV outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    preprocess(args.tables_dir.resolve(), args.output_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
