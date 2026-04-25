#!/usr/bin/env python3
"""Compare turnout/share patterns for Progressive Bulgaria against other parties."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROGRESSIVE_BULGARIA_PARTY_ID = 21


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


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


def party_name_for(group: pd.DataFrame) -> str:
    names = group.groupby("party_name")["valid_votes"].sum().sort_values(ascending=False)
    return str(names.index[0]) if len(names) else ""


def read_inputs(stations_csv: Path, votes_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    dtype = {
        "section_id": str,
        "region_id": str,
        "municipality_code": str,
        "admin_area_code": str,
        "precinct_code": str,
    }
    stations = pd.read_csv(stations_csv, dtype=dtype)
    votes = pd.read_csv(votes_csv, dtype={"section_id": str})
    for column in ["valid_votes", "paper_votes", "machine_votes", "party_id"]:
        votes[column] = pd.to_numeric(votes[column], errors="coerce").fillna(0).astype(int)
    station_cols = [
        "section_id",
        "region_id",
        "admin_name",
        "municipality_code",
        "place_name",
        "is_abroad",
        "voting_mode",
        "registered_voters",
        "voters_signed",
        "turnout",
        "total_valid_candidate_votes",
    ]
    work = votes.merge(stations[station_cols], on="section_id", how="left")
    for column in ["registered_voters", "voters_signed", "turnout", "total_valid_candidate_votes", "is_abroad"]:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work[work["total_valid_candidate_votes"] > 0].copy()
    work["party_share"] = work["valid_votes"] / work["total_valid_candidate_votes"]
    return stations, work


def summarize_parties(votes: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    national_valid_votes = float(votes.drop_duplicates("section_id")["total_valid_candidate_votes"].sum())
    for party_id, group in votes.groupby("party_id"):
        valid_votes = int(group["valid_votes"].sum())
        party_name = party_name_for(group)
        positive = group[group["valid_votes"] > 0]
        rows.append(
            {
                "party_id": int(party_id),
                "party_name": party_name,
                "valid_votes": valid_votes,
                "national_vote_share": valid_votes / national_valid_votes if national_valid_votes else None,
                "stations_with_votes": int((group["valid_votes"] > 0).sum()),
                "station_count": int(len(group)),
                "median_station_share": float(group["party_share"].median()),
                "median_positive_station_share": float(positive["party_share"].median()) if len(positive) else 0.0,
                "max_station_share": float(group["party_share"].max()),
                "paper_votes": int(group["paper_votes"].sum()),
                "machine_votes": int(group["machine_votes"].sum()),
                "paper_vote_share": group["paper_votes"].sum() / valid_votes if valid_votes else None,
                "weighted_corr_turnout_share": weighted_corr(group["turnout"], group["party_share"], group["total_valid_candidate_votes"]),
                "pearson_corr_turnout_share": pearson_corr(group["turnout"], group["party_share"]),
                "spearman_corr_turnout_share": spearman_corr(group["turnout"], group["party_share"]),
                "domestic_weighted_corr_turnout_share": weighted_corr(
                    group[group["is_abroad"] == 0]["turnout"],
                    group[group["is_abroad"] == 0]["party_share"],
                    group[group["is_abroad"] == 0]["total_valid_candidate_votes"],
                ),
                "abroad_weighted_corr_turnout_share": weighted_corr(
                    group[group["is_abroad"] == 1]["turnout"],
                    group[group["is_abroad"] == 1]["party_share"],
                    group[group["is_abroad"] == 1]["total_valid_candidate_votes"],
                ),
                "high_turnout_high_share_stations": int(
                    ((group["turnout"] >= 0.80) & (group["party_share"] >= 0.70) & (group["total_valid_candidate_votes"] >= 50)).sum()
                ),
                "valid_votes_in_high_turnout_high_share_stations": int(
                    group.loc[
                        (group["turnout"] >= 0.80)
                        & (group["party_share"] >= 0.70)
                        & (group["total_valid_candidate_votes"] >= 50),
                        "valid_votes",
                    ].sum()
                ),
            }
        )
    out = pd.DataFrame(rows).sort_values("valid_votes", ascending=False).reset_index(drop=True)
    out["vote_rank"] = np.arange(1, len(out) + 1)
    out["weighted_corr_rank_desc"] = out["weighted_corr_turnout_share"].rank(method="min", ascending=False)
    return out


def turnout_bins(votes: pd.DataFrame, top_party_ids: list[int]) -> pd.DataFrame:
    bins = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0000001]
    labels = ["0-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
    work = votes[votes["party_id"].isin(top_party_ids)].copy()
    work["turnout_bin"] = pd.cut(work["turnout"], bins=bins, labels=labels, include_lowest=True, right=False)
    rows: list[dict[str, Any]] = []
    for (party_id, turnout_bin), group in work.groupby(["party_id", "turnout_bin"], observed=False):
        if group.empty:
            continue
        party_name = party_name_for(group)
        party_votes = int(group["valid_votes"].sum())
        valid_votes = int(group["total_valid_candidate_votes"].sum())
        rows.append(
            {
                "party_id": int(party_id),
                "party_name": party_name,
                "turnout_bin": str(turnout_bin),
                "station_count": int(len(group)),
                "valid_candidate_votes": valid_votes,
                "party_votes": party_votes,
                "party_share": party_votes / valid_votes if valid_votes else None,
                "median_station_share": float(group["party_share"].median()),
            }
        )
    return pd.DataFrame(rows)


def station_party_leaders(stations: pd.DataFrame, votes: pd.DataFrame) -> pd.DataFrame:
    ordered = votes.sort_values(["section_id", "valid_votes", "party_id"], ascending=[True, False, True])
    leaders = []
    pb_rank = {}
    for section_id, group in ordered.groupby("section_id"):
        group = group.copy()
        group["rank"] = group["valid_votes"].rank(method="min", ascending=False).astype(int)
        pb_rows = group[group["party_id"] == PROGRESSIVE_BULGARIA_PARTY_ID]
        pb_rank[section_id] = int(pb_rows["rank"].iloc[0]) if not pb_rows.empty else None
        top = group.iloc[0]
        second = group.iloc[1] if len(group) > 1 else None
        total_valid = float(top["total_valid_candidate_votes"])
        top_share = top["valid_votes"] / total_valid if total_valid else None
        second_share = second["valid_votes"] / total_valid if second is not None and total_valid else None
        leaders.append(
            {
                "section_id": section_id,
                "top_party_id": int(top["party_id"]),
                "top_party_name": top["party_name"],
                "top_party_votes": int(top["valid_votes"]),
                "top_party_share": top_share,
                "second_party_id": int(second["party_id"]) if second is not None else None,
                "second_party_name": second["party_name"] if second is not None else "",
                "second_party_votes": int(second["valid_votes"]) if second is not None else None,
                "second_party_share": second_share,
                "winner_margin": top_share - second_share if top_share is not None and second_share is not None else None,
                "progressive_bulgaria_rank": pb_rank.get(section_id),
            }
        )
    leader_df = pd.DataFrame(leaders)
    station_cols = [
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
    return stations[station_cols].merge(leader_df, on="section_id", how="left")


def svg_correlation_chart(summary: pd.DataFrame, path: Path) -> None:
    rows = summary.head(14).sort_values("weighted_corr_turnout_share", ascending=True)
    width = 1040
    height = 620
    margin_left = 320
    margin_right = 48
    margin_top = 54
    margin_bottom = 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    min_value = min(-0.5, float(rows["weighted_corr_turnout_share"].min()))
    max_value = max(0.5, float(rows["weighted_corr_turnout_share"].max()))

    def x_map(value: float) -> float:
        return margin_left + (value - min_value) / (max_value - min_value) * plot_w

    row_h = plot_h / len(rows)
    zero_x = x_map(0)
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(
        f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">Weighted Turnout / Party Share Correlation</text>'
    )
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    elements.append(f'<line x1="{zero_x:.2f}" y1="{margin_top}" x2="{zero_x:.2f}" y2="{margin_top + plot_h}" stroke="#334155" stroke-width="1.4"/>')
    for i, (_, row) in enumerate(rows.iterrows()):
        y = margin_top + i * row_h + row_h * 0.22
        value = float(row["weighted_corr_turnout_share"])
        x = x_map(min(value, 0))
        bar_w = abs(x_map(value) - zero_x)
        color = "#2563eb" if value >= 0 else "#dc2626"
        label = str(row["party_name"])
        if len(label) > 42:
            label = label[:39] + "..."
        elements.append(
            f'<text x="{margin_left - 12}" y="{y + row_h * 0.34:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{html.escape(label)}</text>'
        )
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{row_h * 0.56:.2f}" fill="{color}"/>')
        elements.append(
            f'<text x="{x_map(value) + (6 if value >= 0 else -6):.2f}" y="{y + row_h * 0.36:.2f}" text-anchor="{"start" if value >= 0 else "end"}" font-family="Arial, sans-serif" font-size="11">{value:.3f}</text>'
        )
    for tick in np.linspace(min_value, max_value, 7):
        x = x_map(float(tick))
        elements.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + plot_h}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{x:.2f}" y="{height - 38}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{tick:.2f}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def markdown_rows(frame: pd.DataFrame, columns: list[str], limit: int = 12) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |\n"
    lines = []
    for _, row in frame.head(limit).iterrows():
        vals = []
        for col in columns:
            value = row[col]
            if pd.isna(value):
                vals.append("")
            elif isinstance(value, float):
                if "corr" in col:
                    vals.append(f"{value:.3f}")
                elif "share" in col:
                    vals.append(f"{value:.1%}")
                else:
                    vals.append(f"{value:.3f}")
            else:
                vals.append(f"{value:,}" if isinstance(value, (int, np.integer)) else str(value))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_document(docs_dir: Path, summary: dict[str, Any], party_summary: pd.DataFrame) -> None:
    pb = party_summary[party_summary["party_id"] == PROGRESSIVE_BULGARIA_PARTY_ID].iloc[0]
    top_corr = party_summary.sort_values("weighted_corr_turnout_share", ascending=False)
    bottom_corr = party_summary.sort_values("weighted_corr_turnout_share", ascending=True)
    note = f"""# Party Pattern Comparison

## Inputs

- `data/processed/cik_2026/votes_long.csv`
- `data/processed/cik_2026/polling_stations_2026.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_party_patterns.py
```

## Generated Outputs

- `outputs/tables/party_national_summary_2026.csv`
- `outputs/tables/party_turnout_bins_2026.csv`
- `outputs/tables/station_party_leaders_2026.csv`
- `outputs/tables/party_pattern_summary_2026.json`
- `outputs/figures/party_turnout_correlation_2026.svg`

## Progressive Bulgaria Context

- National vote share: `{pb["national_vote_share"]:.2%}`
- Vote rank: `{int(pb["vote_rank"])}`
- Weighted turnout/share correlation: `{pb["weighted_corr_turnout_share"]:.3f}`
- Correlation rank among parties, descending: `{int(pb["weighted_corr_rank_desc"])}`
- High-turnout/high-share stations under the same 80% turnout and 70% party-share rule: `{int(pb["high_turnout_high_share_stations"]):,}`

## Top Parties by Votes

| Rank | Party | Votes | Share | Weighted turnout/share r | High-turnout/high-share stations |
|---:|---|---:|---:|---:|---:|
{markdown_rows(party_summary, ["vote_rank", "party_name", "valid_votes", "national_vote_share", "weighted_corr_turnout_share", "high_turnout_high_share_stations"], limit=14)}

## Highest Positive Turnout/Share Correlations

| Party | Share | Weighted r | Domestic weighted r | Abroad weighted r |
|---|---:|---:|---:|---:|
{markdown_rows(top_corr, ["party_name", "national_vote_share", "weighted_corr_turnout_share", "domestic_weighted_corr_turnout_share", "abroad_weighted_corr_turnout_share"], limit=10)}

## Most Negative Turnout/Share Correlations

| Party | Share | Weighted r | Domestic weighted r | Abroad weighted r |
|---|---:|---:|---:|---:|
{markdown_rows(bottom_corr, ["party_name", "national_vote_share", "weighted_corr_turnout_share", "domestic_weighted_corr_turnout_share", "abroad_weighted_corr_turnout_share"], limit=10)}

## Initial Interpretation

Progressive Bulgaria's national result is unusual politically, but the turnout/share statistic is not a simple pro-winner stuffing pattern: its station-level weighted turnout/share correlation is negative overall. Other parties have stronger positive correlations with turnout. That does not clear every local anomaly, but it weakens the hypothesis of a broad nationwide mechanism where turnout and Progressive Bulgaria share rise together.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "party_patterns_2026.md").write_text(note, encoding="utf-8")


def analyze(stations_csv: Path, votes_csv: Path, tables_dir: Path, figures_dir: Path, docs_dir: Path) -> None:
    stations, votes = read_inputs(stations_csv, votes_csv)
    party_summary = summarize_parties(votes)
    top_party_ids = party_summary.head(10)["party_id"].astype(int).tolist()
    if PROGRESSIVE_BULGARIA_PARTY_ID not in top_party_ids:
        top_party_ids.append(PROGRESSIVE_BULGARIA_PARTY_ID)
    bins = turnout_bins(votes, top_party_ids)
    leaders = station_party_leaders(stations, votes)

    tables_dir.mkdir(parents=True, exist_ok=True)
    party_summary.to_csv(tables_dir / "party_national_summary_2026.csv", index=False)
    bins.to_csv(tables_dir / "party_turnout_bins_2026.csv", index=False)
    leaders.to_csv(tables_dir / "station_party_leaders_2026.csv", index=False)
    svg_correlation_chart(party_summary, figures_dir / "party_turnout_correlation_2026.svg")

    pb = party_summary[party_summary["party_id"] == PROGRESSIVE_BULGARIA_PARTY_ID].iloc[0]
    summary = {
        "party_count": int(len(party_summary)),
        "progressive_bulgaria_vote_share": clean(pb["national_vote_share"]),
        "progressive_bulgaria_vote_rank": int(pb["vote_rank"]),
        "progressive_bulgaria_weighted_turnout_share_corr": clean(pb["weighted_corr_turnout_share"]),
        "progressive_bulgaria_weighted_corr_rank_desc": int(pb["weighted_corr_rank_desc"]),
        "top_positive_corr_parties": party_summary.sort_values("weighted_corr_turnout_share", ascending=False)
        .head(10)["party_id"]
        .astype(int)
        .tolist(),
        "outputs": {
            "party_summary": str(tables_dir / "party_national_summary_2026.csv"),
            "turnout_bins": str(tables_dir / "party_turnout_bins_2026.csv"),
            "station_leaders": str(tables_dir / "station_party_leaders_2026.csv"),
            "figure": str(figures_dir / "party_turnout_correlation_2026.svg"),
        },
    }
    write_json(tables_dir / "party_pattern_summary_2026.json", summary)
    write_document(docs_dir, summary, party_summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations-csv", type=Path, default=Path("data/processed/cik_2026/polling_stations_2026.csv"))
    parser.add_argument("--votes-csv", type=Path, default=Path("data/processed/cik_2026/votes_long.csv"))
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(args.stations_csv.resolve(), args.votes_csv.resolve(), args.tables_dir.resolve(), args.figures_dir.resolve(), args.docs_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
