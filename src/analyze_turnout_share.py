#!/usr/bin/env python3
"""Analyze turnout vs Progressive Bulgaria vote share at polling-station level."""

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


PLOT_WIDTH = 980
PLOT_HEIGHT = 660
MARGIN_LEFT = 80
MARGIN_RIGHT = 40
MARGIN_TOP = 42
MARGIN_BOTTOM = 72


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


def weighted_mean(values: pd.Series, weights: pd.Series) -> float | None:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    return float(np.average(values[mask], weights=weights[mask]))


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


def pearson_corr(x: pd.Series, y: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    return float(np.corrcoef(x[mask].to_numpy(dtype=float), y[mask].to_numpy(dtype=float))[0, 1])


def spearman_corr(x: pd.Series, y: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return None
    return pearson_corr(x[mask].rank(method="average"), y[mask].rank(method="average"))


def weighted_slope(x: pd.Series, y: pd.Series, weights: pd.Series) -> float | None:
    mask = x.notna() & y.notna() & weights.notna() & (weights > 0)
    if mask.sum() < 3:
        return None
    xv = x[mask].to_numpy(dtype=float)
    yv = y[mask].to_numpy(dtype=float)
    w = weights[mask].to_numpy(dtype=float)
    x_mean = np.average(xv, weights=w)
    y_mean = np.average(yv, weights=w)
    denominator = np.sum(w * (xv - x_mean) ** 2)
    if denominator <= 0:
        return None
    return float(np.sum(w * (xv - x_mean) * (yv - y_mean)) / denominator)


def summarize_group(df: pd.DataFrame, label: str) -> dict[str, Any]:
    valid_votes = int(df["total_valid_candidate_votes"].sum())
    pb_votes = int(df["progressive_bulgaria_votes"].sum())
    registered = int(df["registered_voters"].sum())
    voters_signed = int(df["voters_signed"].sum())
    return {
        "group": label,
        "station_count": int(len(df)),
        "registered_voters": registered,
        "voters_signed": voters_signed,
        "valid_candidate_votes": valid_votes,
        "progressive_bulgaria_votes": pb_votes,
        "turnout_signed_over_registered": voters_signed / registered if registered else None,
        "progressive_bulgaria_share": pb_votes / valid_votes if valid_votes else None,
        "station_turnout_mean": clean_float(df["turnout"].mean()),
        "station_turnout_median": clean_float(df["turnout"].median()),
        "station_pb_share_mean": clean_float(df["progressive_bulgaria_share"].mean()),
        "station_pb_share_median": clean_float(df["progressive_bulgaria_share"].median()),
        "pearson_turnout_pb_share": pearson_corr(df["turnout"], df["progressive_bulgaria_share"]),
        "spearman_turnout_pb_share": spearman_corr(df["turnout"], df["progressive_bulgaria_share"]),
        "weighted_corr_by_valid_votes": weighted_corr(
            df["turnout"], df["progressive_bulgaria_share"], df["total_valid_candidate_votes"]
        ),
        "weighted_slope_pb_share_per_turnout_point": weighted_slope(
            df["turnout"], df["progressive_bulgaria_share"], df["total_valid_candidate_votes"]
        ),
    }


def make_group_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    groups = [summarize_group(df, "all")]
    groups.append(summarize_group(df[df["is_abroad"] == 0], "domestic"))
    groups.append(summarize_group(df[df["is_abroad"] == 1], "abroad"))
    for voting_mode, group in sorted(df.groupby("voting_mode"), key=lambda item: item[0]):
        groups.append(summarize_group(group, f"voting_mode:{voting_mode}"))
    return groups


def make_region_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for region_id, group in sorted(df.groupby("region_id"), key=lambda item: item[0]):
        row = summarize_group(group, f"region:{region_id}")
        row["region_id"] = region_id
        row["region_name"] = str(group["admin_name"].iloc[0])
        rows.append(row)
    return rows


def make_turnout_bins(df: pd.DataFrame) -> list[dict[str, Any]]:
    bins = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0000001]
    labels = ["0-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    work = df.copy()
    work["turnout_bin"] = pd.cut(work["turnout"], bins=bins, labels=labels, include_lowest=True, right=False)
    rows = []
    for label, group in work.groupby("turnout_bin", observed=False):
        if len(group) == 0:
            continue
        valid_votes = int(group["total_valid_candidate_votes"].sum())
        pb_votes = int(group["progressive_bulgaria_votes"].sum())
        registered = int(group["registered_voters"].sum())
        voters_signed = int(group["voters_signed"].sum())
        rows.append(
            {
                "turnout_bin": str(label),
                "station_count": int(len(group)),
                "registered_voters": registered,
                "voters_signed": voters_signed,
                "valid_candidate_votes": valid_votes,
                "progressive_bulgaria_votes": pb_votes,
                "turnout_signed_over_registered": voters_signed / registered if registered else None,
                "progressive_bulgaria_share": pb_votes / valid_votes if valid_votes else None,
                "station_pb_share_median": clean_float(group["progressive_bulgaria_share"].median()),
            }
        )
    return rows


def make_high_turnout_high_share_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    candidates = df[
        (df["turnout"] >= 0.80)
        & (df["progressive_bulgaria_share"] >= 0.70)
        & (df["total_valid_candidate_votes"] >= 50)
    ].copy()
    candidates["impact_votes_above_national_share"] = (
        candidates["progressive_bulgaria_votes"] - 0.4459414917059549 * candidates["total_valid_candidate_votes"]
    )
    candidates = candidates.sort_values(["impact_votes_above_national_share", "progressive_bulgaria_votes"], ascending=False)
    fields = [
        "section_id",
        "region_id",
        "admin_name",
        "place_name",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
        "impact_votes_above_national_share",
    ]
    return [{field: clean_float(row[field]) for field in fields} for _, row in candidates.iterrows()]


def make_extreme_turnout_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    candidates = df[(df["turnout"] >= 0.95) | (df["turnout"] <= 0.05)].copy()
    candidates = candidates.sort_values(["turnout", "total_valid_candidate_votes"], ascending=[False, False])
    fields = [
        "section_id",
        "region_id",
        "admin_name",
        "place_name",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
        "progressive_bulgaria_votes",
        "progressive_bulgaria_share",
    ]
    return [{field: clean_float(row[field]) for field in fields} for _, row in candidates.iterrows()]


def map_x(value: float, min_value: float, max_value: float) -> float:
    plot_w = PLOT_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    return MARGIN_LEFT + (value - min_value) / (max_value - min_value) * plot_w


def map_y(value: float, min_value: float, max_value: float) -> float:
    plot_h = PLOT_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    return PLOT_HEIGHT - MARGIN_BOTTOM - (value - min_value) / (max_value - min_value) * plot_h


def make_heatmap_svg(
    df: pd.DataFrame,
    path: Path,
    title: str,
    subtitle: str,
    x_col: str = "turnout",
    y_col: str = "progressive_bulgaria_share",
    bins: int = 48,
) -> None:
    work = df[[x_col, y_col, "total_valid_candidate_votes"]].dropna()
    x = work[x_col].to_numpy(dtype=float)
    y = work[y_col].to_numpy(dtype=float)
    hist, x_edges, y_edges = np.histogram2d(x, y, bins=bins, range=[[0, 1], [0, 1]])
    max_count = hist.max() if hist.size else 0

    elements: list[str] = []
    elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PLOT_WIDTH}" height="{PLOT_HEIGHT}" viewBox="0 0 {PLOT_WIDTH} {PLOT_HEIGHT}">')
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(f'<text x="{MARGIN_LEFT}" y="24" font-family="Arial, sans-serif" font-size="20" font-weight="700">{html.escape(title)}</text>')
    elements.append(f'<text x="{MARGIN_LEFT}" y="46" font-family="Arial, sans-serif" font-size="13" fill="#4b5563">{html.escape(subtitle)}</text>')

    plot_x = MARGIN_LEFT
    plot_y = MARGIN_TOP
    plot_w = PLOT_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    plot_h = PLOT_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    elements.append(f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')

    for i in range(bins):
        for j in range(bins):
            count = hist[i, j]
            if count <= 0:
                continue
            opacity = 0.14 + 0.76 * math.log1p(count) / math.log1p(max_count)
            x0 = map_x(x_edges[i], 0, 1)
            x1 = map_x(x_edges[i + 1], 0, 1)
            y0 = map_y(y_edges[j], 0, 1)
            y1 = map_y(y_edges[j + 1], 0, 1)
            rect_y = min(y0, y1)
            rect_h = abs(y1 - y0)
            elements.append(
                f'<rect x="{x0:.2f}" y="{rect_y:.2f}" width="{(x1 - x0):.2f}" height="{rect_h:.2f}" fill="#2563eb" opacity="{opacity:.3f}"/>'
            )

    # Weighted average line by turnout bin.
    line_points = []
    bin_edges = np.linspace(0, 1, 21)
    for start, end in zip(bin_edges[:-1], bin_edges[1:]):
        bin_group = work[(work[x_col] >= start) & (work[x_col] < end if end < 1 else work[x_col] <= end)]
        if len(bin_group) == 0:
            continue
        y_mean = weighted_mean(bin_group[y_col], bin_group["total_valid_candidate_votes"])
        if y_mean is None:
            continue
        x_mid = (start + end) / 2
        line_points.append(f"{map_x(x_mid, 0, 1):.2f},{map_y(y_mean, 0, 1):.2f}")
    if len(line_points) >= 2:
        elements.append(
            f'<polyline points="{" ".join(line_points)}" fill="none" stroke="#dc2626" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
        )

    # Grid and axes.
    for tick in np.linspace(0, 1, 6):
        x_tick = map_x(float(tick), 0, 1)
        y_tick = map_y(float(tick), 0, 1)
        elements.append(f'<line x1="{x_tick:.2f}" y1="{plot_y}" x2="{x_tick:.2f}" y2="{plot_y + plot_h}" stroke="#e2e8f0"/>')
        elements.append(f'<line x1="{plot_x}" y1="{y_tick:.2f}" x2="{plot_x + plot_w}" y2="{y_tick:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{x_tick:.2f}" y="{PLOT_HEIGHT - 42}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{int(tick * 100)}%</text>')
        elements.append(f'<text x="{MARGIN_LEFT - 12}" y="{y_tick + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{int(tick * 100)}%</text>')

    elements.append(f'<text x="{MARGIN_LEFT + plot_w / 2:.2f}" y="{PLOT_HEIGHT - 14}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">Turnout</text>')
    elements.append(
        f'<text x="22" y="{MARGIN_TOP + plot_h / 2:.2f}" text-anchor="middle" transform="rotate(-90 22 {MARGIN_TOP + plot_h / 2:.2f})" font-family="Arial, sans-serif" font-size="14">Progressive Bulgaria vote share</text>'
    )
    elements.append(f'<text x="{PLOT_WIDTH - MARGIN_RIGHT - 8}" y="{MARGIN_TOP + 20}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#dc2626">red line = weighted mean by turnout bin</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def make_bar_svg(rows: list[dict[str, Any]], path: Path, title: str) -> None:
    width = 980
    height = 560
    margin_left = 92
    margin_right = 36
    margin_top = 44
    margin_bottom = 86
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_share = max(row["progressive_bulgaria_share"] for row in rows if row["progressive_bulgaria_share"] is not None)

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(f'<text x="{margin_left}" y="28" font-family="Arial, sans-serif" font-size="20" font-weight="700">{html.escape(title)}</text>')
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    bar_w = plot_w / len(rows) * 0.7
    for i, row in enumerate(rows):
        share = row["progressive_bulgaria_share"]
        x = margin_left + (i + 0.15) * plot_w / len(rows)
        bar_h = share / max_share * plot_h if max_share else 0
        y = margin_top + plot_h - bar_h
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="#2563eb"/>')
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 52}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" transform="rotate(-35 {x + bar_w / 2:.2f} {height - 52})">{html.escape(row["turnout_bin"])}</text>'
        )
        elements.append(f'<text x="{x + bar_w / 2:.2f}" y="{y - 6:.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{share * 100:.1f}%</text>')

    for tick in np.linspace(0, max_share, 5):
        y = margin_top + plot_h - (tick / max_share * plot_h if max_share else 0)
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{margin_left - 12}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick * 100:.0f}%</text>')

    elements.append(f'<text x="{margin_left + plot_w / 2:.2f}" y="{height - 16}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14">Turnout bin</text>')
    elements.append(
        f'<text x="24" y="{margin_top + plot_h / 2:.2f}" text-anchor="middle" transform="rotate(-90 24 {margin_top + plot_h / 2:.2f})" font-family="Arial, sans-serif" font-size="14">Progressive Bulgaria share</text>'
    )
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def analyze(input_csv: Path, tables_dir: Path, figures_dir: Path, docs_dir: Path) -> None:
    df = pd.read_csv(
        input_csv,
        dtype={"section_id": str, "region_id": str, "municipality_code": str, "admin_area_code": str, "precinct_code": str},
    )
    df = df[(df["registered_voters"] > 0) & (df["total_valid_candidate_votes"] > 0)].copy()

    group_summary = make_group_summary(df)
    region_summary = make_region_summary(df)
    turnout_bins = make_turnout_bins(df)
    high_turnout_high_share = make_high_turnout_high_share_table(df)
    extreme_turnout = make_extreme_turnout_table(df)
    high_scope_counts = (
        pd.DataFrame(high_turnout_high_share)
        .assign(scope=lambda frame: np.where(frame["region_id"].astype(str) == "32", "abroad", "domestic"))
        .groupby("scope", as_index=False)
        .agg(
            station_count=("section_id", "count"),
            valid_candidate_votes=("total_valid_candidate_votes", "sum"),
            progressive_bulgaria_votes=("progressive_bulgaria_votes", "sum"),
        )
        .to_dict("records")
        if high_turnout_high_share
        else []
    )
    extreme_scope_counts = (
        pd.DataFrame(extreme_turnout)
        .assign(
            scope=lambda frame: np.where(frame["region_id"].astype(str) == "32", "abroad", "domestic"),
            turnout_bucket=lambda frame: np.where(frame["turnout"] >= 0.95, ">=95%", "<=5%"),
        )
        .groupby(["turnout_bucket", "scope"], as_index=False)
        .agg(station_count=("section_id", "count"))
        .to_dict("records")
        if extreme_turnout
        else []
    )
    top_positive_regions = sorted(
        region_summary,
        key=lambda row: row["weighted_corr_by_valid_votes"] if row["weighted_corr_by_valid_votes"] is not None else -999,
        reverse=True,
    )[:8]
    top_negative_regions = sorted(
        region_summary,
        key=lambda row: row["weighted_corr_by_valid_votes"] if row["weighted_corr_by_valid_votes"] is not None else 999,
    )[:8]

    write_rows(
        tables_dir / "turnout_share_group_summary_2026.csv",
        group_summary,
        [
            "group",
            "station_count",
            "registered_voters",
            "voters_signed",
            "valid_candidate_votes",
            "progressive_bulgaria_votes",
            "turnout_signed_over_registered",
            "progressive_bulgaria_share",
            "station_turnout_mean",
            "station_turnout_median",
            "station_pb_share_mean",
            "station_pb_share_median",
            "pearson_turnout_pb_share",
            "spearman_turnout_pb_share",
            "weighted_corr_by_valid_votes",
            "weighted_slope_pb_share_per_turnout_point",
        ],
    )
    write_rows(
        tables_dir / "turnout_share_region_summary_2026.csv",
        region_summary,
        [
            "region_id",
            "region_name",
            "group",
            "station_count",
            "registered_voters",
            "voters_signed",
            "valid_candidate_votes",
            "progressive_bulgaria_votes",
            "turnout_signed_over_registered",
            "progressive_bulgaria_share",
            "station_turnout_mean",
            "station_turnout_median",
            "station_pb_share_mean",
            "station_pb_share_median",
            "pearson_turnout_pb_share",
            "spearman_turnout_pb_share",
            "weighted_corr_by_valid_votes",
            "weighted_slope_pb_share_per_turnout_point",
        ],
    )
    write_rows(
        tables_dir / "turnout_bins_2026.csv",
        turnout_bins,
        [
            "turnout_bin",
            "station_count",
            "registered_voters",
            "voters_signed",
            "valid_candidate_votes",
            "progressive_bulgaria_votes",
            "turnout_signed_over_registered",
            "progressive_bulgaria_share",
            "station_pb_share_median",
        ],
    )
    write_rows(
        tables_dir / "high_turnout_high_progressive_bulgaria_2026.csv",
        high_turnout_high_share,
        [
            "section_id",
            "region_id",
            "admin_name",
            "place_name",
            "voting_mode",
            "registered_voters",
            "voters_signed",
            "turnout",
            "total_valid_candidate_votes",
            "progressive_bulgaria_votes",
            "progressive_bulgaria_share",
            "impact_votes_above_national_share",
        ],
    )
    write_rows(
        tables_dir / "extreme_turnout_stations_2026.csv",
        extreme_turnout,
        [
            "section_id",
            "region_id",
            "admin_name",
            "place_name",
            "voting_mode",
            "registered_voters",
            "voters_signed",
            "turnout",
            "total_valid_candidate_votes",
            "progressive_bulgaria_votes",
            "progressive_bulgaria_share",
        ],
    )

    make_heatmap_svg(
        df,
        figures_dir / "turnout_vs_progressive_bulgaria_share_2026.svg",
        "Turnout vs Progressive Bulgaria Share",
        "Each blue cell counts polling stations; red line is vote-weighted mean share by turnout bin",
    )
    make_heatmap_svg(
        df[df["is_abroad"] == 0],
        figures_dir / "turnout_vs_progressive_bulgaria_share_domestic_2026.svg",
        "Domestic Stations: Turnout vs Progressive Bulgaria Share",
        "Each blue cell counts polling stations; red line is vote-weighted mean share by turnout bin",
    )
    make_heatmap_svg(
        df[df["is_abroad"] == 1],
        figures_dir / "turnout_vs_progressive_bulgaria_share_abroad_2026.svg",
        "Abroad Stations: Turnout vs Progressive Bulgaria Share",
        "Each blue cell counts polling stations; red line is vote-weighted mean share by turnout bin",
    )
    make_bar_svg(turnout_bins, figures_dir / "progressive_bulgaria_share_by_turnout_bin_2026.svg", "Progressive Bulgaria Share by Turnout Bin")

    summary = {
        "input_csv": str(input_csv),
        "included_station_count": int(len(df)),
        "excluded_station_count": int(pd.read_csv(input_csv).shape[0] - len(df)),
        "group_summary": group_summary,
        "high_turnout_high_share_thresholds": {
            "turnout_gte": 0.80,
            "progressive_bulgaria_share_gte": 0.70,
            "valid_candidate_votes_gte": 50,
            "station_count": len(high_turnout_high_share),
            "total_valid_candidate_votes": int(sum(row["total_valid_candidate_votes"] for row in high_turnout_high_share)),
            "progressive_bulgaria_votes": int(sum(row["progressive_bulgaria_votes"] for row in high_turnout_high_share)),
            "scope_counts": high_scope_counts,
        },
        "extreme_turnout_thresholds": {
            "turnout_gte": 0.95,
            "turnout_lte": 0.05,
            "station_count": len(extreme_turnout),
            "scope_counts": extreme_scope_counts,
        },
        "top_positive_regions_by_weighted_corr": top_positive_regions,
        "top_negative_regions_by_weighted_corr": top_negative_regions,
        "figures": [
            str(figures_dir / "turnout_vs_progressive_bulgaria_share_2026.svg"),
            str(figures_dir / "turnout_vs_progressive_bulgaria_share_domestic_2026.svg"),
            str(figures_dir / "turnout_vs_progressive_bulgaria_share_abroad_2026.svg"),
            str(figures_dir / "progressive_bulgaria_share_by_turnout_bin_2026.svg"),
        ],
    }
    write_json(tables_dir / "turnout_share_summary_2026.json", summary)

    national = group_summary[0]
    domestic = next(row for row in group_summary if row["group"] == "domestic")
    abroad = next(row for row in group_summary if row["group"] == "abroad")
    mixed = next(row for row in group_summary if row["group"] == "voting_mode:mixed_machine_paper")
    paper_only = next(row for row in group_summary if row["group"] == "voting_mode:paper_only")

    note = f"""# Turnout vs Progressive Bulgaria Share

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_turnout_share.py
```

## Generated Outputs

Figures:

- `outputs/figures/turnout_vs_progressive_bulgaria_share_2026.svg`
- `outputs/figures/turnout_vs_progressive_bulgaria_share_domestic_2026.svg`
- `outputs/figures/turnout_vs_progressive_bulgaria_share_abroad_2026.svg`
- `outputs/figures/progressive_bulgaria_share_by_turnout_bin_2026.svg`

Tables:

- `outputs/tables/turnout_share_group_summary_2026.csv`
- `outputs/tables/turnout_share_region_summary_2026.csv`
- `outputs/tables/turnout_bins_2026.csv`
- `outputs/tables/high_turnout_high_progressive_bulgaria_2026.csv`
- `outputs/tables/extreme_turnout_stations_2026.csv`
- `outputs/tables/turnout_share_summary_2026.json`

## National Pattern

- Stations analyzed: `{national["station_count"]:,}`
- Registered voters: `{national["registered_voters"]:,}`
- Signed turnout: `{national["turnout_signed_over_registered"]:.3%}`
- Progressive Bulgaria votes: `{national["progressive_bulgaria_votes"]:,}`
- Progressive Bulgaria share of party/list valid votes: `{national["progressive_bulgaria_share"]:.3%}`
- Unweighted Pearson correlation between station turnout and Progressive Bulgaria share: `{national["pearson_turnout_pb_share"]:.3f}`
- Unweighted Spearman correlation: `{national["spearman_turnout_pb_share"]:.3f}`
- Valid-vote-weighted correlation: `{national["weighted_corr_by_valid_votes"]:.3f}`

## Domestic vs Abroad

| Group | Stations | Turnout | Progressive Bulgaria Share | Pearson r | Weighted r |
|---|---:|---:|---:|---:|---:|
| Domestic | `{domestic["station_count"]:,}` | `{domestic["turnout_signed_over_registered"]:.3%}` | `{domestic["progressive_bulgaria_share"]:.3%}` | `{domestic["pearson_turnout_pb_share"]:.3f}` | `{domestic["weighted_corr_by_valid_votes"]:.3f}` |
| Abroad | `{abroad["station_count"]:,}` | `{abroad["turnout_signed_over_registered"]:.3%}` | `{abroad["progressive_bulgaria_share"]:.3%}` | `{abroad["pearson_turnout_pb_share"]:.3f}` | `{abroad["weighted_corr_by_valid_votes"]:.3f}` |

## Voting Method Split

| Group | Stations | Turnout | Progressive Bulgaria Share | Pearson r | Weighted r |
|---|---:|---:|---:|---:|---:|
| Mixed machine/paper | `{mixed["station_count"]:,}` | `{mixed["turnout_signed_over_registered"]:.3%}` | `{mixed["progressive_bulgaria_share"]:.3%}` | `{mixed["pearson_turnout_pb_share"]:.3f}` | `{mixed["weighted_corr_by_valid_votes"]:.3f}` |
| Paper only | `{paper_only["station_count"]:,}` | `{paper_only["turnout_signed_over_registered"]:.3%}` | `{paper_only["progressive_bulgaria_share"]:.3%}` | `{paper_only["pearson_turnout_pb_share"]:.3f}` | `{paper_only["weighted_corr_by_valid_votes"]:.3f}` |

## Turnout Bins

| Turnout bin | Stations | Progressive Bulgaria share |
|---|---:|---:|
"""
    for row in turnout_bins:
        note += f"| {row['turnout_bin']} | {row['station_count']:,} | {row['progressive_bulgaria_share']:.3%} |\n"

    note += f"""
## High-Turnout / High-Share Leads

Threshold used for this first pass:

- turnout >= `80%`
- Progressive Bulgaria share >= `70%`
- valid candidate-list votes >= `50`

Stations meeting threshold: `{len(high_turnout_high_share):,}`

Scope split:

| Scope | Stations | Valid candidate-list votes | Progressive Bulgaria votes |
|---|---:|---:|---:|
"""
    for row in high_scope_counts:
        note += f"| {row['scope']} | {int(row['station_count']):,} | {int(row['valid_candidate_votes']):,} | {int(row['progressive_bulgaria_votes']):,} |\n"

    note += f"""
These rows are leads for later contextual review, not fraud findings. They are written to `outputs/tables/high_turnout_high_progressive_bulgaria_2026.csv`.

Extreme-turnout stations using turnout >= `95%` or <= `5%`: `{len(extreme_turnout):,}`. These are written to `outputs/tables/extreme_turnout_stations_2026.csv`.

Extreme-turnout scope split:

| Turnout bucket | Scope | Stations |
|---|---|---:|
"""
    for row in extreme_scope_counts:
        note += f"| {row['turnout_bucket']} | {row['scope']} | {int(row['station_count']):,} |\n"

    note += """
## Regional Correlations

Highest valid-vote-weighted turnout/share correlations:

| Region | Name | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|
"""
    for row in top_positive_regions:
        note += f"| {row['region_id']} | {row['region_name']} | {row['weighted_corr_by_valid_votes']:.3f} | {row['progressive_bulgaria_share']:.3%} |\n"

    note += """
Lowest valid-vote-weighted turnout/share correlations:

| Region | Name | Weighted r | Progressive Bulgaria share |
|---|---|---:|---:|
"""
    for row in top_negative_regions:
        note += f"| {row['region_id']} | {row['region_name']} | {row['weighted_corr_by_valid_votes']:.3f} | {row['progressive_bulgaria_share']:.3%} |\n"

    note += """
## Initial Interpretation

This first pass does not by itself prove anything about fraud. It establishes the turnout/share surface that later tests should control for by region, voting method, and historical baseline.

The national pattern is not a simple high-turnout/high-Progressive-Bulgaria pattern: the national Pearson correlation is negative, the valid-vote-weighted correlation is negative, and the 80-90% turnout bin has a lower Progressive Bulgaria share than the national average. The abroad stations behave differently and need separate treatment because their registered-voter denominators and turnout mechanics are not directly comparable with domestic sections.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "turnout_share_2026.md").write_text(note, encoding="utf-8")

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
        "--tables-dir",
        type=Path,
        default=Path("outputs/tables"),
        help="Directory for output tables.",
    )
    parser.add_argument(
        "--figures-dir",
        type=Path,
        default=Path("outputs/figures"),
        help="Directory for output figures.",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for generated notes.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(args.input_csv.resolve(), args.tables_dir.resolve(), args.figures_dir.resolve(), args.docs_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
