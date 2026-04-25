#!/usr/bin/env python3
"""Build a nearest-prior historical baseline from the October 2024 CIK archive."""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import math
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PPDB_2024_PARTY_ID = 26
GERB_2024_PARTY_ID = 18
DPS_NEW_2024_PARTY_ID = 8
APS_2024_PARTY_ID = 13


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def to_int(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    value = value.strip()
    if value == "":
        return 0
    return int(value)


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or pd.isna(denominator):
        return None
    return float(numerator / denominator)


def read_table_from_zip(zf: zipfile.ZipFile, prefix: str) -> list[list[str]]:
    matches = [name for name in zf.namelist() if name.split("/")[-1].startswith(prefix + "_") and name.endswith(".txt")]
    if len(matches) != 1:
        raise ValueError(f"Expected one {prefix}_*.txt entry, found {len(matches)}")
    data = zf.read(matches[0]).decode("utf-8-sig")
    return list(csv.reader(io.StringIO(data), delimiter=";"))


def parse_2024_archive(archive: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(archive) as zf:
        party_rows = read_table_from_zip(zf, "cik_parties")
        protocol_rows = read_table_from_zip(zf, "protocols")
        vote_rows = read_table_from_zip(zf, "votes")

    party_names = {to_int(row[0]): row[1] for row in party_rows}
    stations = []
    for row in protocol_rows:
        section_id = row[1]
        registered = to_int(row[7]) + to_int(row[8])
        voters_signed = to_int(row[9])
        valid_paper = to_int(row[15])
        valid_machine = to_int(row[18])
        stations.append(
            {
                "section_id": section_id,
                "registered_voters_2024": registered,
                "voters_signed_2024": voters_signed,
                "turnout_2024": safe_divide(voters_signed, registered),
                "valid_candidate_votes_2024": valid_paper + valid_machine,
            }
        )
    stations_df = pd.DataFrame(stations)

    vote_records = []
    for row in vote_rows:
        section_id = row[1]
        fields = row[3:]
        for idx in range(0, len(fields), 4):
            if idx + 3 >= len(fields):
                continue
            party_id = to_int(fields[idx])
            valid_votes = to_int(fields[idx + 1])
            vote_records.append(
                {
                    "section_id": section_id,
                    "party_id": party_id,
                    "party_name": party_names.get(party_id, ""),
                    "valid_votes_2024": valid_votes,
                }
            )
    votes_df = pd.DataFrame(vote_records)
    votes_df = votes_df.merge(stations_df[["section_id", "valid_candidate_votes_2024"]], on="section_id", how="left")
    votes_df["party_share_2024"] = np.where(
        votes_df["valid_candidate_votes_2024"] > 0,
        votes_df["valid_votes_2024"] / votes_df["valid_candidate_votes_2024"],
        np.nan,
    )

    ordered = votes_df.sort_values(["section_id", "valid_votes_2024", "party_id"], ascending=[True, False, True])
    leaders = ordered.groupby("section_id").first().reset_index()
    leaders = leaders.rename(
        columns={
            "party_id": "top_party_id_2024",
            "party_name": "top_party_name_2024",
            "valid_votes_2024": "top_party_votes_2024",
            "party_share_2024": "top_party_share_2024",
        }
    )

    pivot = votes_df.pivot_table(index="section_id", columns="party_id", values="valid_votes_2024", aggfunc="sum", fill_value=0)
    for party_id in [PPDB_2024_PARTY_ID, GERB_2024_PARTY_ID, DPS_NEW_2024_PARTY_ID, APS_2024_PARTY_ID]:
        if party_id not in pivot.columns:
            pivot[party_id] = 0
    pivot = pivot.reset_index()
    pivot = pivot.rename(
        columns={
            PPDB_2024_PARTY_ID: "ppdb_votes_2024",
            GERB_2024_PARTY_ID: "gerb_sds_votes_2024",
            DPS_NEW_2024_PARTY_ID: "dps_new_votes_2024",
            APS_2024_PARTY_ID: "aps_votes_2024",
        }
    )

    station_summary = stations_df.merge(leaders[["section_id", "top_party_id_2024", "top_party_name_2024", "top_party_votes_2024", "top_party_share_2024"]], on="section_id", how="left")
    station_summary = station_summary.merge(
        pivot[["section_id", "ppdb_votes_2024", "gerb_sds_votes_2024", "dps_new_votes_2024", "aps_votes_2024"]],
        on="section_id",
        how="left",
    )
    for column in ["ppdb_votes_2024", "gerb_sds_votes_2024", "dps_new_votes_2024", "aps_votes_2024"]:
        station_summary[column] = station_summary[column].fillna(0).astype(int)
    station_summary["ppdb_share_2024"] = station_summary["ppdb_votes_2024"] / station_summary["valid_candidate_votes_2024"].replace(0, np.nan)
    station_summary["gerb_sds_share_2024"] = station_summary["gerb_sds_votes_2024"] / station_summary["valid_candidate_votes_2024"].replace(0, np.nan)
    station_summary["ppdb_plus_gerb_share_2024"] = (
        station_summary["ppdb_votes_2024"] + station_summary["gerb_sds_votes_2024"]
    ) / station_summary["valid_candidate_votes_2024"].replace(0, np.nan)
    station_summary["dps_plus_aps_share_2024"] = (
        station_summary["dps_new_votes_2024"] + station_summary["aps_votes_2024"]
    ) / station_summary["valid_candidate_votes_2024"].replace(0, np.nan)
    return station_summary, votes_df


def weighted_corr(x: pd.Series, y: pd.Series, weights: pd.Series) -> float | None:
    mask = x.notna() & y.notna() & weights.notna() & (weights > 0)
    if mask.sum() < 3:
        return None
    xv = x[mask].to_numpy(dtype=float)
    yv = y[mask].to_numpy(dtype=float)
    w = weights[mask].to_numpy(dtype=float)
    wx = np.average(xv, weights=w)
    wy = np.average(yv, weights=w)
    cov = np.average((xv - wx) * (yv - wy), weights=w)
    var_x = np.average((xv - wx) ** 2, weights=w)
    var_y = np.average((yv - wy) ** 2, weights=w)
    if var_x <= 0 or var_y <= 0:
        return None
    return float(cov / math.sqrt(var_x * var_y))


def build_swing_frame(current_csv: Path, historical: pd.DataFrame) -> pd.DataFrame:
    current = pd.read_csv(
        current_csv,
        dtype={"section_id": str, "region_id": str, "municipality_code": str, "admin_area_code": str, "precinct_code": str},
    )
    columns = [
        "section_id",
        "region_id",
        "admin_name",
        "municipality_code",
        "place_name",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
    ]
    out = current[columns].merge(historical, on="section_id", how="inner")
    out["turnout_delta_2026_minus_2024"] = out["turnout"] - out["turnout_2024"]
    out["pb_share_2026_minus_2024_top_party_share"] = out["progressive_bulgaria_share"] - out["top_party_share_2024"]
    out["pb_share_2026_minus_2024_ppdb_share"] = out["progressive_bulgaria_share"] - out["ppdb_share_2024"]
    out["pb_share_2026_minus_2024_ppdb_plus_gerb_share"] = out["progressive_bulgaria_share"] - out["ppdb_plus_gerb_share_2024"]
    out["registered_voter_delta_2026_minus_2024"] = out["registered_voters"] - out["registered_voters_2024"]
    out["valid_vote_delta_2026_minus_2024"] = out["total_valid_candidate_votes"] - out["valid_candidate_votes_2024"]
    out["historical_swing_lead"] = (
        (out["total_valid_candidate_votes"] >= 50)
        & (out["turnout_delta_2026_minus_2024"] >= 0.20)
        & (out["pb_share_2026_minus_2024_top_party_share"] >= 0.20)
    ).astype(int)
    return out.sort_values(
        ["historical_swing_lead", "pb_share_2026_minus_2024_top_party_share", "turnout_delta_2026_minus_2024"],
        ascending=False,
    )


def region_summary(swing: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region_id, group in swing.groupby("region_id"):
        valid_2026 = float(group["total_valid_candidate_votes"].sum())
        pb_2026 = float(group["progressive_bulgaria_votes"].sum())
        valid_2024 = float(group["valid_candidate_votes_2024"].sum())
        top_2024 = float(group["top_party_votes_2024"].sum())
        ppdb_2024 = float(group["ppdb_votes_2024"].sum())
        gerb_2024 = float(group["gerb_sds_votes_2024"].sum())
        reg_2026 = float(group["registered_voters"].sum())
        signed_2026 = float(group["voters_signed"].sum())
        reg_2024 = float(group["registered_voters_2024"].sum())
        signed_2024 = float(group["voters_signed_2024"].sum())
        rows.append(
            {
                "region_id": region_id,
                "region_name": group["admin_name"].iloc[0],
                "matched_station_count": int(len(group)),
                "turnout_2024": safe_divide(signed_2024, reg_2024),
                "turnout_2026": safe_divide(signed_2026, reg_2026),
                "turnout_delta_2026_minus_2024": safe_divide(signed_2026, reg_2026) - safe_divide(signed_2024, reg_2024),
                "pb_share_2026": safe_divide(pb_2026, valid_2026),
                "top_party_share_2024_weighted_sum": safe_divide(top_2024, valid_2024),
                "ppdb_share_2024": safe_divide(ppdb_2024, valid_2024),
                "ppdb_plus_gerb_share_2024": safe_divide(ppdb_2024 + gerb_2024, valid_2024),
                "pb_minus_2024_top_party_share": safe_divide(pb_2026, valid_2026) - safe_divide(top_2024, valid_2024),
                "pb_minus_2024_ppdb_share": safe_divide(pb_2026, valid_2026) - safe_divide(ppdb_2024, valid_2024),
                "historical_swing_lead_stations": int(group["historical_swing_lead"].sum()),
                "weighted_corr_turnout_delta_pb_share_delta_vs_top": weighted_corr(
                    group["turnout_delta_2026_minus_2024"],
                    group["pb_share_2026_minus_2024_top_party_share"],
                    group["total_valid_candidate_votes"],
                ),
            }
        )
    return pd.DataFrame(rows).sort_values("pb_minus_2024_top_party_share", ascending=False)


def svg_region_delta(rows: pd.DataFrame, path: Path) -> None:
    frame = rows.sort_values("pb_minus_2024_top_party_share", ascending=False)
    width = 1120
    height = 620
    margin_left = 80
    margin_right = 36
    margin_top = 54
    margin_bottom = 98
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    min_value = min(0.0, float(frame["pb_minus_2024_top_party_share"].min()))
    max_value = max(0.0, float(frame["pb_minus_2024_top_party_share"].max()))
    if max_value == min_value:
        max_value = min_value + 1

    def y_map(value: float) -> float:
        return margin_top + plot_h - (value - min_value) / (max_value - min_value) * plot_h

    zero_y = y_map(0)
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(
        f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">2026 PB Share Minus 2024 Top-Party Share by Region</text>'
    )
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    elements.append(f'<line x1="{margin_left}" y1="{zero_y:.2f}" x2="{margin_left + plot_w}" y2="{zero_y:.2f}" stroke="#334155"/>')
    slot = plot_w / len(frame)
    bar_w = slot * 0.64
    for idx, (_, row) in enumerate(frame.iterrows()):
        value = float(row["pb_minus_2024_top_party_share"])
        x = margin_left + idx * slot + (slot - bar_w) / 2
        y = y_map(max(value, 0))
        if value < 0:
            y = zero_y
        elements.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{abs(y_map(value) - zero_y):.2f}" fill="{"#0f766e" if value >= 0 else "#dc2626"}"/>'
        )
        label = str(row["region_id"])
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 58}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" transform="rotate(-45 {x + bar_w / 2:.2f} {height - 58})">{html.escape(label)}</text>'
        )
    for tick in np.linspace(min_value, max_value, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick:.0%}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def markdown_rows(frame: pd.DataFrame, columns: list[str], limit: int = 12) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |\n"
    lines = []
    for _, row in frame.head(limit).iterrows():
        values = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                if "share" in column or "turnout" in column or "delta" in column:
                    values.append(f"{value:.1%}")
                else:
                    values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_document(docs_dir: Path, summary: dict[str, Any], swing: pd.DataFrame, regions: pd.DataFrame) -> None:
    leads = swing[swing["historical_swing_lead"] == 1]
    top_regions = regions.head(12)
    note = f"""# Historical Baseline: October 2024 to April 2026

## Inputs

- `data/raw/cik_historical/october_2024_parliamentary.zip`
- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/build_historical_baseline.py
```

## Generated Outputs

- `data/processed/historical_baselines.csv`
- `outputs/tables/historical_station_swing_2024_2026.csv`
- `outputs/tables/historical_swing_leads_2024_2026.csv`
- `outputs/tables/historical_region_swing_2024_2026.csv`
- `outputs/tables/historical_summary_2024_2026.json`
- `outputs/figures/historical_region_pb_minus_2024_top_2026.svg`

## Method

This is a conservative nearest-prior baseline using exact polling-section ID matches between the official 27 October 2024 archive and the 19 April 2026 data. It does not assume that Progressive Bulgaria has a single direct predecessor. It reports comparisons to:

- the strongest 2024 party in the same station;
- 2024 PP-DB;
- 2024 PP-DB plus GERB-SDS as a broad non-identical reference pool.

## Summary

- 2024 stations parsed: `{summary["historical_2024_station_count"]:,}`
- 2026 stations: `{summary["current_2026_station_count"]:,}`
- Exact section matches: `{summary["matched_section_count"]:,}`
- Historical swing lead stations: `{summary["historical_swing_lead_count"]:,}`
- Weighted turnout-delta / PB-minus-2024-top-share correlation: `{summary["weighted_corr_turnout_delta_pb_minus_2024_top"]:.3f}`

## Top Regions by PB 2026 Minus 2024 Top-Party Share

| Region | Name | Matched sections | Turnout delta | PB 2026 | 2024 top-party weighted share | PB minus 2024 top-party share | Swing leads |
|---|---|---:|---:|---:|---:|---:|---:|
{markdown_rows(top_regions, ["region_id", "region_name", "matched_station_count", "turnout_delta_2026_minus_2024", "pb_share_2026", "top_party_share_2024_weighted_sum", "pb_minus_2024_top_party_share", "historical_swing_lead_stations"])}

## Top Station Swing Leads

Definition: at least 50 valid votes in 2026, turnout at least 20 percentage points above 2024, and Progressive Bulgaria share at least 20 percentage points above the strongest 2024 party share in the same station.

| Section | Region | Place | Turnout 2024 | Turnout 2026 | PB 2026 | 2024 top party | 2024 top share | PB minus 2024 top share |
|---|---|---|---:|---:|---:|---|---:|---:|
{markdown_rows(leads, ["section_id", "region_id", "place_name", "turnout_2024", "turnout", "progressive_bulgaria_share", "top_party_name_2024", "top_party_share_2024", "pb_share_2026_minus_2024_top_party_share"])}

## Interpretation

The historical pass is useful for prioritization, but it should not be treated as a direct fraud test. Exact section IDs can still hide boundary changes, and a new national political alignment can legitimately produce large station-level swings. The strongest historical leads are most useful when they overlap with matched-control leads, spatial clusters, validation issues, or protocol-review priorities.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "historical_baseline_2026.md").write_text(note, encoding="utf-8")


def analyze(archive: Path, current_csv: Path, processed_dir: Path, tables_dir: Path, figures_dir: Path, docs_dir: Path) -> None:
    historical, _votes = parse_2024_archive(archive)
    swing = build_swing_frame(current_csv, historical)
    regions = region_summary(swing)
    leads = swing[swing["historical_swing_lead"] == 1].copy()
    leads = leads.sort_values(
        ["pb_share_2026_minus_2024_top_party_share", "turnout_delta_2026_minus_2024", "progressive_bulgaria_votes"],
        ascending=False,
    )

    processed_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    swing.to_csv(processed_dir / "historical_baselines.csv", index=False)
    swing.to_csv(tables_dir / "historical_station_swing_2024_2026.csv", index=False)
    leads.to_csv(tables_dir / "historical_swing_leads_2024_2026.csv", index=False)
    regions.to_csv(tables_dir / "historical_region_swing_2024_2026.csv", index=False)
    svg_region_delta(regions, figures_dir / "historical_region_pb_minus_2024_top_2026.svg")

    summary = {
        "historical_2024_station_count": int(len(historical)),
        "current_2026_station_count": int(len(pd.read_csv(current_csv, usecols=["section_id"]))),
        "matched_section_count": int(len(swing)),
        "historical_swing_lead_count": int(leads.shape[0]),
        "weighted_corr_turnout_delta_pb_minus_2024_top": weighted_corr(
            swing["turnout_delta_2026_minus_2024"],
            swing["pb_share_2026_minus_2024_top_party_share"],
            swing["total_valid_candidate_votes"],
        ),
        "median_turnout_delta": float(swing["turnout_delta_2026_minus_2024"].median()),
        "median_pb_minus_2024_top_share": float(swing["pb_share_2026_minus_2024_top_party_share"].median()),
        "outputs": {
            "historical_baselines": str(processed_dir / "historical_baselines.csv"),
            "station_swing": str(tables_dir / "historical_station_swing_2024_2026.csv"),
            "swing_leads": str(tables_dir / "historical_swing_leads_2024_2026.csv"),
            "region_swing": str(tables_dir / "historical_region_swing_2024_2026.csv"),
            "figure": str(figures_dir / "historical_region_pb_minus_2024_top_2026.svg"),
        },
    }
    write_json(tables_dir / "historical_summary_2024_2026.json", summary)
    write_document(docs_dir, summary, swing, regions)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/raw/cik_historical/october_2024_parliamentary.zip"))
    parser.add_argument("--current-csv", type=Path, default=Path("data/processed/cik_2026/polling_stations_2026.csv"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.archive.resolve(),
        args.current_csv.resolve(),
        args.processed_dir.resolve(),
        args.tables_dir.resolve(),
        args.figures_dir.resolve(),
        args.docs_dir.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
