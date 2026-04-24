#!/usr/bin/env python3
"""Regional checks for turnout and Progressive Bulgaria station patterns."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


NATIONAL_PB_SHARE = 0.4459414917059549


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean_float(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or pd.isna(denominator):
        return None
    return float(numerator / denominator)


def pearson_corr(x: pd.Series, y: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    return float(np.corrcoef(x[mask].to_numpy(dtype=float), y[mask].to_numpy(dtype=float))[0, 1])


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


def robust_z(values: pd.Series, center: float, mad: float) -> pd.Series:
    if mad <= 0 or pd.isna(mad):
        std = values.std(ddof=0)
        if std <= 0 or pd.isna(std):
            return pd.Series(np.zeros(len(values)), index=values.index)
        return (values - center) / std
    return 0.6745 * (values - center) / mad


def make_region_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region_id, group in sorted(df.groupby("region_id"), key=lambda item: item[0]):
        registered = int(group["registered_voters"].sum())
        voters_signed = int(group["voters_signed"].sum())
        valid_votes = int(group["total_valid_candidate_votes"].sum())
        pb_votes = int(group["progressive_bulgaria_votes"].sum())
        pb_share = pb_votes / valid_votes if valid_votes else 0
        turnout = voters_signed / registered if registered else 0
        rows.append(
            {
                "region_id": region_id,
                "region_name": str(group["admin_name"].iloc[0]),
                "is_abroad_region": int(region_id == "32"),
                "station_count": int(len(group)),
                "registered_voters": registered,
                "voters_signed": voters_signed,
                "turnout_signed_over_registered": turnout,
                "valid_candidate_votes": valid_votes,
                "progressive_bulgaria_votes": pb_votes,
                "progressive_bulgaria_share": pb_share,
                "pb_share_minus_national": pb_share - NATIONAL_PB_SHARE,
                "expected_pb_votes_at_national_share": NATIONAL_PB_SHARE * valid_votes,
                "pb_votes_minus_national_expectation": pb_votes - NATIONAL_PB_SHARE * valid_votes,
                "station_turnout_median": clean_float(group["turnout"].median()),
                "station_pb_share_median": clean_float(group["progressive_bulgaria_share"].median()),
                "pearson_turnout_pb_share": pearson_corr(group["turnout"], group["progressive_bulgaria_share"]),
                "weighted_corr_turnout_pb_share": weighted_corr(
                    group["turnout"], group["progressive_bulgaria_share"], group["total_valid_candidate_votes"]
                ),
                "paper_only_station_count": int((group["voting_mode"] == "paper_only").sum()),
                "mixed_machine_paper_station_count": int((group["voting_mode"] == "mixed_machine_paper").sum()),
            }
        )
    out = pd.DataFrame(rows)
    out["pb_share_rank_desc"] = out["progressive_bulgaria_share"].rank(method="min", ascending=False).astype(int)
    out["turnout_rank_desc"] = out["turnout_signed_over_registered"].rank(method="min", ascending=False).astype(int)
    return out


def add_region_residuals(df: pd.DataFrame, region_summary: pd.DataFrame, validation_issues: pd.DataFrame | None) -> pd.DataFrame:
    region_lookup = region_summary.set_index("region_id")
    out = df.copy()
    out["region_pb_share"] = out["region_id"].map(region_lookup["progressive_bulgaria_share"])
    out["region_turnout"] = out["region_id"].map(region_lookup["turnout_signed_over_registered"])
    out["region_expected_pb_votes"] = out["region_pb_share"] * out["total_valid_candidate_votes"]
    out["pb_votes_minus_region_expectation"] = out["progressive_bulgaria_votes"] - out["region_expected_pb_votes"]
    out["pb_share_minus_region_share"] = out["progressive_bulgaria_share"] - out["region_pb_share"]
    out["turnout_minus_region_turnout"] = out["turnout"] - out["region_turnout"]

    variance = out["total_valid_candidate_votes"] * out["region_pb_share"] * (1 - out["region_pb_share"])
    out["pb_binomial_style_z"] = np.where(variance > 0, out["pb_votes_minus_region_expectation"] / np.sqrt(variance), 0.0)

    out["pb_share_region_robust_z"] = 0.0
    out["turnout_region_robust_z"] = 0.0
    for region_id, group in out.groupby("region_id"):
        pb_center = group["progressive_bulgaria_share"].median()
        pb_mad = (group["progressive_bulgaria_share"] - pb_center).abs().median()
        turnout_center = group["turnout"].median()
        turnout_mad = (group["turnout"] - turnout_center).abs().median()
        out.loc[group.index, "pb_share_region_robust_z"] = robust_z(group["progressive_bulgaria_share"], pb_center, pb_mad)
        out.loc[group.index, "turnout_region_robust_z"] = robust_z(group["turnout"], turnout_center, turnout_mad)

    if validation_issues is not None and not validation_issues.empty:
        counts = validation_issues.groupby("section_id").size()
        out["validation_issue_count"] = out["section_id"].map(counts).fillna(0).astype(int)
    else:
        out["validation_issue_count"] = 0

    out["absolute_high_turnout_high_share"] = (
        (out["turnout"] >= 0.80)
        & (out["progressive_bulgaria_share"] >= 0.70)
        & (out["total_valid_candidate_votes"] >= 50)
    ).astype(int)
    out["relative_high_turnout_high_share"] = (
        (out["turnout"] >= out["region_turnout"] + 0.20)
        & (out["progressive_bulgaria_share"] >= out["region_pb_share"] + 0.20)
        & (out["total_valid_candidate_votes"] >= 50)
    ).astype(int)
    out["positive_residual_lead"] = (
        (out["total_valid_candidate_votes"] >= 50)
        & (out["pb_votes_minus_region_expectation"] >= 50)
        & (out["pb_binomial_style_z"] >= 4)
    ).astype(int)
    out["regional_lead_score"] = (
        (out["absolute_high_turnout_high_share"] == 1).astype(int)
        + (out["relative_high_turnout_high_share"] == 1).astype(int)
        + (out["positive_residual_lead"] == 1).astype(int)
        + ((out["pb_share_region_robust_z"] >= 3) & (out["total_valid_candidate_votes"] >= 50)).astype(int)
        + ((out["turnout_region_robust_z"] >= 3) & (out["total_valid_candidate_votes"] >= 50)).astype(int)
        + (out["validation_issue_count"] > 0).astype(int)
    )
    return out


def make_region_flags(station_residuals: pd.DataFrame, region_summary: pd.DataFrame) -> pd.DataFrame:
    agg = (
        station_residuals.groupby("region_id")
        .agg(
            absolute_high_turnout_high_share_stations=("absolute_high_turnout_high_share", "sum"),
            relative_high_turnout_high_share_stations=("relative_high_turnout_high_share", "sum"),
            positive_residual_lead_stations=("positive_residual_lead", "sum"),
            validation_issue_stations=("validation_issue_count", lambda s: int((s > 0).sum())),
            max_positive_pb_vote_residual=("pb_votes_minus_region_expectation", "max"),
            min_negative_pb_vote_residual=("pb_votes_minus_region_expectation", "min"),
            max_pb_share_robust_z=("pb_share_region_robust_z", "max"),
            max_turnout_robust_z=("turnout_region_robust_z", "max"),
        )
        .reset_index()
    )
    merged = region_summary.merge(agg, on="region_id", how="left")
    for column in [
        "absolute_high_turnout_high_share_stations",
        "relative_high_turnout_high_share_stations",
        "positive_residual_lead_stations",
        "validation_issue_stations",
    ]:
        merged[column] = merged[column].fillna(0).astype(int)
    merged["regional_attention_score"] = (
        merged["relative_high_turnout_high_share_stations"]
        + merged["positive_residual_lead_stations"]
        + (merged["weighted_corr_turnout_pb_share"].fillna(0) >= 0.20).astype(int)
        + (merged["validation_issue_stations"] > 0).astype(int)
    )
    return merged.sort_values(
        ["regional_attention_score", "relative_high_turnout_high_share_stations", "positive_residual_lead_stations"],
        ascending=False,
    )


def svg_bar_chart(rows: list[dict[str, Any]], path: Path, title: str, value_key: str, label_key: str = "region_id") -> None:
    width = 1120
    height = 620
    margin_left = 72
    margin_right = 38
    margin_top = 48
    margin_bottom = 92
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_value = max(float(row[value_key]) for row in rows)
    min_value = min(float(row[value_key]) for row in rows)
    y_min = min(0.0, min_value)
    y_max = max(0.0, max_value)
    if y_max == y_min:
        y_max = y_min + 1

    def y_map(value: float) -> float:
        return margin_top + plot_h - (value - y_min) / (y_max - y_min) * plot_h

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(f'<text x="{margin_left}" y="30" font-family="Arial, sans-serif" font-size="20" font-weight="700">{html.escape(title)}</text>')
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    zero_y = y_map(0)
    elements.append(f'<line x1="{margin_left}" y1="{zero_y:.2f}" x2="{margin_left + plot_w}" y2="{zero_y:.2f}" stroke="#475569" stroke-width="1.2"/>')

    sorted_rows = sorted(rows, key=lambda row: float(row[value_key]), reverse=True)
    bar_slot = plot_w / len(sorted_rows)
    bar_w = bar_slot * 0.68
    for i, row in enumerate(sorted_rows):
        value = float(row[value_key])
        x = margin_left + i * bar_slot + (bar_slot - bar_w) / 2
        y = y_map(max(value, 0))
        bar_h = abs(y_map(value) - zero_y)
        fill = "#2563eb" if value >= 0 else "#dc2626"
        if value < 0:
            y = zero_y
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="{fill}"/>')
        label = str(row[label_key])
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 56}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" transform="rotate(-45 {x + bar_w / 2:.2f} {height - 56})">{html.escape(label)}</text>'
        )

    for tick in np.linspace(y_min, y_max, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        tick_label = f"{tick * 100:.0f}%" if abs(tick) <= 1.0 else f"{tick:,.0f}"
        elements.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{html.escape(tick_label)}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def analyze(input_csv: Path, validation_issues_csv: Path, tables_dir: Path, figures_dir: Path, docs_dir: Path) -> None:
    df = pd.read_csv(
        input_csv,
        dtype={"section_id": str, "region_id": str, "municipality_code": str, "admin_area_code": str, "precinct_code": str},
    )
    df = df[(df["registered_voters"] > 0) & (df["total_valid_candidate_votes"] > 0)].copy()
    validation_issues = None
    if validation_issues_csv.exists():
        validation_issues = pd.read_csv(validation_issues_csv, dtype={"section_id": str})

    region_summary = make_region_summary(df)
    station_residuals = add_region_residuals(df, region_summary, validation_issues)
    region_flags = make_region_flags(station_residuals, region_summary)

    station_fields = [
        "section_id",
        "region_id",
        "admin_name",
        "place_name",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "region_turnout",
        "turnout_minus_region_turnout",
        "turnout_region_robust_z",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "region_pb_share",
        "pb_share_minus_region_share",
        "region_expected_pb_votes",
        "pb_votes_minus_region_expectation",
        "pb_binomial_style_z",
        "pb_share_region_robust_z",
        "validation_issue_count",
        "absolute_high_turnout_high_share",
        "relative_high_turnout_high_share",
        "positive_residual_lead",
        "regional_lead_score",
    ]
    lead_stations = station_residuals[
        (station_residuals["regional_lead_score"] >= 2)
        | (station_residuals["relative_high_turnout_high_share"] == 1)
        | (station_residuals["positive_residual_lead"] == 1)
    ].sort_values(
        ["regional_lead_score", "pb_votes_minus_region_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )
    strong_lead_stations = station_residuals[station_residuals["regional_lead_score"] >= 2].sort_values(
        ["regional_lead_score", "pb_votes_minus_region_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )

    output_station_residuals = station_residuals.sort_values(
        ["pb_votes_minus_region_expectation", "progressive_bulgaria_votes"], ascending=False
    )

    tables_dir.mkdir(parents=True, exist_ok=True)
    region_summary.to_csv(tables_dir / "regional_summary_2026.csv", index=False)
    region_flags.to_csv(tables_dir / "regional_attention_summary_2026.csv", index=False)
    output_station_residuals[station_fields].to_csv(tables_dir / "station_regional_residuals_2026.csv", index=False)
    lead_stations[station_fields].to_csv(tables_dir / "regional_lead_stations_2026.csv", index=False)
    strong_lead_stations[station_fields].to_csv(tables_dir / "regional_strong_lead_stations_2026.csv", index=False)

    domestic_regions = region_summary[region_summary["region_id"] != "32"].to_dict("records")
    all_regions = region_summary.to_dict("records")
    svg_bar_chart(all_regions, figures_dir / "regional_progressive_bulgaria_share_2026.svg", "Progressive Bulgaria Share by Region", "progressive_bulgaria_share")
    svg_bar_chart(all_regions, figures_dir / "regional_turnout_2026.svg", "Signed Turnout by Region", "turnout_signed_over_registered")
    svg_bar_chart(
        all_regions,
        figures_dir / "regional_turnout_pb_weighted_corr_2026.svg",
        "Weighted Turnout / Progressive Bulgaria Correlation by Region",
        "weighted_corr_turnout_pb_share",
    )

    top_regions_by_share = region_summary.sort_values("progressive_bulgaria_share", ascending=False).head(8)
    bottom_regions_by_share = region_summary.sort_values("progressive_bulgaria_share", ascending=True).head(8)
    top_positive_corr = region_summary.sort_values("weighted_corr_turnout_pb_share", ascending=False).head(8)
    top_negative_corr = region_summary.sort_values("weighted_corr_turnout_pb_share", ascending=True).head(8)
    top_attention = region_flags.head(12)

    summary = {
        "input_csv": str(input_csv),
        "station_count": int(len(df)),
        "region_count": int(region_summary.shape[0]),
        "domestic_region_count": len(domestic_regions),
        "lead_station_count": int(len(lead_stations)),
        "strong_lead_station_count": int(len(strong_lead_stations)),
        "lead_station_score_counts": {
            str(int(score)): int(count)
            for score, count in lead_stations["regional_lead_score"].value_counts().sort_index().items()
        },
        "relative_high_turnout_high_share_station_count": int(station_residuals["relative_high_turnout_high_share"].sum()),
        "positive_residual_lead_station_count": int(station_residuals["positive_residual_lead"].sum()),
        "absolute_high_turnout_high_share_station_count": int(station_residuals["absolute_high_turnout_high_share"].sum()),
        "regions_with_weighted_corr_gte_0_20": int((region_summary["weighted_corr_turnout_pb_share"] >= 0.20).sum()),
        "regions_with_weighted_corr_lte_minus_0_20": int((region_summary["weighted_corr_turnout_pb_share"] <= -0.20).sum()),
        "figures": [
            str(figures_dir / "regional_progressive_bulgaria_share_2026.svg"),
            str(figures_dir / "regional_turnout_2026.svg"),
            str(figures_dir / "regional_turnout_pb_weighted_corr_2026.svg"),
        ],
    }
    write_json(tables_dir / "regional_checks_summary_2026.json", summary)

    def region_rows_markdown(rows: pd.DataFrame, cols: list[str]) -> str:
        lines = []
        for _, row in rows.iterrows():
            values = []
            for col in cols:
                value = row[col]
                if isinstance(value, float):
                    if "corr" in col:
                        values.append(f"{value:.3f}")
                    elif "share" in col or "turnout" in col:
                        values.append(f"{value:.3%}")
                    else:
                        values.append(f"{value:.3f}")
                else:
                    values.append(f"{value}")
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    note = f"""# Regional Checks

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_regional_checks.py
```

## Generated Outputs

Figures:

- `outputs/figures/regional_progressive_bulgaria_share_2026.svg`
- `outputs/figures/regional_turnout_2026.svg`
- `outputs/figures/regional_turnout_pb_weighted_corr_2026.svg`

Tables:

- `outputs/tables/regional_summary_2026.csv`
- `outputs/tables/regional_attention_summary_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`
- `outputs/tables/regional_lead_stations_2026.csv`
- `outputs/tables/regional_strong_lead_stations_2026.csv`
- `outputs/tables/regional_checks_summary_2026.json`

## Summary

- Regions checked: `{region_summary.shape[0]}`
- Stations checked: `{len(df):,}`
- Absolute high-turnout/high-share stations: `{int(station_residuals["absolute_high_turnout_high_share"].sum()):,}`
- Relative high-turnout/high-share stations: `{int(station_residuals["relative_high_turnout_high_share"].sum()):,}`
- Positive regional residual lead stations: `{int(station_residuals["positive_residual_lead"].sum()):,}`
- Broad regional lead stations written to table: `{len(lead_stations):,}`
- Stronger multi-signal lead stations with score >= 2: `{len(strong_lead_stations):,}`

Definitions:

- `relative_high_turnout_high_share`: turnout is at least 20 percentage points above the region turnout and Progressive Bulgaria share is at least 20 percentage points above the region share, with at least 50 valid candidate-list votes.
- `positive_residual_lead`: at least 50 Progressive Bulgaria votes above regional expectation and a binomial-style standardized residual of at least 4. This is a ranking heuristic, not a formal proof test.

## Highest Progressive Bulgaria Regional Shares

| Region | Name | Stations | Turnout | Progressive Bulgaria share |
|---|---|---:|---:|---:|
{region_rows_markdown(top_regions_by_share, ["region_id", "region_name", "station_count", "turnout_signed_over_registered", "progressive_bulgaria_share"])}

## Lowest Progressive Bulgaria Regional Shares

| Region | Name | Stations | Turnout | Progressive Bulgaria share |
|---|---|---:|---:|---:|
{region_rows_markdown(bottom_regions_by_share, ["region_id", "region_name", "station_count", "turnout_signed_over_registered", "progressive_bulgaria_share"])}

## Highest Weighted Turnout/Share Correlations

| Region | Name | Stations | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|---:|
{region_rows_markdown(top_positive_corr, ["region_id", "region_name", "station_count", "weighted_corr_turnout_pb_share", "progressive_bulgaria_share"])}

## Lowest Weighted Turnout/Share Correlations

| Region | Name | Stations | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|---:|
{region_rows_markdown(top_negative_corr, ["region_id", "region_name", "station_count", "weighted_corr_turnout_pb_share", "progressive_bulgaria_share"])}

## Regions With Most Regional Leads

| Region | Name | Attention score | Relative high-turnout/high-share | Positive residual leads | Validation issue stations |
|---|---|---:|---:|---:|---:|
"""
    for _, row in top_attention.iterrows():
        note += (
            f"| {row['region_id']} | {row['region_name']} | {int(row['regional_attention_score'])} | "
            f"{int(row['relative_high_turnout_high_share_stations'])} | {int(row['positive_residual_lead_stations'])} | "
            f"{int(row['validation_issue_stations'])} |\n"
        )

    note += """
## Initial Interpretation

The regional checks still do not show a broad high-turnout/high-Progressive-Bulgaria pattern. Most regions with strong turnout/share relationships are negative, and only a few regions have weighted positive correlations above 0.20.

The next useful step is matched controls inside municipalities or neighboring settlements. The regional residual table gives a ranked list of stations to compare locally, but by itself it is not evidence of fraud because real local political geography can create large station-level residuals.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "regional_checks_2026.md").write_text(note, encoding="utf-8")
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
        "--validation-issues-csv",
        type=Path,
        default=Path("outputs/tables/validation_issues.csv"),
        help="Validation issue CSV, if available.",
    )
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"), help="Directory for output tables.")
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"), help="Directory for output figures.")
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"), help="Directory for generated notes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.input_csv.resolve(),
        args.validation_issues_csv.resolve(),
        args.tables_dir.resolve(),
        args.figures_dir.resolve(),
        args.docs_dir.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
