#!/usr/bin/env python3
"""Voting-method checks for the Bulgaria 2026 election audit."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


MIXED_MODE = "mixed_machine_paper"
PAPER_MODE = "paper_only"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or pd.isna(denominator):
        return None
    return float(numerator / denominator)


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


def unique_join(values: pd.Series, limit: int = 8) -> str:
    cleaned = sorted({str(value).strip() for value in values.dropna() if str(value).strip()})
    if len(cleaned) <= limit:
        return "; ".join(cleaned)
    return "; ".join(cleaned[:limit]) + f"; (+{len(cleaned) - limit} more)"


def read_inputs(stations_csv: Path, matched_controls_csv: Path, validation_issues_csv: Path) -> pd.DataFrame:
    dtype = {
        "section_id": str,
        "region_id": str,
        "municipality_code": str,
        "admin_area_code": str,
        "precinct_code": str,
    }
    df = pd.read_csv(stations_csv, dtype=dtype)
    matched = pd.read_csv(matched_controls_csv, dtype=dtype)
    matched_cols = [
        "section_id",
        "control_group_level",
        "control_count",
        "control_weighted_pb_share",
        "pb_share_minus_control",
        "turnout_minus_control",
        "pb_votes_minus_control_expectation",
        "pb_control_z",
        "matched_positive_residual",
        "matched_relative_high_turnout_high_share",
        "regional_lead_score",
        "matched_control_score",
    ]
    df = df.merge(matched[[column for column in matched_cols if column in matched.columns]], on="section_id", how="left")
    for column in [
        "registered_voters",
        "voters_signed",
        "total_ballots_found",
        "invalid_paper_ballots",
        "total_none_votes",
        "total_valid_candidate_votes",
        "paper_votes_from_votes_table",
        "machine_votes_from_votes_table",
        "progressive_bulgaria_votes",
        "control_count",
        "matched_positive_residual",
        "matched_relative_high_turnout_high_share",
        "regional_lead_score",
        "matched_control_score",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    for column in [
        "turnout",
        "valid_candidate_vote_rate",
        "progressive_bulgaria_share",
        "progressive_bulgaria_share_of_ballots_found",
        "control_weighted_pb_share",
        "pb_share_minus_control",
        "turnout_minus_control",
        "pb_votes_minus_control_expectation",
        "pb_control_z",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    if validation_issues_csv.exists():
        issues = pd.read_csv(validation_issues_csv, dtype={"section_id": str})
        issue_counts = issues.groupby("section_id").size()
        issue_types = issues.groupby("section_id")["issue_type"].apply(lambda s: unique_join(s, limit=4))
        df["validation_issue_count"] = df["section_id"].map(issue_counts).fillna(0).astype(int)
        df["validation_issue_types"] = df["section_id"].map(issue_types).fillna("")
    else:
        df["validation_issue_count"] = 0
        df["validation_issue_types"] = ""
    df["strong_matched_lead"] = (df["matched_control_score"].fillna(0) >= 2).astype(int)
    df["paper_vote_share_of_valid"] = np.where(
        df["total_valid_candidate_votes"] > 0,
        df["paper_votes_from_votes_table"] / df["total_valid_candidate_votes"],
        np.nan,
    )
    return df


def summarize_groups(df: pd.DataFrame, by_columns: list[str], group_level: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in df.groupby(by_columns, dropna=False):
        values = key if isinstance(key, tuple) else (key,)
        row = {"group_level": group_level}
        for column, value in zip(by_columns, values, strict=False):
            row[column] = "" if pd.isna(value) else value
        registered = float(group["registered_voters"].sum())
        signed = float(group["voters_signed"].sum())
        valid_votes = float(group["total_valid_candidate_votes"].sum())
        pb_votes = float(group["progressive_bulgaria_votes"].sum())
        ballots = float(group["total_ballots_found"].sum())
        paper_votes = float(group["paper_votes_from_votes_table"].sum())
        machine_votes = float(group["machine_votes_from_votes_table"].sum())
        row.update(
            {
                "station_count": int(len(group)),
                "registered_voters": int(registered),
                "voters_signed": int(signed),
                "turnout": safe_divide(signed, registered),
                "total_ballots_found": int(ballots),
                "invalid_paper_ballots": int(group["invalid_paper_ballots"].sum()),
                "none_votes": int(group["total_none_votes"].sum()),
                "valid_candidate_votes": int(valid_votes),
                "paper_valid_votes": int(paper_votes),
                "machine_valid_votes": int(machine_votes),
                "paper_vote_share_of_valid": safe_divide(paper_votes, valid_votes),
                "progressive_bulgaria_votes": int(pb_votes),
                "progressive_bulgaria_share": safe_divide(pb_votes, valid_votes),
                "progressive_bulgaria_share_of_ballots_found": safe_divide(pb_votes, ballots),
                "median_station_turnout": float(group["turnout"].median()),
                "median_station_progressive_bulgaria_share": float(group["progressive_bulgaria_share"].median()),
                "weighted_turnout_pb_corr": weighted_corr(
                    group["turnout"], group["progressive_bulgaria_share"], group["total_valid_candidate_votes"]
                ),
                "strong_matched_leads": int(group["strong_matched_lead"].sum()),
                "strong_matched_lead_rate": safe_divide(float(group["strong_matched_lead"].sum()), float(len(group))),
                "matched_positive_residual_stations": int(group["matched_positive_residual"].sum()),
                "validation_issue_stations": int((group["validation_issue_count"] > 0).sum()),
                "max_matched_control_score": int(group["matched_control_score"].max()),
                "pb_votes_minus_control_expectation": float(group["pb_votes_minus_control_expectation"].sum(skipna=True)),
            }
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_scope_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    scopes = {
        "all": df,
        "domestic": df[df["region_id"] != "32"],
        "abroad": df[df["region_id"] == "32"],
    }
    for scope, group in scopes.items():
        if group.empty:
            continue
        tmp = summarize_groups(group, ["voting_mode"], scope)
        tmp.insert(0, "scope", scope)
        rows.append(tmp)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def build_local_contrasts(summary: pd.DataFrame, identity_columns: list[str], label: str) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for key, group in summary.groupby(identity_columns, dropna=False):
        modes = {str(row["voting_mode"]): row for _, row in group.iterrows()}
        if MIXED_MODE not in modes or PAPER_MODE not in modes:
            continue
        mixed = modes[MIXED_MODE]
        paper = modes[PAPER_MODE]
        values = key if isinstance(key, tuple) else (key,)
        row = {"contrast_level": label}
        for column, value in zip(identity_columns, values, strict=False):
            row[column] = "" if pd.isna(value) else value
        row.update(
            {
                "mixed_station_count": int(mixed["station_count"]),
                "paper_station_count": int(paper["station_count"]),
                "mixed_valid_candidate_votes": int(mixed["valid_candidate_votes"]),
                "paper_valid_candidate_votes": int(paper["valid_candidate_votes"]),
                "mixed_turnout": mixed["turnout"],
                "paper_turnout": paper["turnout"],
                "paper_minus_mixed_turnout": paper["turnout"] - mixed["turnout"],
                "mixed_pb_share": mixed["progressive_bulgaria_share"],
                "paper_pb_share": paper["progressive_bulgaria_share"],
                "paper_minus_mixed_pb_share": paper["progressive_bulgaria_share"] - mixed["progressive_bulgaria_share"],
                "mixed_strong_lead_rate": mixed["strong_matched_lead_rate"],
                "paper_strong_lead_rate": paper["strong_matched_lead_rate"],
                "paper_minus_mixed_strong_lead_rate": paper["strong_matched_lead_rate"] - mixed["strong_matched_lead_rate"],
                "mixed_strong_matched_leads": int(mixed["strong_matched_leads"]),
                "paper_strong_matched_leads": int(paper["strong_matched_leads"]),
                "paper_minus_mixed_pb_votes_above_control_expectation": paper["pb_votes_minus_control_expectation"]
                - mixed["pb_votes_minus_control_expectation"],
                "mixed_validation_issue_stations": int(mixed["validation_issue_stations"]),
                "paper_validation_issue_stations": int(paper["validation_issue_stations"]),
            }
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        ["paper_minus_mixed_pb_share", "paper_valid_candidate_votes", "paper_strong_matched_leads"],
        ascending=False,
    )


def station_leads(df: pd.DataFrame) -> pd.DataFrame:
    out = df[
        (df["strong_matched_lead"] == 1)
        | (df["matched_positive_residual"] == 1)
        | (df["matched_relative_high_turnout_high_share"] == 1)
        | ((df["validation_issue_count"] > 0) & (df["voting_mode"] == PAPER_MODE))
    ].copy()
    return out.sort_values(
        ["matched_control_score", "pb_votes_minus_control_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )


def svg_method_chart(scope_summary: pd.DataFrame, path: Path) -> None:
    rows = scope_summary[scope_summary["scope"].isin(["domestic", "abroad"])].copy()
    if rows.empty:
        return
    rows["label"] = rows["scope"].astype(str) + " / " + rows["voting_mode"].astype(str)
    rows = rows.sort_values(["scope", "voting_mode"])
    width = 980
    height = 520
    margin_left = 84
    margin_right = 36
    margin_top = 54
    margin_bottom = 142
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_value = max(0.01, float(rows["progressive_bulgaria_share"].max()))

    def y_map(value: float) -> float:
        return margin_top + plot_h - value / max_value * plot_h

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(
        f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">Progressive Bulgaria Share by Voting Method</text>'
    )
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    bar_slot = plot_w / len(rows)
    bar_w = bar_slot * 0.62
    for idx, (_, row) in enumerate(rows.iterrows()):
        value = float(row["progressive_bulgaria_share"])
        x = margin_left + idx * bar_slot + (bar_slot - bar_w) / 2
        y = y_map(value)
        height_bar = margin_top + plot_h - y
        color = "#2563eb" if row["voting_mode"] == MIXED_MODE else "#f97316"
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{height_bar:.2f}" fill="{color}"/>')
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{value:.1%}</text>'
        )
        label = str(row["label"])
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 86}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" transform="rotate(-38 {x + bar_w / 2:.2f} {height - 86})">{html.escape(label)}</text>'
        )
    for tick in np.linspace(0, max_value, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(
            f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick:.0%}</text>'
        )
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
                if "share" in column or "turnout" in column or "rate" in column:
                    values.append(f"{value:.1%}")
                elif "expectation" in column:
                    values.append(f"{value:.1f}")
                else:
                    values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def write_document(
    docs_dir: Path,
    summary: dict[str, Any],
    scope_summary: pd.DataFrame,
    municipality_contrasts: pd.DataFrame,
    abroad_contrasts: pd.DataFrame,
) -> None:
    top_paper_pb = municipality_contrasts[
        (municipality_contrasts["paper_station_count"] >= 2) & (municipality_contrasts["paper_valid_candidate_votes"] >= 100)
    ].sort_values("paper_minus_mixed_pb_share", ascending=False)
    top_paper_leads = municipality_contrasts[
        (municipality_contrasts["paper_station_count"] >= 2) & (municipality_contrasts["paper_valid_candidate_votes"] >= 100)
    ].sort_values("paper_minus_mixed_strong_lead_rate", ascending=False)
    note = f"""# Voting Method Analysis

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_voting_method.py
```

## Generated Outputs

- `outputs/tables/voting_method_summary_2026.csv`
- `outputs/tables/voting_method_region_summary_2026.csv`
- `outputs/tables/voting_method_municipality_contrasts_2026.csv`
- `outputs/tables/voting_method_abroad_contrasts_2026.csv`
- `outputs/tables/voting_method_lead_stations_2026.csv`
- `outputs/tables/voting_method_summary_2026.json`
- `outputs/figures/voting_method_progressive_bulgaria_share_2026.svg`

## Summary

- Stations checked: `{summary["station_count"]:,}`
- Mixed machine/paper stations: `{summary["mixed_machine_paper_stations"]:,}`
- Paper-only stations: `{summary["paper_only_stations"]:,}`
- Municipalities with both voting modes: `{summary["municipality_contrast_count"]:,}`
- Abroad countries/places with both voting modes: `{summary["abroad_contrast_count"]:,}`
- Strong matched-control leads in mixed machine/paper stations: `{summary["mixed_machine_paper_strong_leads"]:,}`
- Strong matched-control leads in paper-only stations: `{summary["paper_only_strong_leads"]:,}`

## National Method Summary

| Scope | Method | Stations | Turnout | PB share | Strong lead rate | Validation issue stations |
|---|---|---:|---:|---:|---:|---:|
{markdown_rows(scope_summary, ["scope", "voting_mode", "station_count", "turnout", "progressive_bulgaria_share", "strong_matched_lead_rate", "validation_issue_stations"], limit=20)}

## Largest Municipal Paper-Only PB-Share Differences

These rows compare paper-only stations with mixed machine/paper stations inside the same region and municipality. They are leads for review, not proof of method manipulation.

| Region | Municipality | Mixed stations | Paper stations | Mixed PB share | Paper PB share | Paper-minus-mixed PB share | Paper lead rate minus mixed |
|---|---|---:|---:|---:|---:|---:|---:|
{markdown_rows(top_paper_pb, ["region_id", "municipality_code", "mixed_station_count", "paper_station_count", "mixed_pb_share", "paper_pb_share", "paper_minus_mixed_pb_share", "paper_minus_mixed_strong_lead_rate"])}

## Largest Municipal Paper-Only Lead-Rate Differences

| Region | Municipality | Mixed stations | Paper stations | Mixed lead rate | Paper lead rate | Difference | Paper PB share |
|---|---|---:|---:|---:|---:|---:|---:|
{markdown_rows(top_paper_leads, ["region_id", "municipality_code", "mixed_station_count", "paper_station_count", "mixed_strong_lead_rate", "paper_strong_lead_rate", "paper_minus_mixed_strong_lead_rate", "paper_pb_share"])}

## Abroad Method Contrasts

| Country/place | Mixed stations | Paper stations | Mixed PB share | Paper PB share | Paper-minus-mixed PB share | Paper lead rate minus mixed |
|---|---:|---:|---:|---:|---:|---:|
{markdown_rows(abroad_contrasts, ["abroad_country", "mixed_station_count", "paper_station_count", "mixed_pb_share", "paper_pb_share", "paper_minus_mixed_pb_share", "paper_minus_mixed_strong_lead_rate"])}

## Initial Interpretation

Voting method is confounded by station size and geography: paper-only stations are usually smaller or abroad-specific, so raw national differences should not be read as causal. The more useful rows are local contrasts where both methods exist in the same municipality or abroad country/place. Any paper-only locality with large Progressive Bulgaria differences should be checked against station size, local political geography, protocol scans, and whether the paper-only status was expected or caused by a machine issue.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "voting_method_2026.md").write_text(note, encoding="utf-8")


def analyze(
    stations_csv: Path,
    matched_controls_csv: Path,
    validation_issues_csv: Path,
    tables_dir: Path,
    figures_dir: Path,
    docs_dir: Path,
) -> None:
    df = read_inputs(stations_csv, matched_controls_csv, validation_issues_csv)
    scope_summary = build_scope_summary(df)
    region_summary = summarize_groups(df, ["region_id", "admin_name", "voting_mode"], "region_method").sort_values(
        ["region_id", "voting_mode"]
    )
    municipality_summary = summarize_groups(
        df[df["region_id"] != "32"], ["region_id", "admin_name", "municipality_code", "voting_mode"], "municipality_method"
    )
    abroad_summary = summarize_groups(df[df["region_id"] == "32"], ["abroad_country", "place_name", "voting_mode"], "abroad_method") if "abroad_country" in df.columns else pd.DataFrame()

    if "abroad_country" not in df.columns:
        df["abroad_country"] = ""
        df.loc[df["region_id"] == "32", "abroad_country"] = df.loc[df["region_id"] == "32", "place_name"].str.split(",", n=1).str[0]
        abroad_summary = summarize_groups(df[df["region_id"] == "32"], ["abroad_country", "place_name", "voting_mode"], "abroad_method")

    municipality_contrasts = build_local_contrasts(
        municipality_summary, ["region_id", "admin_name", "municipality_code"], "municipality"
    )
    abroad_contrasts = build_local_contrasts(abroad_summary, ["abroad_country", "place_name"], "abroad_place")
    leads = station_leads(df)

    station_columns = [
        "section_id",
        "region_id",
        "admin_name",
        "municipality_code",
        "place_name",
        "address",
        "voting_mode",
        "machines_count",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "control_weighted_pb_share",
        "pb_share_minus_control",
        "turnout_minus_control",
        "pb_votes_minus_control_expectation",
        "pb_control_z",
        "matched_control_score",
        "strong_matched_lead",
        "validation_issue_count",
        "validation_issue_types",
    ]

    tables_dir.mkdir(parents=True, exist_ok=True)
    scope_summary.to_csv(tables_dir / "voting_method_summary_2026.csv", index=False)
    region_summary.to_csv(tables_dir / "voting_method_region_summary_2026.csv", index=False)
    municipality_contrasts.to_csv(tables_dir / "voting_method_municipality_contrasts_2026.csv", index=False)
    abroad_contrasts.to_csv(tables_dir / "voting_method_abroad_contrasts_2026.csv", index=False)
    leads[[column for column in station_columns if column in leads.columns]].to_csv(
        tables_dir / "voting_method_lead_stations_2026.csv", index=False
    )
    svg_method_chart(scope_summary, figures_dir / "voting_method_progressive_bulgaria_share_2026.svg")

    summary = {
        "station_count": int(len(df)),
        "mixed_machine_paper_stations": int((df["voting_mode"] == MIXED_MODE).sum()),
        "paper_only_stations": int((df["voting_mode"] == PAPER_MODE).sum()),
        "mixed_machine_paper_strong_leads": int(((df["voting_mode"] == MIXED_MODE) & (df["strong_matched_lead"] == 1)).sum()),
        "paper_only_strong_leads": int(((df["voting_mode"] == PAPER_MODE) & (df["strong_matched_lead"] == 1)).sum()),
        "municipality_contrast_count": int(len(municipality_contrasts)),
        "abroad_contrast_count": int(len(abroad_contrasts)),
        "method_counts": df["voting_mode"].value_counts().to_dict(),
        "outputs": {
            "summary": str(tables_dir / "voting_method_summary_2026.csv"),
            "region_summary": str(tables_dir / "voting_method_region_summary_2026.csv"),
            "municipality_contrasts": str(tables_dir / "voting_method_municipality_contrasts_2026.csv"),
            "abroad_contrasts": str(tables_dir / "voting_method_abroad_contrasts_2026.csv"),
            "lead_stations": str(tables_dir / "voting_method_lead_stations_2026.csv"),
            "figure": str(figures_dir / "voting_method_progressive_bulgaria_share_2026.svg"),
        },
    }
    write_json(tables_dir / "voting_method_summary_2026.json", summary)
    write_document(docs_dir, summary, scope_summary, municipality_contrasts, abroad_contrasts)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations-csv", type=Path, default=Path("data/processed/cik_2026/polling_stations_2026.csv"))
    parser.add_argument("--matched-controls-csv", type=Path, default=Path("outputs/tables/matched_control_results_2026.csv"))
    parser.add_argument("--validation-issues-csv", type=Path, default=Path("outputs/tables/validation_issues.csv"))
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.stations_csv.resolve(),
        args.matched_controls_csv.resolve(),
        args.validation_issues_csv.resolve(),
        args.tables_dir.resolve(),
        args.figures_dir.resolve(),
        args.docs_dir.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
