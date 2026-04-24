#!/usr/bin/env python3
"""Validate processed CIK tables and produce aggregate totals."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROGRESSIVE_BULGARIA_PARTY_ID = 21


def read_dicts(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: str | int | None) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, int):
        return value
    return int(value)


def add_issue(issues: list[dict[str, Any]], section_id: str, issue_type: str, details: str) -> None:
    issues.append({"section_id": section_id, "issue_type": issue_type, "details": details})


def duplicate_count(rows: list[dict[str, str]], key: str) -> int:
    counts = Counter(row[key] for row in rows)
    return sum(1 for count in counts.values() if count > 1)


def validate(processed_dir: Path, output_dir: Path) -> None:
    sections = read_dicts(processed_dir / "sections.csv")
    protocols = read_dicts(processed_dir / "protocols.csv")
    votes = read_dicts(processed_dir / "votes_long.csv")
    stations = read_dicts(processed_dir / "polling_stations_2026.csv")

    issues: list[dict[str, Any]] = []

    section_ids = {row["section_id"] for row in sections}
    protocol_ids = {row["section_id"] for row in protocols}
    vote_ids = {row["section_id"] for row in votes}

    for section_id in sorted(section_ids - protocol_ids):
        add_issue(issues, section_id, "missing_protocol", "section exists but no protocol row was found")
    for section_id in sorted(protocol_ids - section_ids):
        add_issue(issues, section_id, "protocol_without_section", "protocol row exists but no section row was found")
    for section_id in sorted(section_ids - vote_ids):
        add_issue(issues, section_id, "missing_vote_row", "section exists but no votes row was found")
    for section_id in sorted(vote_ids - section_ids):
        add_issue(issues, section_id, "vote_row_without_section", "votes row exists but no section row was found")

    protocol_by_section = {row["section_id"]: row for row in protocols}
    vote_sums_by_section: dict[str, dict[str, int]] = defaultdict(lambda: {"valid_votes": 0, "paper_votes": 0, "machine_votes": 0})
    party_totals: dict[tuple[int, str], dict[str, int]] = defaultdict(lambda: {"valid_votes": 0, "paper_votes": 0, "machine_votes": 0, "station_entries": 0})
    region_party_totals: dict[tuple[str, int, str], dict[str, int]] = defaultdict(lambda: {"valid_votes": 0, "paper_votes": 0, "machine_votes": 0, "station_entries": 0})
    vote_component_mismatches = 0

    for vote in votes:
        section_id = vote["section_id"]
        party_id = to_int(vote["party_id"])
        party_name = vote["party_name"]
        valid_votes = to_int(vote["valid_votes"])
        paper_votes = to_int(vote["paper_votes"])
        machine_votes = to_int(vote["machine_votes"])
        if valid_votes != paper_votes + machine_votes:
            vote_component_mismatches += 1
            add_issue(
                issues,
                section_id,
                "vote_component_mismatch",
                f"party {party_id}: valid_votes={valid_votes}, paper+machine={paper_votes + machine_votes}",
            )

        vote_sums_by_section[section_id]["valid_votes"] += valid_votes
        vote_sums_by_section[section_id]["paper_votes"] += paper_votes
        vote_sums_by_section[section_id]["machine_votes"] += machine_votes
        party_totals[(party_id, party_name)]["valid_votes"] += valid_votes
        party_totals[(party_id, party_name)]["paper_votes"] += paper_votes
        party_totals[(party_id, party_name)]["machine_votes"] += machine_votes
        party_totals[(party_id, party_name)]["station_entries"] += 1

        region_id = section_id[:2]
        region_party_totals[(region_id, party_id, party_name)]["valid_votes"] += valid_votes
        region_party_totals[(region_id, party_id, party_name)]["paper_votes"] += paper_votes
        region_party_totals[(region_id, party_id, party_name)]["machine_votes"] += machine_votes
        region_party_totals[(region_id, party_id, party_name)]["station_entries"] += 1

    station_vote_mismatches = 0
    protocol_paper_arithmetic_mismatches = 0
    protocol_machine_arithmetic_mismatches = 0
    signed_ballot_mismatches = 0
    turnout_over_registered = 0

    for protocol in protocols:
        section_id = protocol["section_id"]
        vote_sums = vote_sums_by_section[section_id]
        protocol_valid_total = to_int(protocol["total_valid_candidate_votes"])
        protocol_valid_paper = to_int(protocol["valid_paper_candidate_votes"])
        protocol_valid_machine = to_int(protocol["valid_machine_candidate_votes"])

        if (
            protocol_valid_total != vote_sums["valid_votes"]
            or protocol_valid_paper != vote_sums["paper_votes"]
            or protocol_valid_machine != vote_sums["machine_votes"]
        ):
            station_vote_mismatches += 1
            add_issue(
                issues,
                section_id,
                "station_vote_sum_mismatch",
                (
                    f"protocol total/paper/machine={protocol_valid_total}/{protocol_valid_paper}/{protocol_valid_machine}; "
                    f"votes table={vote_sums['valid_votes']}/{vote_sums['paper_votes']}/{vote_sums['machine_votes']}"
                ),
            )

        paper_expected = (
            to_int(protocol["invalid_paper_ballots"])
            + to_int(protocol["paper_none_votes"])
            + to_int(protocol["valid_paper_candidate_votes"])
        )
        if to_int(protocol["paper_ballots_found"]) != paper_expected:
            protocol_paper_arithmetic_mismatches += 1
            add_issue(
                issues,
                section_id,
                "protocol_paper_arithmetic_mismatch",
                f"paper_ballots_found={protocol['paper_ballots_found']}, expected={paper_expected}",
            )

        machine_expected = to_int(protocol["machine_none_votes"]) + to_int(protocol["valid_machine_candidate_votes"])
        if to_int(protocol["machine_ballots_found"]) != machine_expected:
            protocol_machine_arithmetic_mismatches += 1
            add_issue(
                issues,
                section_id,
                "protocol_machine_arithmetic_mismatch",
                f"machine_ballots_found={protocol['machine_ballots_found']}, expected={machine_expected}",
            )

        ballot_total = to_int(protocol["paper_ballots_found"]) + to_int(protocol["machine_ballots_found"])
        if to_int(protocol["voters_signed"]) != ballot_total:
            signed_ballot_mismatches += 1
            add_issue(
                issues,
                section_id,
                "signed_voters_ballots_found_mismatch",
                f"voters_signed={protocol['voters_signed']}, ballots_found={ballot_total}",
            )

        if to_int(protocol["voters_signed"]) > to_int(protocol["registered_voters"]):
            turnout_over_registered += 1
            add_issue(
                issues,
                section_id,
                "turnout_over_registered",
                f"voters_signed={protocol['voters_signed']}, registered_voters={protocol['registered_voters']}",
            )

    national_valid_candidate_votes_protocol = sum(to_int(row["total_valid_candidate_votes"]) for row in protocols)
    national_valid_candidate_votes_votes_table = sum(totals["valid_votes"] for totals in party_totals.values())
    national_ballots_found = sum(to_int(row["total_ballots_found"]) for row in protocols)
    national_registered_voters = sum(to_int(row["registered_voters"]) for row in protocols)
    national_voters_signed = sum(to_int(row["voters_signed"]) for row in protocols)

    party_total_rows = []
    for (party_id, party_name), totals in sorted(party_totals.items()):
        party_total_rows.append(
            {
                "party_id": party_id,
                "party_name": party_name,
                "valid_votes": totals["valid_votes"],
                "paper_votes": totals["paper_votes"],
                "machine_votes": totals["machine_votes"],
                "station_entries": totals["station_entries"],
                "share_of_valid_candidate_votes": totals["valid_votes"] / national_valid_candidate_votes_votes_table if national_valid_candidate_votes_votes_table else "",
            }
        )

    region_party_rows = []
    for (region_id, party_id, party_name), totals in sorted(region_party_totals.items()):
        region_party_rows.append(
            {
                "region_id": region_id,
                "party_id": party_id,
                "party_name": party_name,
                "valid_votes": totals["valid_votes"],
                "paper_votes": totals["paper_votes"],
                "machine_votes": totals["machine_votes"],
                "station_entries": totals["station_entries"],
            }
        )

    progressive_votes = sum(
        totals["valid_votes"]
        for (party_id, _party_name), totals in party_totals.items()
        if party_id == PROGRESSIVE_BULGARIA_PARTY_ID
    )

    issue_counts = Counter(issue["issue_type"] for issue in issues)
    summary = {
        "input_dir": str(processed_dir),
        "output_dir": str(output_dir),
        "row_counts": {
            "sections": len(sections),
            "protocols": len(protocols),
            "votes_long": len(votes),
            "polling_stations_2026": len(stations),
        },
        "duplicate_id_counts": {
            "sections": duplicate_count(sections, "section_id"),
            "protocols": duplicate_count(protocols, "section_id"),
            "polling_stations_2026": duplicate_count(stations, "section_id"),
        },
        "id_set_checks": {
            "sections_equal_protocols": section_ids == protocol_ids,
            "sections_equal_votes": section_ids == vote_ids,
        },
        "validation_checks": {
            "vote_component_mismatches": vote_component_mismatches,
            "station_vote_mismatches": station_vote_mismatches,
            "protocol_paper_arithmetic_mismatches": protocol_paper_arithmetic_mismatches,
            "protocol_machine_arithmetic_mismatches": protocol_machine_arithmetic_mismatches,
            "signed_voters_ballots_found_mismatches": signed_ballot_mismatches,
            "turnout_over_registered": turnout_over_registered,
            "total_issues": len(issues),
            "issue_counts": dict(sorted(issue_counts.items())),
        },
        "national_totals": {
            "registered_voters": national_registered_voters,
            "voters_signed": national_voters_signed,
            "ballots_found": national_ballots_found,
            "valid_candidate_votes_protocol": national_valid_candidate_votes_protocol,
            "valid_candidate_votes_votes_table": national_valid_candidate_votes_votes_table,
            "valid_candidate_votes_protocol_minus_votes_table": national_valid_candidate_votes_protocol - national_valid_candidate_votes_votes_table,
            "progressive_bulgaria_votes": progressive_votes,
            "progressive_bulgaria_share_of_votes_table_valid_candidate_votes": progressive_votes / national_valid_candidate_votes_votes_table if national_valid_candidate_votes_votes_table else None,
            "progressive_bulgaria_share_of_protocol_valid_candidate_votes": progressive_votes / national_valid_candidate_votes_protocol if national_valid_candidate_votes_protocol else None,
            "turnout_signed_over_registered": national_voters_signed / national_registered_voters if national_registered_voters else None,
        },
    }

    write_csv(
        output_dir / "party_totals_2026.csv",
        party_total_rows,
        ["party_id", "party_name", "valid_votes", "paper_votes", "machine_votes", "station_entries", "share_of_valid_candidate_votes"],
    )
    write_csv(
        output_dir / "region_party_totals_2026.csv",
        region_party_rows,
        ["region_id", "party_id", "party_name", "valid_votes", "paper_votes", "machine_votes", "station_entries"],
    )
    write_csv(output_dir / "validation_issues.csv", issues, ["section_id", "issue_type", "details"])
    (output_dir / "validation_summary_2026.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed/cik_2026"),
        help="Directory containing normalized CSV outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/tables"),
        help="Directory for validation tables and summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate(args.processed_dir.resolve(), args.output_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
