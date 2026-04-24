#!/usr/bin/env python3
"""Matched-control checks for station-level Progressive Bulgaria residuals."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MIN_CONTROLS = 5
MAX_CONTROLS = 30


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def abroad_country(place_name: str) -> str:
    if "," not in place_name:
        return place_name.strip()
    return place_name.split(",", 1)[0].strip()


def binomial_style_z(observed: float, total: float, probability: float) -> float | None:
    variance = total * probability * (1 - probability)
    if variance <= 0:
        return None
    return float((observed - total * probability) / math.sqrt(variance))


def make_group_maps(df: pd.DataFrame) -> dict[str, dict[Any, np.ndarray]]:
    group_specs = {
        "domestic_same_municipality_voting_mode": ["region_id", "municipality_code", "voting_mode"],
        "domestic_same_municipality": ["region_id", "municipality_code"],
        "domestic_same_region_voting_mode": ["region_id", "voting_mode"],
        "domestic_same_region": ["region_id"],
        "abroad_same_country_voting_mode": ["abroad_country", "voting_mode"],
        "abroad_same_country": ["abroad_country"],
        "abroad_same_voting_mode": ["voting_mode"],
        "abroad_all": ["region_id"],
    }
    maps: dict[str, dict[Any, np.ndarray]] = {}
    for label, columns in group_specs.items():
        group_map: dict[Any, np.ndarray] = {}
        for key, group in df.groupby(columns, dropna=False):
            group_map[key] = group.index.to_numpy()
        maps[label] = group_map
    return maps


def candidate_group_keys(row: pd.Series) -> list[tuple[str, Any]]:
    if row["region_id"] == "32":
        return [
            ("abroad_same_country_voting_mode", (row["abroad_country"], row["voting_mode"])),
            ("abroad_same_country", row["abroad_country"]),
            ("abroad_same_voting_mode", row["voting_mode"]),
            ("abroad_all", row["region_id"]),
        ]
    return [
        ("domestic_same_municipality_voting_mode", (row["region_id"], row["municipality_code"], row["voting_mode"])),
        ("domestic_same_municipality", (row["region_id"], row["municipality_code"])),
        ("domestic_same_region_voting_mode", (row["region_id"], row["voting_mode"])),
        ("domestic_same_region", row["region_id"]),
    ]


def select_controls(df: pd.DataFrame, group_maps: dict[str, dict[Any, np.ndarray]], idx: int) -> tuple[str, pd.DataFrame]:
    row = df.loc[idx]
    for level, key in candidate_group_keys(row):
        idxs = group_maps[level].get(key)
        if idxs is None:
            continue
        idxs = idxs[idxs != idx]
        if len(idxs) < MIN_CONTROLS:
            continue
        controls = df.loc[idxs].copy()
        target_size = math.log1p(float(row["registered_voters"]))
        controls["size_distance"] = (np.log1p(controls["registered_voters"]) - target_size).abs()
        controls = controls.sort_values(["size_distance", "section_id"]).head(MAX_CONTROLS)
        if len(controls) >= MIN_CONTROLS:
            return level, controls
    return "no_sufficient_controls", pd.DataFrame()


def compare_station(row: pd.Series, controls: pd.DataFrame, group_level: str, regional_score: int) -> dict[str, Any]:
    if controls.empty:
        return {
            "section_id": row["section_id"],
            "region_id": row["region_id"],
            "admin_name": row["admin_name"],
            "place_name": row["place_name"],
            "abroad_country": row["abroad_country"],
            "voting_mode": row["voting_mode"],
            "registered_voters": int(row["registered_voters"]),
            "voters_signed": int(row["voters_signed"]),
            "turnout": row["turnout"],
            "total_valid_candidate_votes": int(row["total_valid_candidate_votes"]),
            "progressive_bulgaria_votes": int(row["progressive_bulgaria_votes"]),
            "progressive_bulgaria_share": row["progressive_bulgaria_share"],
            "control_group_level": group_level,
            "control_count": 0,
            "control_valid_candidate_votes": 0,
            "control_progressive_bulgaria_votes": 0,
            "control_weighted_pb_share": None,
            "control_median_pb_share": None,
            "control_median_turnout": None,
            "control_weighted_turnout": None,
            "pb_share_minus_control": None,
            "turnout_minus_control": None,
            "pb_votes_minus_control_expectation": None,
            "pb_control_z": None,
            "pb_share_percentile_in_controls": None,
            "turnout_percentile_in_controls": None,
            "matched_positive_residual": 0,
            "matched_relative_high_turnout_high_share": 0,
            "regional_lead_score": regional_score,
            "matched_control_score": 0,
        }

    control_valid = float(controls["total_valid_candidate_votes"].sum())
    control_pb = float(controls["progressive_bulgaria_votes"].sum())
    control_registered = float(controls["registered_voters"].sum())
    control_signed = float(controls["voters_signed"].sum())
    control_share = control_pb / control_valid if control_valid else 0.0
    control_turnout = control_signed / control_registered if control_registered else 0.0
    control_median_share = float(controls["progressive_bulgaria_share"].median())
    control_median_turnout = float(controls["turnout"].median())
    target_valid = float(row["total_valid_candidate_votes"])
    target_pb = float(row["progressive_bulgaria_votes"])
    expected_pb = control_share * target_valid
    residual = target_pb - expected_pb
    z = binomial_style_z(target_pb, target_valid, control_share)
    pb_share_percentile = float((controls["progressive_bulgaria_share"] <= row["progressive_bulgaria_share"]).mean())
    turnout_percentile = float((controls["turnout"] <= row["turnout"]).mean())

    matched_positive_residual = int(target_valid >= 50 and residual >= 50 and z is not None and z >= 4)
    matched_relative_high = int(
        target_valid >= 50
        and row["turnout"] >= control_median_turnout + 0.20
        and row["progressive_bulgaria_share"] >= control_share + 0.20
    )
    matched_control_score = (
        matched_positive_residual
        + matched_relative_high
        + int(pb_share_percentile >= 0.95 and target_valid >= 50)
        + int(turnout_percentile >= 0.95 and target_valid >= 50)
        + int(regional_score >= 2)
    )

    return {
        "section_id": row["section_id"],
        "region_id": row["region_id"],
        "admin_name": row["admin_name"],
        "municipality_code": row["municipality_code"],
        "place_name": row["place_name"],
        "abroad_country": row["abroad_country"],
        "voting_mode": row["voting_mode"],
        "registered_voters": int(row["registered_voters"]),
        "voters_signed": int(row["voters_signed"]),
        "turnout": row["turnout"],
        "total_valid_candidate_votes": int(row["total_valid_candidate_votes"]),
        "progressive_bulgaria_votes": int(row["progressive_bulgaria_votes"]),
        "progressive_bulgaria_share": row["progressive_bulgaria_share"],
        "control_group_level": group_level,
        "control_count": int(len(controls)),
        "control_valid_candidate_votes": int(control_valid),
        "control_progressive_bulgaria_votes": int(control_pb),
        "control_weighted_pb_share": control_share,
        "control_median_pb_share": control_median_share,
        "control_median_turnout": control_median_turnout,
        "control_weighted_turnout": control_turnout,
        "pb_share_minus_control": row["progressive_bulgaria_share"] - control_share,
        "turnout_minus_control": row["turnout"] - control_median_turnout,
        "pb_votes_minus_control_expectation": residual,
        "pb_control_z": z,
        "pb_share_percentile_in_controls": pb_share_percentile,
        "turnout_percentile_in_controls": turnout_percentile,
        "matched_positive_residual": matched_positive_residual,
        "matched_relative_high_turnout_high_share": matched_relative_high,
        "regional_lead_score": regional_score,
        "matched_control_score": matched_control_score,
    }


def load_regional_scores(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    rows = pd.read_csv(path, dtype={"section_id": str})
    return dict(zip(rows["section_id"], rows["regional_lead_score"].astype(int), strict=False))


def make_summary(results: pd.DataFrame) -> dict[str, Any]:
    group_rows = []
    for group_level, group in results.groupby("control_group_level"):
        group_rows.append(
            {
                "control_group_level": group_level,
                "station_count": int(len(group)),
                "matched_positive_residual_count": int(group["matched_positive_residual"].sum()),
                "matched_relative_high_turnout_high_share_count": int(group["matched_relative_high_turnout_high_share"].sum()),
                "score_gte_2_count": int((group["matched_control_score"] >= 2).sum()),
                "median_control_count": float(group["control_count"].median()),
            }
        )

    return {
        "station_count": int(len(results)),
        "stations_with_controls": int((results["control_count"] >= MIN_CONTROLS).sum()),
        "stations_without_sufficient_controls": int((results["control_count"] < MIN_CONTROLS).sum()),
        "matched_positive_residual_count": int(results["matched_positive_residual"].sum()),
        "matched_relative_high_turnout_high_share_count": int(results["matched_relative_high_turnout_high_share"].sum()),
        "matched_control_score_counts": {
            str(int(score)): int(count)
            for score, count in results["matched_control_score"].value_counts().sort_index().items()
        },
        "strong_matched_leads_score_gte_2": int((results["matched_control_score"] >= 2).sum()),
        "group_level_summary": sorted(group_rows, key=lambda row: row["station_count"], reverse=True),
    }


def analyze(
    input_csv: Path,
    regional_residuals_csv: Path,
    tables_dir: Path,
    docs_dir: Path,
) -> None:
    df = pd.read_csv(
        input_csv,
        dtype={"section_id": str, "region_id": str, "municipality_code": str, "admin_area_code": str, "precinct_code": str},
    )
    df = df[(df["registered_voters"] > 0) & (df["total_valid_candidate_votes"] > 0)].copy().reset_index(drop=True)
    df["abroad_country"] = np.where(df["region_id"] == "32", df["place_name"].map(abroad_country), "")

    regional_scores = load_regional_scores(regional_residuals_csv)
    group_maps = make_group_maps(df)
    rows = []
    for idx, row in df.iterrows():
        group_level, controls = select_controls(df, group_maps, idx)
        regional_score = int(regional_scores.get(row["section_id"], 0))
        rows.append(compare_station(row, controls, group_level, regional_score))

    results = pd.DataFrame(rows)
    results = results.sort_values(
        ["matched_control_score", "pb_votes_minus_control_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )
    leads = results[
        (results["matched_control_score"] >= 2)
        | (results["matched_positive_residual"] == 1)
        | (results["matched_relative_high_turnout_high_share"] == 1)
    ].copy()
    strong_leads = results[results["matched_control_score"] >= 2].copy()

    output_columns = [
        "section_id",
        "region_id",
        "admin_name",
        "municipality_code",
        "place_name",
        "abroad_country",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "control_group_level",
        "control_count",
        "control_valid_candidate_votes",
        "control_progressive_bulgaria_votes",
        "control_weighted_pb_share",
        "control_median_pb_share",
        "control_median_turnout",
        "control_weighted_turnout",
        "pb_share_minus_control",
        "turnout_minus_control",
        "pb_votes_minus_control_expectation",
        "pb_control_z",
        "pb_share_percentile_in_controls",
        "turnout_percentile_in_controls",
        "matched_positive_residual",
        "matched_relative_high_turnout_high_share",
        "regional_lead_score",
        "matched_control_score",
    ]
    tables_dir.mkdir(parents=True, exist_ok=True)
    results[output_columns].to_csv(tables_dir / "matched_control_results_2026.csv", index=False)
    leads[output_columns].to_csv(tables_dir / "matched_control_leads_2026.csv", index=False)
    strong_leads[output_columns].to_csv(tables_dir / "matched_control_strong_leads_2026.csv", index=False)

    summary = make_summary(results)
    write_rows(
        tables_dir / "matched_control_group_summary_2026.csv",
        summary["group_level_summary"],
        [
            "control_group_level",
            "station_count",
            "matched_positive_residual_count",
            "matched_relative_high_turnout_high_share_count",
            "score_gte_2_count",
            "median_control_count",
        ],
    )
    write_json(tables_dir / "matched_control_summary_2026.json", summary)

    top_strong = strong_leads.head(20)
    top_residual = leads.sort_values("pb_votes_minus_control_expectation", ascending=False).head(20)

    def station_rows_markdown(frame: pd.DataFrame) -> str:
        if frame.empty:
            return "| _none_ |  |  |  |  |  |  |\n"
        lines = []
        for _, row in frame.iterrows():
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(row["section_id"]),
                        str(row["region_id"]),
                        str(row["place_name"]),
                        str(row["control_group_level"]),
                        f"{row['progressive_bulgaria_share']:.1%}",
                        f"{row['control_weighted_pb_share']:.1%}" if pd.notna(row["control_weighted_pb_share"]) else "",
                        f"{row['pb_votes_minus_control_expectation']:.1f}" if pd.notna(row["pb_votes_minus_control_expectation"]) else "",
                        str(int(row["matched_control_score"])),
                    ]
                )
                + " |"
            )
        return "\n".join(lines)

    note = f"""# Matched Controls

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_matched_controls.py
```

## Generated Outputs

- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/matched_control_leads_2026.csv`
- `outputs/tables/matched_control_strong_leads_2026.csv`
- `outputs/tables/matched_control_group_summary_2026.csv`
- `outputs/tables/matched_control_summary_2026.json`

## Method

Each station is compared to up to `{MAX_CONTROLS}` nearest peers by registered-voter size from the most local available group with at least `{MIN_CONTROLS}` controls.

Domestic priority:

1. same region, same municipality code, same voting mode;
2. same region and municipality code;
3. same region and voting mode;
4. same region.

Abroad priority:

1. same country and voting mode;
2. same country;
3. same abroad voting mode;
4. all abroad stations.

## Summary

- Stations checked: `{summary["station_count"]:,}`
- Stations with controls: `{summary["stations_with_controls"]:,}`
- Stations without sufficient controls: `{summary["stations_without_sufficient_controls"]:,}`
- Matched positive residual leads: `{summary["matched_positive_residual_count"]:,}`
- Matched relative high-turnout/high-share leads: `{summary["matched_relative_high_turnout_high_share_count"]:,}`
- Strong matched leads with score >= 2: `{summary["strong_matched_leads_score_gte_2"]:,}`

Score distribution:

| Score | Stations |
|---:|---:|
"""
    for score, count in summary["matched_control_score_counts"].items():
        note += f"| {score} | {count:,} |\n"

    note += """
## Control Group Coverage

| Control group | Stations | Positive residual leads | Relative high-turnout/high-share leads | Score >= 2 |
|---|---:|---:|---:|---:|
"""
    for row in summary["group_level_summary"]:
        note += (
            f"| {row['control_group_level']} | {row['station_count']:,} | "
            f"{row['matched_positive_residual_count']:,} | "
            f"{row['matched_relative_high_turnout_high_share_count']:,} | "
            f"{row['score_gte_2_count']:,} |\n"
        )

    note += """
## Top Strong Matched Leads

| Section | Region | Place | Control group | PB share | Control PB share | PB votes above control expectation | Score |
|---|---|---|---|---:|---:|---:|---:|
"""
    note += station_rows_markdown(top_strong)

    note += """

## Largest Positive Matched Residuals

| Section | Region | Place | Control group | PB share | Control PB share | PB votes above control expectation | Score |
|---|---|---|---|---:|---:|---:|---:|
"""
    note += station_rows_markdown(top_residual)

    note += """

## Initial Interpretation

Matched controls are stricter than regional residuals because they compare stations against local peers. Stations that remain high after this step are better candidates for manual review, especially when they also appear in the regional lead table or have protocol/administrative issues.

These matched-control leads are still not fraud findings. The next step is to examine whether the leads cluster by municipality/settlement and whether they overlap with voting method changes, complaints, RIK decisions, or scanned protocol issues.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "matched_controls_2026.md").write_text(note, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=Path("data/processed/cik_2026/polling_stations_2026.csv"),
        help="Processed station-level CSV.",
    )
    parser.add_argument(
        "--regional-residuals-csv",
        type=Path,
        default=Path("outputs/tables/station_regional_residuals_2026.csv"),
        help="Regional residual output, if available.",
    )
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"), help="Directory for output tables.")
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"), help="Directory for generated notes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.input_csv.resolve(),
        args.regional_residuals_csv.resolve(),
        args.tables_dir.resolve(),
        args.docs_dir.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
