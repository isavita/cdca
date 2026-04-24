#!/usr/bin/env python3
"""Cluster checks for matched-control Progressive Bulgaria leads."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


STRONG_LEAD_SCORE = 2
GEO_CLUSTER_EPS_KM = 5.0
GEO_CLUSTER_MIN_POINTS = 3


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or pd.isna(denominator):
        return None
    return float(numerator / denominator)


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
    shown = cleaned[:limit]
    return "; ".join(shown) + f"; (+{len(cleaned) - limit} more)"


def top_sections(group: pd.DataFrame, limit: int = 10) -> str:
    if group.empty:
        return ""
    ordered = group.sort_values(
        ["matched_control_score", "pb_votes_minus_control_expectation", "progressive_bulgaria_votes"],
        ascending=False,
    )
    return "; ".join(ordered["section_id"].head(limit).astype(str).tolist())


def parse_abroad_country(place_name: Any) -> str:
    text = "" if pd.isna(place_name) else str(place_name).strip()
    if "," not in text:
        return text
    return text.split(",", 1)[0].strip()


def parse_abroad_location(place_name: Any) -> str:
    text = "" if pd.isna(place_name) else str(place_name).strip()
    if "," not in text:
        return ""
    return text.split(",", 1)[1].strip()


def load_inputs(stations_csv: Path, matched_controls_csv: Path, validation_issues_csv: Path) -> pd.DataFrame:
    dtype = {
        "section_id": str,
        "region_id": str,
        "municipality_code": str,
        "admin_area_code": str,
        "precinct_code": str,
    }
    matched = pd.read_csv(matched_controls_csv, dtype=dtype)
    stations = pd.read_csv(stations_csv, dtype=dtype)

    station_cols = [
        "section_id",
        "admin_id",
        "admin_area_code",
        "precinct_code",
        "ekatte",
        "address",
        "longitude",
        "latitude",
        "is_abroad",
        "is_mobile",
        "is_ship",
        "machines_count",
    ]
    available_station_cols = [column for column in station_cols if column in stations.columns]
    df = matched.merge(stations[available_station_cols], on="section_id", how="left")

    for column in [
        "registered_voters",
        "voters_signed",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "control_count",
        "matched_positive_residual",
        "matched_relative_high_turnout_high_share",
        "regional_lead_score",
        "matched_control_score",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    for column in [
        "turnout",
        "progressive_bulgaria_share",
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
        "longitude",
        "latitude",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    if "abroad_country" not in df.columns:
        df["abroad_country"] = ""
    df["abroad_country"] = np.where(
        df["region_id"] == "32",
        df["place_name"].map(parse_abroad_country),
        df["abroad_country"].fillna(""),
    )
    df["abroad_location"] = np.where(df["region_id"] == "32", df["place_name"].map(parse_abroad_location), "")
    df["strong_matched_lead"] = (df["matched_control_score"] >= STRONG_LEAD_SCORE).astype(int)
    df["broad_matched_lead"] = (
        (df["strong_matched_lead"] == 1)
        | (df["matched_positive_residual"] == 1)
        | (df["matched_relative_high_turnout_high_share"] == 1)
    ).astype(int)
    df["positive_pb_residual"] = df["pb_votes_minus_control_expectation"].clip(lower=0)

    if validation_issues_csv.exists():
        issues = pd.read_csv(validation_issues_csv, dtype={"section_id": str})
        issue_counts = issues.groupby("section_id").size()
        issue_types = issues.groupby("section_id")["issue_type"].apply(lambda s: unique_join(s, limit=4))
        df["validation_issue_count"] = df["section_id"].map(issue_counts).fillna(0).astype(int)
        df["validation_issue_types"] = df["section_id"].map(issue_types).fillna("")
    else:
        df["validation_issue_count"] = 0
        df["validation_issue_types"] = ""

    return df


def group_key_to_dict(key: Any, columns: list[str]) -> dict[str, Any]:
    values = key if isinstance(key, tuple) else (key,)
    out: dict[str, Any] = {}
    for column, value in zip(columns, values, strict=False):
        out[column] = "" if pd.isna(value) else value
    return out


def aggregate_group_rows(df: pd.DataFrame, by_columns: list[str], group_level: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for key, group in df.groupby(by_columns, dropna=False):
        strong = group[group["strong_matched_lead"] == 1]
        if strong.empty:
            continue
        broad = group[group["broad_matched_lead"] == 1]
        valid_votes = float(group["total_valid_candidate_votes"].sum())
        pb_votes = float(group["progressive_bulgaria_votes"].sum())
        registered = float(group["registered_voters"].sum())
        signed = float(group["voters_signed"].sum())
        strong_valid_votes = float(strong["total_valid_candidate_votes"].sum())
        strong_pb_votes = float(strong["progressive_bulgaria_votes"].sum())
        row = {
            "group_level": group_level,
            **group_key_to_dict(key, by_columns),
            "station_count": int(len(group)),
            "broad_matched_lead_stations": int(group["broad_matched_lead"].sum()),
            "strong_matched_lead_stations": int(group["strong_matched_lead"].sum()),
            "strong_lead_station_rate": safe_divide(float(group["strong_matched_lead"].sum()), float(len(group))),
            "registered_voters": int(registered),
            "voters_signed": int(signed),
            "turnout": safe_divide(signed, registered),
            "valid_candidate_votes": int(valid_votes),
            "progressive_bulgaria_votes": int(pb_votes),
            "progressive_bulgaria_share": safe_divide(pb_votes, valid_votes),
            "strong_lead_valid_candidate_votes": int(strong_valid_votes),
            "strong_lead_progressive_bulgaria_votes": int(strong_pb_votes),
            "strong_lead_progressive_bulgaria_share": safe_divide(strong_pb_votes, strong_valid_votes),
            "strong_lead_valid_vote_share_of_group": safe_divide(strong_valid_votes, valid_votes),
            "strong_lead_pb_votes_minus_control_expectation": float(strong["pb_votes_minus_control_expectation"].sum(skipna=True)),
            "broad_lead_pb_votes_minus_control_expectation": float(broad["pb_votes_minus_control_expectation"].sum(skipna=True)),
            "matched_positive_residual_stations": int(group["matched_positive_residual"].sum()),
            "matched_relative_high_turnout_high_share_stations": int(group["matched_relative_high_turnout_high_share"].sum()),
            "validation_issue_stations": int((group["validation_issue_count"] > 0).sum()),
            "strong_lead_validation_issue_stations": int((strong["validation_issue_count"] > 0).sum()),
            "max_matched_control_score": int(strong["matched_control_score"].max()),
            "max_pb_control_z": clean(strong["pb_control_z"].max()),
            "max_pb_share_minus_control": clean(strong["pb_share_minus_control"].max()),
            "max_turnout_minus_control": clean(strong["turnout_minus_control"].max()),
            "strong_lead_sections": top_sections(strong),
            "strong_lead_places": unique_join(strong["place_name"], limit=10),
            "voting_modes_in_strong_leads": unique_join(strong["voting_mode"], limit=5),
            "validation_issue_types": unique_join(strong.loc[strong["validation_issue_count"] > 0, "validation_issue_types"], limit=5),
            "strong_lead_centroid_latitude": clean(strong["latitude"].mean()) if "latitude" in strong.columns else None,
            "strong_lead_centroid_longitude": clean(strong["longitude"].mean()) if "longitude" in strong.columns else None,
        }
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    sort_columns = [
        "strong_matched_lead_stations",
        "strong_lead_pb_votes_minus_control_expectation",
        "strong_lead_valid_candidate_votes",
        "max_matched_control_score",
    ]
    return out.sort_values(sort_columns, ascending=False).reset_index(drop=True)


def add_group_labels(municipality: pd.DataFrame, settlement: pd.DataFrame, abroad: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not municipality.empty:
        municipality["group_label"] = municipality["region_id"].astype(str) + "/" + municipality["municipality_code"].astype(str)
    if not settlement.empty:
        settlement["group_label"] = (
            settlement["region_id"].astype(str)
            + "/"
            + settlement["municipality_code"].astype(str)
            + " "
            + settlement["place_name"].astype(str)
        )
    if not abroad.empty:
        labels = []
        for _, row in abroad.iterrows():
            if row["group_level"] == "abroad_country":
                labels.append(str(row["abroad_country"]))
            else:
                labels.append(f"{row['abroad_country']} / {row['place_name']}")
        abroad["group_label"] = labels
    return municipality, settlement, abroad


def haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + math.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * radius_km * np.arcsin(np.sqrt(a))


def dbscan_haversine(points: pd.DataFrame, eps_km: float, min_points: int) -> np.ndarray:
    n = len(points)
    if n == 0:
        return np.array([], dtype=int)
    latitudes = points["latitude"].to_numpy(dtype=float)
    longitudes = points["longitude"].to_numpy(dtype=float)
    labels = np.full(n, -2, dtype=int)
    visited = np.zeros(n, dtype=bool)
    neighbor_cache: dict[int, list[int]] = {}

    def neighbors(idx: int) -> list[int]:
        if idx not in neighbor_cache:
            distances = haversine_km(latitudes[idx], longitudes[idx], latitudes, longitudes)
            neighbor_cache[idx] = np.where(distances <= eps_km)[0].astype(int).tolist()
        return neighbor_cache[idx]

    cluster_id = 0
    for idx in range(n):
        if visited[idx]:
            continue
        visited[idx] = True
        idx_neighbors = neighbors(idx)
        if len(idx_neighbors) < min_points:
            labels[idx] = -1
            continue

        labels[idx] = cluster_id
        seeds = list(idx_neighbors)
        seed_set = set(seeds)
        cursor = 0
        while cursor < len(seeds):
            point_idx = seeds[cursor]
            if not visited[point_idx]:
                visited[point_idx] = True
                point_neighbors = neighbors(point_idx)
                if len(point_neighbors) >= min_points:
                    for neighbor_idx in point_neighbors:
                        if neighbor_idx not in seed_set:
                            seeds.append(neighbor_idx)
                            seed_set.add(neighbor_idx)
            if labels[point_idx] in (-2, -1):
                labels[point_idx] = cluster_id
            cursor += 1
        cluster_id += 1

    labels[labels == -2] = -1
    return labels


def make_geo_clusters(df: pd.DataFrame, eps_km: float, min_points: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    strong_domestic = df[
        (df["region_id"] != "32")
        & (df["strong_matched_lead"] == 1)
        & df["latitude"].notna()
        & df["longitude"].notna()
    ].copy()
    strong_domestic = strong_domestic.sort_values(["region_id", "municipality_code", "section_id"]).reset_index(drop=True)
    labels = dbscan_haversine(strong_domestic, eps_km=eps_km, min_points=min_points)
    if len(strong_domestic):
        strong_domestic["geo_cluster_id"] = labels + 1
        strong_domestic.loc[labels < 0, "geo_cluster_id"] = 0
        strong_domestic["is_geo_clustered"] = (labels >= 0).astype(int)
    else:
        strong_domestic["geo_cluster_id"] = pd.Series(dtype=int)
        strong_domestic["is_geo_clustered"] = pd.Series(dtype=int)

    cluster_rows: list[dict[str, Any]] = []
    clustered = strong_domestic[strong_domestic["is_geo_clustered"] == 1]
    for cluster_id, group in clustered.groupby("geo_cluster_id"):
        center_lat = float(group["latitude"].mean())
        center_lon = float(group["longitude"].mean())
        distances = haversine_km(center_lat, center_lon, group["latitude"].to_numpy(dtype=float), group["longitude"].to_numpy(dtype=float))
        valid_votes = float(group["total_valid_candidate_votes"].sum())
        pb_votes = float(group["progressive_bulgaria_votes"].sum())
        cluster_rows.append(
            {
                "geo_cluster_id": int(cluster_id),
                "eps_km": eps_km,
                "min_points": min_points,
                "strong_matched_lead_stations": int(len(group)),
                "center_latitude": center_lat,
                "center_longitude": center_lon,
                "max_distance_from_center_km": float(distances.max()) if len(distances) else 0.0,
                "region_ids": unique_join(group["region_id"], limit=8),
                "municipality_codes": unique_join(group["municipality_code"], limit=10),
                "places": unique_join(group["place_name"], limit=12),
                "valid_candidate_votes": int(valid_votes),
                "progressive_bulgaria_votes": int(pb_votes),
                "progressive_bulgaria_share": safe_divide(pb_votes, valid_votes),
                "pb_votes_minus_control_expectation": float(group["pb_votes_minus_control_expectation"].sum(skipna=True)),
                "matched_positive_residual_stations": int(group["matched_positive_residual"].sum()),
                "matched_relative_high_turnout_high_share_stations": int(group["matched_relative_high_turnout_high_share"].sum()),
                "validation_issue_stations": int((group["validation_issue_count"] > 0).sum()),
                "max_matched_control_score": int(group["matched_control_score"].max()),
                "section_ids": top_sections(group, limit=20),
            }
        )
    clusters = pd.DataFrame(cluster_rows)
    if not clusters.empty:
        clusters = clusters.sort_values(
            ["strong_matched_lead_stations", "pb_votes_minus_control_expectation", "valid_candidate_votes"],
            ascending=False,
        ).reset_index(drop=True)
    member_cols = [
        "section_id",
        "geo_cluster_id",
        "is_geo_clustered",
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
        "control_weighted_pb_share",
        "pb_share_minus_control",
        "turnout_minus_control",
        "pb_votes_minus_control_expectation",
        "pb_control_z",
        "matched_control_score",
        "validation_issue_count",
        "validation_issue_types",
    ]
    return clusters, strong_domestic[[column for column in member_cols if column in strong_domestic.columns]]


def svg_bar_chart(rows: list[dict[str, Any]], path: Path, title: str, value_key: str, label_key: str) -> None:
    width = 1180
    height = 620
    margin_left = 72
    margin_right = 40
    margin_top = 52
    margin_bottom = 126
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    if not rows:
        return
    max_value = max(float(row[value_key]) for row in rows)
    if max_value <= 0:
        max_value = 1.0

    def y_map(value: float) -> float:
        return margin_top + plot_h - value / max_value * plot_h

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">{html.escape(title)}</text>')
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    bar_slot = plot_w / len(rows)
    bar_w = bar_slot * 0.68
    for i, row in enumerate(rows):
        value = float(row[value_key])
        x = margin_left + i * bar_slot + (bar_slot - bar_w) / 2
        y = y_map(value)
        bar_h = plot_h - (y - margin_top)
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="#0f766e"/>')
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{int(value)}</text>'
        )
        label = str(row[label_key])
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 76}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" transform="rotate(-45 {x + bar_w / 2:.2f} {height - 76})">{html.escape(label)}</text>'
        )

    for tick in np.linspace(0, max_value, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick:.0f}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def markdown_cluster_rows(frame: pd.DataFrame, label_column: str, limit: int = 12) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |  |  |  |\n"
    lines = []
    for _, row in frame.head(limit).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row[label_column]),
                    f"{int(row['station_count']):,}",
                    f"{int(row['strong_matched_lead_stations']):,}",
                    f"{row['strong_lead_station_rate']:.1%}" if pd.notna(row["strong_lead_station_rate"]) else "",
                    f"{row['strong_lead_pb_votes_minus_control_expectation']:.1f}",
                    str(int(row["max_matched_control_score"])),
                    str(int(row["strong_lead_validation_issue_stations"])),
                    str(row["strong_lead_sections"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def markdown_geo_rows(frame: pd.DataFrame, limit: int = 12) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |  |  |  |\n"
    lines = []
    for _, row in frame.head(limit).iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["geo_cluster_id"])),
                    str(int(row["strong_matched_lead_stations"])),
                    str(row["region_ids"]),
                    str(row["places"]),
                    f"{row['pb_votes_minus_control_expectation']:.1f}",
                    str(int(row["max_matched_control_score"])),
                    str(row["section_ids"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def write_document(
    docs_dir: Path,
    summary: dict[str, Any],
    municipality: pd.DataFrame,
    settlement: pd.DataFrame,
    abroad: pd.DataFrame,
    geo_clusters: pd.DataFrame,
) -> None:
    country = abroad[abroad["group_level"] == "abroad_country"] if not abroad.empty else pd.DataFrame()
    abroad_place = abroad[abroad["group_level"] == "abroad_place"] if not abroad.empty else pd.DataFrame()
    note = f"""# Lead Clusters

## Inputs

- `outputs/tables/matched_control_results_2026.csv`
- `data/processed/cik_2026/polling_stations_2026.csv`
- `outputs/tables/validation_issues.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_lead_clusters.py
```

## Generated Outputs

- `outputs/tables/lead_cluster_municipality_2026.csv`
- `outputs/tables/lead_cluster_settlement_2026.csv`
- `outputs/tables/lead_cluster_abroad_2026.csv`
- `outputs/tables/lead_geo_clusters_2026.csv`
- `outputs/tables/lead_geo_cluster_members_2026.csv`
- `outputs/tables/lead_cluster_summary_2026.json`
- `outputs/figures/lead_clusters_by_municipality_2026.svg`

## Method

The primary lead definition is `matched_control_score >= {STRONG_LEAD_SCORE}` from the matched-control step. This script aggregates those stations by municipality code, settlement, abroad country/place, and a simple DBSCAN-style domestic coordinate cluster. The coordinate cluster uses a {GEO_CLUSTER_EPS_KM:g} km radius and requires at least {GEO_CLUSTER_MIN_POINTS} strong-lead stations.

These are follow-up leads, not fraud findings. A coherent cluster is more useful than an isolated station, but it still needs corroboration from protocol scans, complaints, local context, voting-method changes, or historical baselines.

## Summary

- Stations checked: `{summary["station_count"]:,}`
- Strong matched-control leads: `{summary["strong_matched_leads"]:,}`
- Municipalities with at least one strong lead: `{summary["municipality_groups_with_strong_leads"]:,}`
- Settlements with at least one strong lead: `{summary["settlement_groups_with_strong_leads"]:,}`
- Abroad country/place groups with at least one strong lead: `{summary["abroad_groups_with_strong_leads"]:,}`
- Domestic strong leads with usable coordinates: `{summary["domestic_strong_leads_with_coordinates"]:,}`
- Coordinate clusters found: `{summary["geo_cluster_count"]:,}`
- Domestic strong leads inside coordinate clusters: `{summary["geo_clustered_strong_leads"]:,}`
- Domestic strong leads treated as coordinate noise/isolated: `{summary["geo_noise_strong_leads"]:,}`

## Top Municipality Concentrations

| Municipality | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
{markdown_cluster_rows(municipality, "group_label")}

## Top Settlement Concentrations

| Settlement | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
{markdown_cluster_rows(settlement, "group_label")}

## Abroad Country Concentrations

| Abroad country | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
{markdown_cluster_rows(country, "group_label")}

## Abroad Place Concentrations

| Abroad place | Stations | Strong leads | Rate | PB votes above matched expectation | Max score | Strong leads with validation issues | Sections |
|---|---:|---:|---:|---:|---:|---:|---|
{markdown_cluster_rows(abroad_place, "group_label")}

## Coordinate Clusters

| Cluster | Strong leads | Regions | Places | PB votes above matched expectation | Max score | Sections |
|---:|---:|---|---|---:|---:|---|
{markdown_geo_rows(geo_clusters)}

## Initial Interpretation

The local-cluster view separates broad concentration from isolated station outliers. Groups with several strong matched-control leads should be prioritized for manual protocol and complaint review, especially where multiple nearby stations share the same pattern. Groups with a single strong station remain useful leads, but are weaker statistical evidence unless corroborated by another independent signal.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "lead_clusters_2026.md").write_text(note, encoding="utf-8")


def analyze(
    stations_csv: Path,
    matched_controls_csv: Path,
    validation_issues_csv: Path,
    tables_dir: Path,
    figures_dir: Path,
    docs_dir: Path,
) -> None:
    df = load_inputs(stations_csv, matched_controls_csv, validation_issues_csv)

    domestic = df[df["region_id"] != "32"].copy()
    abroad = df[df["region_id"] == "32"].copy()

    municipality = aggregate_group_rows(domestic, ["region_id", "admin_name", "municipality_code"], "municipality")
    settlement = aggregate_group_rows(domestic, ["region_id", "admin_name", "municipality_code", "place_name"], "settlement")
    abroad_country = aggregate_group_rows(abroad, ["abroad_country"], "abroad_country")
    abroad_place = aggregate_group_rows(abroad, ["abroad_country", "place_name"], "abroad_place")
    abroad_clusters = pd.concat([abroad_country, abroad_place], ignore_index=True) if not abroad_country.empty or not abroad_place.empty else pd.DataFrame()
    municipality, settlement, abroad_clusters = add_group_labels(municipality, settlement, abroad_clusters)

    geo_clusters, geo_members = make_geo_clusters(df, eps_km=GEO_CLUSTER_EPS_KM, min_points=GEO_CLUSTER_MIN_POINTS)

    tables_dir.mkdir(parents=True, exist_ok=True)
    municipality.to_csv(tables_dir / "lead_cluster_municipality_2026.csv", index=False)
    settlement.to_csv(tables_dir / "lead_cluster_settlement_2026.csv", index=False)
    abroad_clusters.to_csv(tables_dir / "lead_cluster_abroad_2026.csv", index=False)
    geo_clusters.to_csv(tables_dir / "lead_geo_clusters_2026.csv", index=False)
    geo_members.to_csv(tables_dir / "lead_geo_cluster_members_2026.csv", index=False)

    top_municipality_rows = municipality.head(24).to_dict("records") if not municipality.empty else []
    svg_bar_chart(
        top_municipality_rows,
        figures_dir / "lead_clusters_by_municipality_2026.svg",
        "Strong Matched-Control Leads by Municipality",
        "strong_matched_lead_stations",
        "group_label",
    )

    summary = {
        "station_count": int(len(df)),
        "strong_matched_leads": int(df["strong_matched_lead"].sum()),
        "broad_matched_leads": int(df["broad_matched_lead"].sum()),
        "domestic_strong_leads": int(domestic["strong_matched_lead"].sum()),
        "abroad_strong_leads": int(abroad["strong_matched_lead"].sum()),
        "municipality_groups_with_strong_leads": int(len(municipality)),
        "settlement_groups_with_strong_leads": int(len(settlement)),
        "abroad_groups_with_strong_leads": int(len(abroad_clusters)),
        "domestic_strong_leads_with_coordinates": int(len(geo_members)),
        "geo_eps_km": GEO_CLUSTER_EPS_KM,
        "geo_min_points": GEO_CLUSTER_MIN_POINTS,
        "geo_cluster_count": int(len(geo_clusters)),
        "geo_clustered_strong_leads": int(geo_members["is_geo_clustered"].sum()) if not geo_members.empty else 0,
        "geo_noise_strong_leads": int((geo_members["is_geo_clustered"] == 0).sum()) if not geo_members.empty else 0,
        "strong_lead_validation_issue_stations": int(((df["strong_matched_lead"] == 1) & (df["validation_issue_count"] > 0)).sum()),
        "top_municipality_groups": municipality.head(10).to_dict("records") if not municipality.empty else [],
        "top_settlement_groups": settlement.head(10).to_dict("records") if not settlement.empty else [],
        "top_geo_clusters": geo_clusters.head(10).to_dict("records") if not geo_clusters.empty else [],
        "outputs": {
            "municipality": str(tables_dir / "lead_cluster_municipality_2026.csv"),
            "settlement": str(tables_dir / "lead_cluster_settlement_2026.csv"),
            "abroad": str(tables_dir / "lead_cluster_abroad_2026.csv"),
            "geo_clusters": str(tables_dir / "lead_geo_clusters_2026.csv"),
            "geo_members": str(tables_dir / "lead_geo_cluster_members_2026.csv"),
            "figure": str(figures_dir / "lead_clusters_by_municipality_2026.svg"),
        },
    }
    write_json(tables_dir / "lead_cluster_summary_2026.json", summary)
    write_document(docs_dir, summary, municipality, settlement, abroad_clusters, geo_clusters)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stations-csv",
        type=Path,
        default=Path("data/processed/cik_2026/polling_stations_2026.csv"),
        help="Processed station-level CSV.",
    )
    parser.add_argument(
        "--matched-controls-csv",
        type=Path,
        default=Path("outputs/tables/matched_control_results_2026.csv"),
        help="Matched-control station results.",
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
