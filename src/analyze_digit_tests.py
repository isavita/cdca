#!/usr/bin/env python3
"""Low-priority digit diagnostics for station vote counts."""

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


def gammainc_lower_regularized(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x)."""
    if x <= 0:
        return 0.0
    if x < a + 1.0:
        term = 1.0 / a
        total = term
        ap = a
        for _ in range(200):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return min(1.0, total * math.exp(-x + a * math.log(x) - math.lgamma(a)))

    # Continued fraction for Q(a, x), then convert to P.
    b = x + 1.0 - a
    c = 1.0 / 1e-300
    d = 1.0 / b
    h = d
    for i in range(1, 200):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < 1e-300:
            d = 1e-300
        c = b + an / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    q = math.exp(-x + a * math.log(x) - math.lgamma(a)) * h
    return max(0.0, min(1.0, 1.0 - q))


def chi_square_survival(statistic: float, degrees_of_freedom: int) -> float:
    if statistic < 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - gammainc_lower_regularized(degrees_of_freedom / 2.0, statistic / 2.0)))


def chi_square_test(observed: np.ndarray, expected: np.ndarray) -> tuple[float, float]:
    mask = expected > 0
    statistic = float(((observed[mask] - expected[mask]) ** 2 / expected[mask]).sum())
    degrees = int(mask.sum() - 1)
    return statistic, chi_square_survival(statistic, degrees)


def last_digit_counts(values: pd.Series) -> np.ndarray:
    positive = values.dropna().astype(int)
    digits = positive.abs() % 10
    return np.bincount(digits, minlength=10)


def first_digit_counts(values: pd.Series) -> np.ndarray:
    positive = values.dropna().astype(int)
    positive = positive[positive > 0]
    first_digits = positive.astype(str).str[0].astype(int)
    return np.array([(first_digits == digit).sum() for digit in range(1, 10)])


def run_test(label: str, test_type: str, values: pd.Series) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values = pd.to_numeric(values, errors="coerce").dropna().astype(int)
    if test_type == "last_digit_uniform":
        values = values[values > 0]
        counts = last_digit_counts(values)
        expected = np.repeat(counts.sum() / 10.0, 10)
        statistic, p_value = chi_square_test(counts.astype(float), expected)
        digits = list(range(10))
        expected_probs = np.repeat(0.1, 10)
    elif test_type == "first_digit_benford":
        values = values[values > 0]
        counts = first_digit_counts(values)
        expected_probs = np.array([math.log10(1 + 1 / digit) for digit in range(1, 10)])
        expected = expected_probs * counts.sum()
        statistic, p_value = chi_square_test(counts.astype(float), expected)
        digits = list(range(1, 10))
    else:
        raise ValueError(f"Unknown digit test: {test_type}")

    total = int(counts.sum())
    max_abs_deviation = float(max(abs(count / total - prob) for count, prob in zip(counts, expected_probs, strict=False))) if total else None
    summary = {
        "series": label,
        "test_type": test_type,
        "sample_count": total,
        "chi_square_statistic": statistic,
        "p_value": p_value,
        "max_abs_digit_share_deviation": max_abs_deviation,
        "minimum_expected_count": float((expected_probs * total).min()) if total else None,
    }
    rows = []
    for digit, observed, expected_prob in zip(digits, counts, expected_probs, strict=False):
        rows.append(
            {
                "series": label,
                "test_type": test_type,
                "digit": int(digit),
                "observed_count": int(observed),
                "observed_share": observed / total if total else None,
                "expected_share": float(expected_prob),
                "expected_count": float(expected_prob * total),
                "observed_minus_expected_share": observed / total - expected_prob if total else None,
            }
        )
    return summary, rows


def build_series(stations: pd.DataFrame, votes: pd.DataFrame, party_summary: pd.DataFrame) -> dict[str, pd.Series]:
    series = {
        "station_total_valid_votes": stations["total_valid_candidate_votes"],
        "station_registered_voters": stations["registered_voters"],
        "station_voters_signed": stations["voters_signed"],
        "progressive_bulgaria_station_votes": stations["progressive_bulgaria_votes"],
    }
    top_party_ids = party_summary.head(10)["party_id"].astype(int).tolist()
    for party_id in top_party_ids:
        group = votes[votes["party_id"] == party_id]
        party_name = str(group["party_name"].mode().iloc[0]) if not group.empty else f"party_{party_id}"
        label = f"party_{party_id}_{party_name[:48]}"
        series[label] = group["valid_votes"]
    return series


def svg_last_digit(rows: pd.DataFrame, path: Path) -> None:
    target = rows[(rows["series"] == "progressive_bulgaria_station_votes") & (rows["test_type"] == "last_digit_uniform")]
    if target.empty:
        return
    width = 880
    height = 500
    margin_left = 74
    margin_right = 36
    margin_top = 54
    margin_bottom = 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_value = max(float(target["observed_share"].max()), float(target["expected_share"].max())) * 1.18

    def y_map(value: float) -> float:
        return margin_top + plot_h - value / max_value * plot_h

    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    elements.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    elements.append(
        f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700">Progressive Bulgaria Votes: Last Digit Distribution</text>'
    )
    elements.append(f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>')
    slot = plot_w / len(target)
    bar_w = slot * 0.58
    for idx, (_, row) in enumerate(target.sort_values("digit").iterrows()):
        value = float(row["observed_share"])
        x = margin_left + idx * slot + (slot - bar_w) / 2
        y = y_map(value)
        elements.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{margin_top + plot_h - y:.2f}" fill="#2563eb"/>')
        elements.append(
            f'<text x="{x + bar_w / 2:.2f}" y="{height - 38}" text-anchor="middle" font-family="Arial, sans-serif" font-size="13">{int(row["digit"])}</text>'
        )
    expected_y = y_map(0.10)
    elements.append(f'<line x1="{margin_left}" y1="{expected_y:.2f}" x2="{margin_left + plot_w}" y2="{expected_y:.2f}" stroke="#dc2626" stroke-width="2"/>')
    elements.append(
        f'<text x="{margin_left + plot_w - 6}" y="{expected_y - 6:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#dc2626">uniform 10%</text>'
    )
    for tick in np.linspace(0, max_value, 6):
        y = y_map(float(tick))
        elements.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e8f0"/>')
        elements.append(f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12">{tick:.0%}</text>')
    elements.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements), encoding="utf-8")


def markdown_rows(frame: pd.DataFrame, limit: int = 12) -> str:
    if frame.empty:
        return "| _none_ |  |  |  |\n"
    rows = []
    for _, row in frame.head(limit).iterrows():
        rows.append(
            "| "
            + " | ".join(
                [
                    str(row["series"]),
                    str(row["test_type"]),
                    f"{int(row['sample_count']):,}",
                    f"{row['chi_square_statistic']:.2f}",
                    f"{row['p_value']:.4g}",
                    f"{row['max_abs_digit_share_deviation']:.2%}" if pd.notna(row["max_abs_digit_share_deviation"]) else "",
                ]
            )
            + " |"
        )
    return "\n".join(rows)


def write_document(docs_dir: Path, summary: dict[str, Any], test_summary: pd.DataFrame) -> None:
    low_p = test_summary.sort_values("p_value").head(12)
    pb_tests = test_summary[test_summary["series"] == "progressive_bulgaria_station_votes"]
    note = f"""# Digit Diagnostics

## Inputs

- `data/processed/cik_2026/polling_stations_2026.csv`
- `data/processed/cik_2026/votes_long.csv`

Command:

```sh
/Users/isavita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/analyze_digit_tests.py
```

## Generated Outputs

- `outputs/tables/digit_test_summary_2026.csv`
- `outputs/tables/digit_test_digit_counts_2026.csv`
- `outputs/tables/digit_test_summary_2026.json`
- `outputs/figures/digit_test_progressive_bulgaria_last_digit_2026.svg`

## Summary

- Series tested: `{summary["series_count"]:,}`
- Tests run: `{summary["test_count"]:,}`
- Tests with p-value below 0.01: `{summary["tests_p_lt_0_01"]:,}`

## Progressive Bulgaria Tests

| Series | Test | Sample | Chi-square | p-value | Max digit-share deviation |
|---|---|---:|---:|---:|---:|
{markdown_rows(pb_tests, limit=4)}

## Lowest P-Value Diagnostics

| Series | Test | Sample | Chi-square | p-value | Max digit-share deviation |
|---|---|---:|---:|---:|---:|
{markdown_rows(low_p)}

## Interpretation

Digit tests are low-priority diagnostics here. Zero counts are excluded from the last-digit tests. Polling-station vote counts are constrained by station size, party geography, turnout, and local political support, so Benford or last-digit deviations are not fraud evidence on their own. These results are only useful if they line up with stronger evidence such as protocol mismatches, administrative complaints, coherent local clusters, or unexplained historical swings.
"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "digit_tests_2026.md").write_text(note, encoding="utf-8")


def analyze(stations_csv: Path, votes_csv: Path, party_summary_csv: Path, tables_dir: Path, figures_dir: Path, docs_dir: Path) -> None:
    stations = pd.read_csv(stations_csv, dtype={"section_id": str})
    votes = pd.read_csv(votes_csv, dtype={"section_id": str})
    party_summary = pd.read_csv(party_summary_csv)
    for column in ["total_valid_candidate_votes", "registered_voters", "voters_signed", "progressive_bulgaria_votes"]:
        stations[column] = pd.to_numeric(stations[column], errors="coerce").fillna(0).astype(int)
    for column in ["party_id", "valid_votes"]:
        votes[column] = pd.to_numeric(votes[column], errors="coerce").fillna(0).astype(int)

    summaries: list[dict[str, Any]] = []
    count_rows: list[dict[str, Any]] = []
    for label, values in build_series(stations, votes, party_summary).items():
        for test_type in ["last_digit_uniform", "first_digit_benford"]:
            test_summary, digit_rows = run_test(label, test_type, values)
            summaries.append(test_summary)
            count_rows.extend(digit_rows)

    summary_df = pd.DataFrame(summaries).sort_values(["p_value", "series"]).reset_index(drop=True)
    counts_df = pd.DataFrame(count_rows)
    tables_dir.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(tables_dir / "digit_test_summary_2026.csv", index=False)
    counts_df.to_csv(tables_dir / "digit_test_digit_counts_2026.csv", index=False)
    svg_last_digit(counts_df, figures_dir / "digit_test_progressive_bulgaria_last_digit_2026.svg")

    summary = {
        "series_count": int(summary_df["series"].nunique()),
        "test_count": int(len(summary_df)),
        "tests_p_lt_0_01": int((summary_df["p_value"] < 0.01).sum()),
        "progressive_bulgaria_tests": summary_df[summary_df["series"] == "progressive_bulgaria_station_votes"].to_dict("records"),
        "outputs": {
            "summary": str(tables_dir / "digit_test_summary_2026.csv"),
            "counts": str(tables_dir / "digit_test_digit_counts_2026.csv"),
            "figure": str(figures_dir / "digit_test_progressive_bulgaria_last_digit_2026.svg"),
        },
    }
    write_json(tables_dir / "digit_test_summary_2026.json", summary)
    write_document(docs_dir, summary, summary_df)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stations-csv", type=Path, default=Path("data/processed/cik_2026/polling_stations_2026.csv"))
    parser.add_argument("--votes-csv", type=Path, default=Path("data/processed/cik_2026/votes_long.csv"))
    parser.add_argument("--party-summary-csv", type=Path, default=Path("outputs/tables/party_national_summary_2026.csv"))
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analyze(
        args.stations_csv.resolve(),
        args.votes_csv.resolve(),
        args.party_summary_csv.resolve(),
        args.tables_dir.resolve(),
        args.figures_dir.resolve(),
        args.docs_dir.resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
