#!/usr/bin/env python3
"""Build explainable station-level anomaly scores and review samples."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


BASE_RESULTS_URL = "https://results.cik.bg/pe202604"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def unique_join(values: pd.Series, limit: int = 8) -> str:
    cleaned = sorted({str(value).strip() for value in values.dropna() if str(value).strip()})
    if len(cleaned) <= limit:
        return "; ".join(cleaned)
    return "; ".join(cleaned[:limit]) + f"; (+{len(cleaned) - limit} more)"


def read_csv_if_exists(path: Path, dtype: dict[str, Any] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=dtype)


def add_validation(df: pd.DataFrame, validation_issues_csv: Path) -> pd.DataFrame:
    if not validation_issues_csv.exists():
        df["validation_issue_count"] = 0
        df["validation_issue_types"] = ""
        return df
    issues = pd.read_csv(validation_issues_csv, dtype={"section_id": str})
    counts = issues.groupby("section_id").size()
    types = issues.groupby("section_id")["issue_type"].apply(lambda s: unique_join(s, limit=6))
    details = issues.groupby("section_id")["details"].apply(lambda s: unique_join(s, limit=4))
    out = df.copy()
    out["validation_issue_count"] = out["section_id"].map(counts).fillna(0).astype(int)
    out["validation_issue_types"] = out["section_id"].map(types).fillna("")
    out["validation_issue_details"] = out["section_id"].map(details).fillna("")
    return out


def build_base_frame(
    stations_csv: Path,
    matched_controls_csv: Path,
    regional_residuals_csv: Path,
    geo_members_csv: Path,
    station_leaders_csv: Path,
    historical_swing_csv: Path,
    validation_issues_csv: Path,
    voting_method_leads_csv: Path,
) -> pd.DataFrame:
    dtype = {
        "section_id": str,
        "region_id": str,
        "municipality_code": str,
        "admin_area_code": str,
        "precinct_code": str,
    }
    stations = pd.read_csv(stations_csv, dtype=dtype)
    matched = pd.read_csv(matched_controls_csv, dtype=dtype)
    regional = read_csv_if_exists(regional_residuals_csv, dtype=dtype)
    geo = read_csv_if_exists(geo_members_csv, dtype={"section_id": str})
    leaders = read_csv_if_exists(station_leaders_csv, dtype={"section_id": str})
    historical = read_csv_if_exists(historical_swing_csv, dtype={"section_id": str})
    method_leads = read_csv_if_exists(voting_method_leads_csv, dtype={"section_id": str})

    matched_cols = [
        "section_id",
        "control_group_level",
        "control_count",
        "control_weighted_pb_share",
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
    df = stations.merge(matched[[column for column in matched_cols if column in matched.columns]], on="section_id", how="left")

    if not regional.empty:
        regional_cols = [
            "section_id",
            "region_pb_share",
            "pb_votes_minus_region_expectation",
            "pb_binomial_style_z",
            "pb_share_region_robust_z",
            "turnout_region_robust_z",
            "absolute_high_turnout_high_share",
            "relative_high_turnout_high_share",
            "positive_residual_lead",
        ]
        regional = regional[[column for column in regional_cols if column in regional.columns]]
        df = df.merge(regional, on="section_id", how="left", suffixes=("", "_regional"))

    if not geo.empty:
        geo = geo[["section_id", "geo_cluster_id", "is_geo_clustered"]].copy()
        df = df.merge(geo, on="section_id", how="left")
    else:
        df["geo_cluster_id"] = 0
        df["is_geo_clustered"] = 0

    if not leaders.empty:
        leader_cols = [
            "section_id",
            "top_party_id",
            "top_party_name",
            "top_party_share",
            "second_party_name",
            "second_party_share",
            "winner_margin",
            "progressive_bulgaria_rank",
        ]
        df = df.merge(leaders[[column for column in leader_cols if column in leaders.columns]], on="section_id", how="left")

    if not historical.empty:
        historical_cols = [
            "section_id",
            "turnout_2024",
            "top_party_name_2024",
            "top_party_share_2024",
            "ppdb_share_2024",
            "ppdb_plus_gerb_share_2024",
            "turnout_delta_2026_minus_2024",
            "pb_share_2026_minus_2024_top_party_share",
            "pb_share_2026_minus_2024_ppdb_share",
            "pb_share_2026_minus_2024_ppdb_plus_gerb_share",
            "historical_swing_lead",
        ]
        df = df.merge(historical[[column for column in historical_cols if column in historical.columns]], on="section_id", how="left")
    else:
        df["historical_swing_lead"] = 0

    if not method_leads.empty:
        df["voting_method_lead_flag"] = df["section_id"].isin(method_leads["section_id"].astype(str)).astype(int)
    else:
        df["voting_method_lead_flag"] = 0

    df = add_validation(df, validation_issues_csv)

    numeric_columns = [
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_ballots_found",
        "invalid_paper_ballots",
        "total_none_votes",
        "total_valid_candidate_votes",
        "total_valid_candidate_votes_protocol",
        "valid_votes_from_votes_table",
        "valid_vote_protocol_minus_votes_table",
        "paper_votes_from_votes_table",
        "machine_votes_from_votes_table",
        "valid_candidate_vote_rate",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "control_count",
        "control_weighted_pb_share",
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
        "region_pb_share",
        "pb_votes_minus_region_expectation",
        "pb_binomial_style_z",
        "pb_share_region_robust_z",
        "turnout_region_robust_z",
        "absolute_high_turnout_high_share",
        "relative_high_turnout_high_share",
        "positive_residual_lead",
        "geo_cluster_id",
        "is_geo_clustered",
        "top_party_share",
        "second_party_share",
        "winner_margin",
        "progressive_bulgaria_rank",
        "turnout_2024",
        "top_party_share_2024",
        "ppdb_share_2024",
        "ppdb_plus_gerb_share_2024",
        "turnout_delta_2026_minus_2024",
        "pb_share_2026_minus_2024_top_party_share",
        "pb_share_2026_minus_2024_ppdb_share",
        "pb_share_2026_minus_2024_ppdb_plus_gerb_share",
        "historical_swing_lead",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in [
        "matched_positive_residual",
        "matched_relative_high_turnout_high_share",
        "regional_lead_score",
        "matched_control_score",
        "absolute_high_turnout_high_share",
        "relative_high_turnout_high_share",
        "positive_residual_lead",
        "geo_cluster_id",
        "is_geo_clustered",
        "historical_swing_lead",
    ]:
        if column in df.columns:
            df[column] = df[column].fillna(0)
    return df


def evidence_summary(row: pd.Series) -> str:
    parts = []
    if row["matched_control_score"] >= 2:
        parts.append(f"matched-control score {int(row['matched_control_score'])}")
    if row["matched_positive_residual"] == 1:
        parts.append(f"+{row['pb_votes_minus_control_expectation']:.1f} PB votes vs matched expectation")
    if row["matched_relative_high_turnout_high_share"] == 1:
        parts.append("high turnout and high PB share vs controls")
    if row["regional_lead_score"] >= 2:
        parts.append(f"regional score {int(row['regional_lead_score'])}")
    if row["is_geo_clustered"] == 1:
        parts.append(f"geo cluster {int(row['geo_cluster_id'])}")
    if row["voting_method_lead_flag"] == 1 and row["voting_mode"] == "paper_only":
        parts.append("paper-only method lead")
    if row["historical_swing_lead"] == 1:
        parts.append("large 2026 swing vs exact 2024 section")
    if row["validation_issue_count"] > 0:
        parts.append(f"validation issue: {row['validation_issue_types']}")
    if not parts:
        return "no scored statistical or validation flag"
    return "; ".join(parts)


def category(score: int, row: pd.Series) -> tuple[int, str]:
    if score <= 0:
        return 0, "normal/no flag"
    if score <= 2:
        return 1, "mild statistical outlier"
    if score <= 4:
        return 2, "strong statistical lead"
    if row["validation_issue_count"] > 0 or row["is_geo_clustered"] == 1:
        if score >= 7 and row["pb_votes_minus_control_expectation"] >= 250:
            return 4, "priority manual review: high-impact clustered/admin lead"
        return 3, "statistical lead with corroborating flag"
    if score >= 7 and row["pb_votes_minus_control_expectation"] >= 250:
        return 4, "priority manual review: high-impact statistical lead"
    return 2, "strong statistical lead"


def score_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["score_matched_control"] = np.select(
        [out["matched_control_score"] >= 4, out["matched_control_score"] >= 2],
        [3, 2],
        default=0,
    )
    out["score_regional"] = (out["regional_lead_score"] >= 2).astype(int)
    out["score_positive_residual"] = (out["matched_positive_residual"] == 1).astype(int)
    out["score_relative_high_turnout_high_share"] = (out["matched_relative_high_turnout_high_share"] == 1).astype(int)
    out["score_geo_cluster"] = (out["is_geo_clustered"] == 1).astype(int)
    out["score_validation"] = (out["validation_issue_count"] > 0).astype(int)
    out["score_method"] = ((out["voting_method_lead_flag"] == 1) & (out["voting_mode"] == "paper_only")).astype(int)
    out["score_historical"] = (out["historical_swing_lead"] == 1).astype(int)
    out["score_high_impact"] = np.select(
        [out["pb_votes_minus_control_expectation"] >= 250, out["pb_votes_minus_control_expectation"] >= 100],
        [2, 1],
        default=0,
    )
    out["score_extreme_absolute"] = (out["absolute_high_turnout_high_share"] == 1).astype(int)
    score_columns = [
        "score_matched_control",
        "score_regional",
        "score_positive_residual",
        "score_relative_high_turnout_high_share",
        "score_geo_cluster",
        "score_validation",
        "score_method",
        "score_historical",
        "score_high_impact",
        "score_extreme_absolute",
    ]
    out["anomaly_score"] = out[score_columns].sum(axis=1).astype(int)
    cats = out.apply(lambda row: category(int(row["anomaly_score"]), row), axis=1)
    out["anomaly_category"] = [item[0] for item in cats]
    out["anomaly_category_label"] = [item[1] for item in cats]
    out["evidence_summary"] = out.apply(evidence_summary, axis=1)
    out["cik_search_url"] = out["section_id"].map(lambda section: f"{BASE_RESULTS_URL}/search/index.html#/s/64/{section}")
    out["candidate_protocol_html_url"] = out.apply(
        lambda row: f"{BASE_RESULTS_URL}/protokoli/64/{str(row['region_id']).zfill(2)}/{row['section_id']}.0.html", axis=1
    )
    out["candidate_protocol_pdf_search_url"] = out["section_id"].map(lambda section: f"{BASE_RESULTS_URL}/search/index.html#/s/64/{section}.0.pdf")
    return out.sort_values(
        ["anomaly_category", "anomaly_score", "pb_votes_minus_control_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )


def protocol_review_sample(scored: pd.DataFrame, limit: int) -> pd.DataFrame:
    candidates = scored[
        (scored["anomaly_category"] >= 2)
        | (scored["validation_issue_count"] > 0)
        | (scored["matched_positive_residual"] == 1)
        | (scored["is_geo_clustered"] == 1)
    ].copy()
    candidates["review_reason_rank"] = (
        candidates["validation_issue_count"].clip(upper=1) * 6
        + candidates["is_geo_clustered"].clip(upper=1) * 3
        + candidates["historical_swing_lead"].clip(upper=1) * 2
        + candidates["score_high_impact"]
        + candidates["score_matched_control"]
    )
    return candidates.sort_values(
        ["anomaly_category", "review_reason_rank", "anomaly_score", "pb_votes_minus_control_expectation"],
        ascending=False,
    ).head(limit)


def svg_score_distribution(scored: pd.DataFrame, path: Path) -> None:
    counts = scored["anomaly_category"].value_counts().sort_index()
    labels = {
        0: "0 normal",
        1: "1 mild",
        2: "2 strong stat",
        3: "3 corroborated",
        4: "4 priority",
    }
    rows = [{"category": labels.get(int(cat), str(cat)), "count": int(count)} for cat, count in counts.items()]
    width = 880
    height = 500
    margin_left = 86
    margin_right = 36
    margin_top = 54
    margin_bottom = 104
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_count = max(row["count"] for row in rows) if rows else 1

    def y_map(value: float) -> float:
        return margin_top + plot_h - value / max_count * plot_h

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">Anomaly Category Distribution</text>')
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    slot = plot_w / len(rows)
    bar_w = slot * 0.58
    palette = ["#94a3b8", "#60a5fa", "#f59e0b", "#ef4444", "#7c2d12"]
    for idx, row in enumerate(rows):
        x = margin_left + idx * slot + (slot - bar_w) / 2
        y = y_map(row["count"])
        color = palette[idx] if idx < len(palette) else "#64748b"
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{margin_top + plot_h - y:.2f}" fill="{color}"/>')
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{y - 7:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{row["count"]:,}</text>'
        )
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 62}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{html.escape(row["category"])}</text>'
        )
    for tick in np.linspace(0, max_count, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick:,.0f}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def markdown_rows(frame: pd.DataFrame, limit: int = 20) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |\n"
    rows = []
    columns = [
        "section_id",
        "region_id",
        "place_name",
        "voting_mode",
        "anomaly_category",
        "anomaly_score",
        "progressive_bulgaria_share",
        "pb_votes_minus_control_expectation",
        "evidence_summary",
    ]
    for _, row in frame.head(limit).iterrows():
        values = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                if "share" in column:
                    values.append(f"{value:.1%}")
                elif "expectation" in column:
                    values.append(f"{value:.1f}")
                else:
                    values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_document(docs_dir: Path, summary: dict[str, Any], scored: pd.DataFrame, sample: pd.DataFrame) -> None:
    top = scored[scored["anomaly_category"] >= 2].head(20)
    note = f"""# Anomaly Scoring and Protocol Review Sample

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/station_regional_residuals_2026.csv`
- `outputs/tables/matched_control_results_2026.csv`
- `outputs/tables/lead_geo_cluster_members_2026.csv`
- `outputs/tables/voting_method_lead_stations_2026.csv`
- `outputs/tables/historical_station_swing_2024_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/score_anomalies.py
```

## Generated Outputs

- `outputs/tables/anomaly_scores_2026.csv`
- `outputs/tables/suspicious_stations_2026.csv`
- `outputs/tables/protocol_review_sample_2026.csv`
- `outputs/tables/anomaly_score_summary_2026.json`
- `outputs/figures/anomaly_score_distribution_2026.svg`

## Summary

- Stations scored: `{summary["station_count"]:,}`
- Category 0, normal/no flag: `{summary["category_counts"].get("0", 0):,}`
- Category 1, mild statistical outlier: `{summary["category_counts"].get("1", 0):,}`
- Category 2, strong statistical lead: `{summary["category_counts"].get("2", 0):,}`
- Category 3, statistical lead with corroborating flag: `{summary["category_counts"].get("3", 0):,}`
- Category 4, priority manual review: `{summary["category_counts"].get("4", 0):,}`
- Historical swing lead stations: `{summary["historical_swing_lead_station_count"]:,}`
- Protocol review sample size: `{summary["protocol_review_sample_size"]:,}`

## Top Scored Stations

| Section | Region | Place | Method | Category | Score | PB share | PB votes above matched expectation | Evidence summary |
|---|---|---|---|---:|---:|---:|---:|---|
{markdown_rows(top)}

## Review Sample Method

The protocol review sample prioritizes stations with high anomaly categories, validation issues, coordinate-cluster membership, large matched-control residuals, and strong matched-control scores. The generated sample includes CIK search links plus candidate protocol HTML/PDF URLs for manual verification. The candidate protocol URLs should be treated as navigational aids because the CIK site may change routing or require browser interaction.

## Interpretation

The score is an auditable triage score, not a fraud label. The strongest statistical leads are places where multiple independent statistical indicators agree, especially when they are clustered or have protocol/validation flags. The score should now be used to guide manual protocol checks, complaint matching, and historical baseline review.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "anomaly_scoring_2026.md").write_text(note, encoding="utf-8")


def analyze(
    stations_csv: Path,
    matched_controls_csv: Path,
    regional_residuals_csv: Path,
    geo_members_csv: Path,
    station_leaders_csv: Path,
    validation_issues_csv: Path,
    voting_method_leads_csv: Path,
    historical_swing_csv: Path,
    tables_dir: Path,
    figures_dir: Path,
    docs_dir: Path,
    sample_size: int,
) -> None:
    base = build_base_frame(
        stations_csv,
        matched_controls_csv,
        regional_residuals_csv,
        geo_members_csv,
        station_leaders_csv,
        historical_swing_csv,
        validation_issues_csv,
        voting_method_leads_csv,
    )
    scored = score_frame(base)
    sample = protocol_review_sample(scored, sample_size)
    suspicious = scored[scored["anomaly_category"] >= 2].copy()

    output_columns = [
        "section_id",
        "region_id",
        "admin_name",
        "municipality_code",
        "place_name",
        "address",
        "latitude",
        "longitude",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "top_party_name",
        "top_party_share",
        "winner_margin",
        "turnout_2024",
        "top_party_name_2024",
        "top_party_share_2024",
        "ppdb_share_2024",
        "ppdb_plus_gerb_share_2024",
        "turnout_delta_2026_minus_2024",
        "pb_share_2026_minus_2024_top_party_share",
        "historical_swing_lead",
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
        "geo_cluster_id",
        "is_geo_clustered",
        "validation_issue_count",
        "validation_issue_types",
        "validation_issue_details",
        "voting_method_lead_flag",
        "score_matched_control",
        "score_regional",
        "score_positive_residual",
        "score_relative_high_turnout_high_share",
        "score_geo_cluster",
        "score_validation",
        "score_method",
        "score_historical",
        "score_high_impact",
        "score_extreme_absolute",
        "anomaly_score",
        "anomaly_category",
        "anomaly_category_label",
        "evidence_summary",
        "cik_search_url",
        "candidate_protocol_html_url",
        "candidate_protocol_pdf_search_url",
    ]
    output_columns = [column for column in output_columns if column in scored.columns]

    tables_dir.mkdir(parents=True, exist_ok=True)
    scored[output_columns].to_csv(tables_dir / "anomaly_scores_2026.csv", index=False)
    suspicious[output_columns].to_csv(tables_dir / "suspicious_stations_2026.csv", index=False)
    sample[output_columns].to_csv(tables_dir / "protocol_review_sample_2026.csv", index=False)
    svg_score_distribution(scored, figures_dir / "anomaly_score_distribution_2026.svg")

    category_counts = {str(int(key)): int(value) for key, value in scored["anomaly_category"].value_counts().sort_index().items()}
    summary = {
        "station_count": int(len(scored)),
        "category_counts": category_counts,
        "suspicious_station_count_category_gte_2": int(len(suspicious)),
        "protocol_review_sample_size": int(len(sample)),
        "max_anomaly_score": int(scored["anomaly_score"].max()),
        "validation_issue_station_count": int((scored["validation_issue_count"] > 0).sum()),
        "geo_clustered_station_count": int((scored["is_geo_clustered"] == 1).sum()),
        "historical_swing_lead_station_count": int((scored["historical_swing_lead"] == 1).sum()),
        "top_stations": scored.head(20)[output_columns].to_dict("records"),
        "outputs": {
            "scores": str(tables_dir / "anomaly_scores_2026.csv"),
            "suspicious": str(tables_dir / "suspicious_stations_2026.csv"),
            "protocol_review_sample": str(tables_dir / "protocol_review_sample_2026.csv"),
            "figure": str(figures_dir / "anomaly_score_distribution_2026.svg"),
        },
    }
    write_json(tables_dir / "anomaly_score_summary_2026.json", summary)
    write_document(docs_dir, summary, scored, sample)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations-csv", type=Path, default=Path("data/processed/cik_2026/polling_stations_2026.csv"))
    parser.add_argument("--matched-controls-csv", type=Path, default=Path("outputs/tables/matched_control_results_2026.csv"))
    parser.add_argument("--regional-residuals-csv", type=Path, default=Path("outputs/tables/station_regional_residuals_2026.csv"))
    parser.add_argument("--geo-members-csv", type=Path, default=Path("outputs/tables/lead_geo_cluster_members_2026.csv"))
    parser.add_argument("--station-leaders-csv", type=Path, default=Path("outputs/tables/station_party_leaders_2026.csv"))
    parser.add_argument("--voting-method-leads-csv", type=Path, default=Path("outputs/tables/voting_method_lead_stations_2026.csv"))
    parser.add_argument("--historical-swing-csv", type=Path, default=Path("outputs/tables/historical_station_swing_2024_2026.csv"))
    parser.add_argument("--validation-issues-csv", type=Path, default=Path("outputs/tables/validation_issues.csv"))
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument("--sample-size", type=int, default=150)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.stations_csv.resolve(),
        args.matched_controls_csv.resolve(),
        args.regional_residuals_csv.resolve(),
        args.geo_members_csv.resolve(),
        args.station_leaders_csv.resolve(),
        args.validation_issues_csv.resolve(),
        args.voting_method_leads_csv.resolve(),
        args.historical_swing_csv.resolve(),
        args.tables_dir.resolve(),
        args.figures_dir.resolve(),
        args.docs_dir.resolve(),
        args.sample_size,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
