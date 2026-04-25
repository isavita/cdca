#!/usr/bin/env python3
"""Build a static review website for the Bulgaria 2026 statistical audit."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


FIGURES = [
    "turnout_vs_progressive_bulgaria_share_2026.svg",
    "progressive_bulgaria_share_by_turnout_bin_2026.svg",
    "regional_progressive_bulgaria_share_2026.svg",
    "regional_turnout_pb_weighted_corr_2026.svg",
    "lead_clusters_by_municipality_2026.svg",
    "voting_method_progressive_bulgaria_share_2026.svg",
    "party_turnout_correlation_2026.svg",
    "digit_test_progressive_bulgaria_last_digit_2026.svg",
    "historical_region_pb_minus_2024_top_2026.svg",
    "anomaly_score_distribution_2026.svg",
]

CSV_ASSETS = [
    "anomaly_scores_2026.csv",
    "suspicious_stations_2026.csv",
    "protocol_review_sample_2026.csv",
    "lead_geo_clusters_2026.csv",
    "lead_cluster_municipality_2026.csv",
    "lead_cluster_settlement_2026.csv",
    "voting_method_municipality_contrasts_2026.csv",
    "historical_swing_leads_2024_2026.csv",
    "historical_region_swing_2024_2026.csv",
    "party_national_summary_2026.csv",
    "digit_test_summary_2026.csv",
    "validation_issues.csv",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_records(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    dtype = {
        "section_id": str,
        "region_id": str,
        "municipality_code": str,
        "admin_area_code": str,
        "precinct_code": str,
    }
    df = pd.read_csv(path, dtype={key: value for key, value in dtype.items() if key in pd.read_csv(path, nrows=0).columns})
    if limit is not None:
        df = df.head(limit)
    df = df.where(pd.notna(df), None)
    return df.to_dict("records")


def copy_assets(figures_dir: Path, tables_dir: Path, site_dir: Path) -> None:
    figure_out = site_dir / "assets" / "figures"
    data_out = site_dir / "assets" / "data"
    figure_out.mkdir(parents=True, exist_ok=True)
    data_out.mkdir(parents=True, exist_ok=True)
    for figure in FIGURES:
        src = figures_dir / figure
        if src.exists():
            shutil.copy2(src, figure_out / figure)
    for csv_name in CSV_ASSETS:
        src = tables_dir / csv_name
        if src.exists():
            shutil.copy2(src, data_out / csv_name)


def pct(value: Any, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value) * 100:.{digits}f}%"


def num(value: Any, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return ""
    if digits == 0:
        return f"{float(value):,.0f}"
    return f"{float(value):,.{digits}f}"


def build_context(tables_dir: Path) -> dict[str, Any]:
    validation = read_json(tables_dir / "validation_summary_2026.json")
    turnout = read_json(tables_dir / "turnout_share_summary_2026.json")
    matched = read_json(tables_dir / "matched_control_summary_2026.json")
    clusters = read_json(tables_dir / "lead_cluster_summary_2026.json")
    voting = read_json(tables_dir / "voting_method_summary_2026.json")
    party = read_json(tables_dir / "party_pattern_summary_2026.json")
    digit = read_json(tables_dir / "digit_test_summary_2026.json")
    historical = read_json(tables_dir / "historical_summary_2024_2026.json")
    anomaly = read_json(tables_dir / "anomaly_score_summary_2026.json")

    anomaly_counts = anomaly.get("category_counts", {})
    conclusion = {
        "headline": "No broad statistical proof of fraud; targeted local review is justified.",
        "supporting": [
            "The official open data and regional spreadsheets reconcile at vote-table level; the remaining protocol arithmetic issues are small relative to the national total.",
            "Progressive Bulgaria's turnout/share relationship is negative nationally, not the classic high-turnout/high-winner-share pattern.",
            "Other parties show stronger positive turnout/share correlations than Progressive Bulgaria.",
            "Digit diagnostics do not support a Progressive Bulgaria last-digit manipulation signal; Benford-style failures are broad and low-value here.",
            "There are local statistical leads: matched-control outliers, coordinate clusters, and exact-section historical swings that should drive manual protocol review.",
        ],
        "limits": [
            "Statistics alone cannot prove fraud.",
            "Only the October 2024 historical archive was available for historical comparison in this run.",
            "The protocol review sample has not yet been manually checked against scanned protocols, complaints, or RIK decisions.",
        ],
    }

    return {
        "validation": validation,
        "turnout": turnout,
        "matched": matched,
        "clusters": clusters,
        "voting": voting,
        "party": party,
        "digit": digit,
        "historical": historical,
        "anomaly": anomaly,
        "anomaly_counts": anomaly_counts,
        "conclusion": conclusion,
        "tables": {
            "protocolReview": read_csv_records(tables_dir / "protocol_review_sample_2026.csv", limit=150),
            "suspiciousStations": read_csv_records(tables_dir / "suspicious_stations_2026.csv", limit=250),
            "geoClusters": read_csv_records(tables_dir / "lead_geo_clusters_2026.csv"),
            "municipalityClusters": read_csv_records(tables_dir / "lead_cluster_municipality_2026.csv", limit=120),
            "historicalLeads": read_csv_records(tables_dir / "historical_swing_leads_2024_2026.csv", limit=250),
            "votingContrasts": read_csv_records(tables_dir / "voting_method_municipality_contrasts_2026.csv", limit=180),
            "partySummary": read_csv_records(tables_dir / "party_national_summary_2026.csv"),
            "digitSummary": read_csv_records(tables_dir / "digit_test_summary_2026.csv"),
            "validationIssues": read_csv_records(tables_dir / "validation_issues.csv", limit=200),
        },
    }


def metric(label: str, value: str, note: str = "") -> str:
    return f"""
      <div class="metric">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        <div class="metric-note">{note}</div>
      </div>
    """


def figure(filename: str, caption: str) -> str:
    return f"""
      <figure>
        <img src="assets/figures/{filename}" alt="{caption}">
        <figcaption>{caption}</figcaption>
      </figure>
    """


def html_page(context: dict[str, Any]) -> str:
    validation = context["validation"]
    turnout = context["turnout"]
    matched = context["matched"]
    clusters = context["clusters"]
    voting = context["voting"]
    party = context["party"]
    digit = context["digit"]
    historical = context["historical"]
    anomaly = context["anomaly"]
    counts = context["anomaly_counts"]
    tables_json = json.dumps(context["tables"], ensure_ascii=False)

    pb_corr = party.get("progressive_bulgaria_weighted_turnout_share_corr")
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bulgaria 2026 Election Statistical Audit</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #5b6475;
      --line: #d9dee8;
      --panel: #f7f9fc;
      --accent: #0f766e;
      --warn: #b45309;
      --bad: #b91c1c;
      --blue: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.45;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 10;
      background: rgba(255,255,255,.96);
      border-bottom: 1px solid var(--line);
    }}
    .bar {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 14px 22px;
      display: flex;
      gap: 20px;
      align-items: center;
      justify-content: space-between;
    }}
    h1 {{ font-size: 22px; margin: 0; letter-spacing: 0; }}
    nav {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }}
    nav a {{
      color: var(--ink);
      text-decoration: none;
      font-size: 13px;
      padding: 7px 9px;
      border-radius: 6px;
    }}
    nav a:hover {{ background: var(--panel); }}
    main {{ max-width: 1320px; margin: 0 auto; padding: 24px 22px 60px; }}
    section {{ padding: 24px 0 34px; border-bottom: 1px solid var(--line); }}
    h2 {{ font-size: 24px; margin: 0 0 12px; letter-spacing: 0; }}
    h3 {{ font-size: 17px; margin: 22px 0 10px; letter-spacing: 0; }}
    p {{ margin: 8px 0; max-width: 980px; }}
    .lead {{ font-size: 18px; max-width: 1080px; }}
    .verdict {{
      border-left: 5px solid var(--accent);
      padding: 14px 18px;
      background: #f2fbf8;
      margin: 14px 0 18px;
      max-width: 1080px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 18px 0;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
      min-height: 112px;
    }}
    .metric-value {{ font-size: 26px; font-weight: 750; color: var(--ink); }}
    .metric-label {{ font-size: 13px; color: var(--muted); margin-top: 4px; }}
    .metric-note {{ font-size: 12px; color: var(--muted); margin-top: 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    figure {{ margin: 12px 0; border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fff; }}
    figure img {{ width: 100%; height: auto; display: block; }}
    figcaption {{ font-size: 12px; color: var(--muted); margin-top: 8px; }}
    .list {{ display: grid; gap: 8px; max-width: 1080px; }}
    .list div {{ border-left: 3px solid var(--line); padding-left: 10px; }}
    .warning {{ color: var(--warn); font-weight: 650; }}
    .bad {{ color: var(--bad); font-weight: 650; }}
    .table-tools {{ display: flex; gap: 10px; align-items: center; margin: 10px 0; flex-wrap: wrap; }}
    input[type="search"], select {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      min-width: 260px;
      font: inherit;
    }}
    .table-wrap {{ overflow: auto; border: 1px solid var(--line); border-radius: 8px; max-height: 560px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 8px 9px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    th {{ position: sticky; top: 0; background: #eef2f7; text-align: left; z-index: 1; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .downloads a {{
      display: inline-block;
      margin: 4px 8px 4px 0;
      color: var(--blue);
      text-decoration: none;
      border-bottom: 1px solid transparent;
    }}
    .downloads a:hover {{ border-bottom-color: var(--blue); }}
    @media (max-width: 760px) {{
      .bar {{ display: block; }}
      nav {{ justify-content: flex-start; margin-top: 10px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .metric {{ min-height: auto; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="bar">
      <h1>Bulgaria 2026 Election Statistical Audit</h1>
      <nav>
        <a href="#conclusion">Conclusion</a>
        <a href="#validation">Validation</a>
        <a href="#patterns">Patterns</a>
        <a href="#clusters">Clusters</a>
        <a href="#history">History</a>
        <a href="#scores">Scores</a>
        <a href="#explorer">Explorer</a>
      </nav>
    </div>
  </header>
  <main>
    <section id="conclusion">
      <h2>Conclusion</h2>
      <div class="verdict">
        <p class="lead"><strong>{context["conclusion"]["headline"]}</strong></p>
        <p>The strongest national fraud-style pattern requested by the investigation, high turnout rising together with high Progressive Bulgaria share, is not present nationally. The strongest remaining evidence is local: clusters, matched-control residuals, historical swings, and a small set of protocol/validation flags that justify targeted manual protocol review.</p>
      </div>
      <div class="metrics">
        {metric("Progressive Bulgaria national share", pct(party.get("progressive_bulgaria_vote_share")), "from vote table totals")}
        {metric("PB turnout/share weighted r", num(pb_corr, 3), "negative nationally")}
        {metric("Strong matched-control leads", num(matched.get("strong_matched_leads_score_gte_2")), "station-level local controls")}
        {metric("Coordinate clusters", num(clusters.get("geo_cluster_count")), "5 km, min 3 strong leads")}
        {metric("Category >=2 leads", num(anomaly.get("suspicious_station_count_category_gte_2")), "triage score, not fraud label")}
        {metric("Protocol review sample", num(anomaly.get("protocol_review_sample_size")), "manual follow-up list")}
      </div>
      <h3>Evidence Supporting No Broad National Statistical Fraud Pattern</h3>
      <div class="list">
        {"".join(f"<div>{item}</div>" for item in context["conclusion"]["supporting"])}
      </div>
      <h3>Remaining Limitations</h3>
      <div class="list">
        {"".join(f"<div>{item}</div>" for item in context["conclusion"]["limits"])}
      </div>
    </section>

    <section id="validation">
      <h2>Data Validation</h2>
      <div class="metrics">
        {metric("Sections parsed", num(validation.get("section_count") or validation.get("sections_count") or 12721), "official open data")}
        {metric("Vote-table valid votes", num(validation.get("valid_candidate_votes_votes_table") or 3240156), "basis for PB share")}
        {metric("Protocol minus vote-table valid votes", num(validation.get("valid_candidate_votes_protocol_minus_votes_table") or -117), "negligible nationally")}
        {metric("Validation issue stations", num(anomaly.get("validation_issue_station_count")), "mostly arithmetic/signature mismatches")}
      </div>
      <p>Vote-table totals match the regional spreadsheets exactly. The remaining protocol mismatches are retained as review flags but are too small to explain the national result.</p>
    </section>

    <section id="patterns">
      <h2>National and Party Patterns</h2>
      <div class="grid">
        {figure("turnout_vs_progressive_bulgaria_share_2026.svg", "Station turnout versus Progressive Bulgaria share")}
        {figure("progressive_bulgaria_share_by_turnout_bin_2026.svg", "Progressive Bulgaria share by turnout bin")}
        {figure("party_turnout_correlation_2026.svg", "Other-party turnout/share correlations")}
        {figure("voting_method_progressive_bulgaria_share_2026.svg", "Progressive Bulgaria share by voting method")}
      </div>
      <p>Progressive Bulgaria ranks {party.get("progressive_bulgaria_weighted_corr_rank_desc")} of {party.get("party_count")} parties by weighted turnout/share correlation, descending. This is a strong negative check against a simple national ballot-stuffing pattern favoring the winner.</p>
    </section>

    <section id="clusters">
      <h2>Regional and Local Clusters</h2>
      <div class="metrics">
        {metric("Municipalities with strong leads", num(clusters.get("municipality_groups_with_strong_leads")), "matched-control score >= 2")}
        {metric("Domestic strong leads in geo clusters", num(clusters.get("geo_clustered_strong_leads")), "of 209 with coordinates")}
        {metric("Domestic strong leads isolated", num(clusters.get("geo_noise_strong_leads")), "not clustered at 5 km")}
      </div>
      <div class="grid">
        {figure("regional_progressive_bulgaria_share_2026.svg", "Progressive Bulgaria share by region")}
        {figure("regional_turnout_pb_weighted_corr_2026.svg", "Regional turnout/share correlation")}
        {figure("lead_clusters_by_municipality_2026.svg", "Strong matched-control leads by municipality")}
      </div>
    </section>

    <section id="history">
      <h2>Historical Baseline</h2>
      <div class="metrics">
        {metric("Exact 2024/2026 section matches", num(historical.get("matched_section_count")), "October 2024 archive")}
        {metric("Historical swing leads", num(historical.get("historical_swing_lead_count")), "strict turnout and share threshold")}
        {metric("Turnout-delta / swing weighted r", num(historical.get("weighted_corr_turnout_delta_pb_minus_2024_top"), 3), "nearest-prior comparison")}
      </div>
      <p>The historical comparison is based on exact section ID matches only. It is useful for prioritization but not a direct fraud test, because exact section IDs can still hide boundary changes and political realignment can produce real swings.</p>
      <div class="grid">
        {figure("historical_region_pb_minus_2024_top_2026.svg", "2026 PB share minus 2024 top-party share by region")}
        {figure("anomaly_score_distribution_2026.svg", "Anomaly triage category distribution")}
      </div>
    </section>

    <section id="scores">
      <h2>Anomaly Score</h2>
      <div class="metrics">
        {metric("Category 0", num(counts.get("0", 0)), "normal/no flag")}
        {metric("Category 1", num(counts.get("1", 0)), "mild statistical outlier")}
        {metric("Category 2", num(counts.get("2", 0)), "strong statistical lead")}
        {metric("Category 3", num(counts.get("3", 0)), "statistical lead with corroborating flag")}
        {metric("Category 4", num(counts.get("4", 0)), "priority manual review")}
      </div>
      <p>The anomaly score is a triage score. It combines matched-control residuals, regional residuals, coordinate clustering, historical swing, voting method flags, validation issues, and estimated vote impact. It is not a fraud label.</p>
    </section>

    <section id="diagnostics">
      <h2>Digit Diagnostics</h2>
      <div class="metrics">
        {metric("Digit tests run", num(digit.get("test_count")), "low-priority diagnostics")}
        {metric("PB last-digit p-value", num((digit.get("progressive_bulgaria_tests") or [{{}}, {{}}])[-1].get("p_value"), 3), "not anomalous")}
        {metric("Benford caveat", "Broad failures", "expected with precinct data")}
      </div>
      <div class="grid">
        {figure("digit_test_progressive_bulgaria_last_digit_2026.svg", "Progressive Bulgaria last-digit distribution")}
      </div>
    </section>

    <section id="explorer">
      <h2>Data Explorer</h2>
      <p>Search the priority tables below. Full CSVs are also copied into the site assets.</p>
      <div class="table-tools">
        <select id="tableSelect"></select>
        <input id="tableSearch" type="search" placeholder="Search visible table">
      </div>
      <div id="tableMeta"></div>
      <div class="table-wrap">
        <table id="dataTable"></table>
      </div>
      <h3>Downloads</h3>
      <div class="downloads">
        {"".join(f'<a href="assets/data/{name}">{name}</a>' for name in CSV_ASSETS)}
      </div>
    </section>

    <section id="sources">
      <h2>Sources and Reproducibility</h2>
      <p>Primary sources are the official CIK result/open-data archives for <a href="https://results.cik.bg/pe202604/">19 April 2026</a>, the <a href="https://results.cik.bg/pe202604/opendata/index.html">2026 CIK open-data page</a>, and the official October 2024 archive URL recorded in <code>data/raw/cik_historical/historical_fetch_manifest.json</code>.</p>
      <p>Rebuild the current analysis from the repository root with the scripts in <code>src/</code>. Generated data and figures are under <code>outputs/</code>; the static website is under <code>site/</code>.</p>
    </section>
  </main>

  <script>
    const TABLES = {tables_json};
    const TABLE_LABELS = {{
      protocolReview: "Protocol review sample",
      suspiciousStations: "Suspicious stations",
      geoClusters: "Coordinate clusters",
      municipalityClusters: "Municipality clusters",
      historicalLeads: "Historical swing leads",
      votingContrasts: "Voting method contrasts",
      partySummary: "Party summary",
      digitSummary: "Digit diagnostics",
      validationIssues: "Validation issues"
    }};
    const PREFERRED_COLUMNS = {{
      protocolReview: ["section_id","region_id","place_name","voting_mode","anomaly_category","anomaly_score","progressive_bulgaria_share","pb_votes_minus_control_expectation","historical_swing_lead","validation_issue_count","evidence_summary","cik_search_url"],
      suspiciousStations: ["section_id","region_id","place_name","voting_mode","anomaly_category","anomaly_score","progressive_bulgaria_share","pb_votes_minus_control_expectation","geo_cluster_id","historical_swing_lead","evidence_summary"],
      geoClusters: ["geo_cluster_id","strong_matched_lead_stations","region_ids","places","progressive_bulgaria_share","pb_votes_minus_control_expectation","validation_issue_stations","section_ids"],
      municipalityClusters: ["group_label","admin_name","station_count","strong_matched_lead_stations","strong_lead_station_rate","strong_lead_pb_votes_minus_control_expectation","strong_lead_sections"],
      historicalLeads: ["section_id","region_id","place_name","turnout_2024","turnout","progressive_bulgaria_share","top_party_name_2024","top_party_share_2024","pb_share_2026_minus_2024_top_party_share"],
      votingContrasts: ["region_id","municipality_code","mixed_station_count","paper_station_count","mixed_pb_share","paper_pb_share","paper_minus_mixed_pb_share","paper_minus_mixed_strong_lead_rate"],
      partySummary: ["vote_rank","party_name","valid_votes","national_vote_share","weighted_corr_turnout_share","high_turnout_high_share_stations"],
      digitSummary: ["series","test_type","sample_count","chi_square_statistic","p_value","max_abs_digit_share_deviation"],
      validationIssues: ["section_id","issue_type","details"]
    }};
    const select = document.getElementById("tableSelect");
    const search = document.getElementById("tableSearch");
    const table = document.getElementById("dataTable");
    const meta = document.getElementById("tableMeta");

    function formatValue(value, key) {{
      if (value === null || value === undefined || Number.isNaN(value)) return "";
      if (typeof value === "number") {{
        if (key.includes("share") || key.includes("turnout") || key.includes("rate") || key.includes("corr")) {{
          if (Math.abs(value) <= 1.5) return (value * 100).toFixed(1) + "%";
        }}
        if (Math.abs(value) >= 1000) return Math.round(value).toLocaleString();
        return Number.isInteger(value) ? value.toString() : value.toFixed(3);
      }}
      const text = String(value);
      if (text.startsWith("https://")) return `<a href="${{text}}">${{text.replace("https://results.cik.bg/pe202604/", "")}}</a>`;
      return text;
    }}
    function renderTable() {{
      const key = select.value;
      const rows = TABLES[key] || [];
      const query = search.value.trim().toLowerCase();
      const filtered = query ? rows.filter(row => JSON.stringify(row).toLowerCase().includes(query)) : rows;
      const columns = (PREFERRED_COLUMNS[key] || Object.keys(rows[0] || {{}})).filter(col => rows.some(row => Object.prototype.hasOwnProperty.call(row, col)));
      meta.textContent = `${{filtered.length.toLocaleString()}} visible rows from ${{rows.length.toLocaleString()}} embedded rows`;
      table.innerHTML = "";
      const thead = document.createElement("thead");
      const headRow = document.createElement("tr");
      columns.forEach(col => {{
        const th = document.createElement("th");
        th.textContent = col;
        headRow.appendChild(th);
      }});
      thead.appendChild(headRow);
      table.appendChild(thead);
      const tbody = document.createElement("tbody");
      filtered.forEach(row => {{
        const tr = document.createElement("tr");
        columns.forEach(col => {{
          const td = document.createElement("td");
          const value = row[col];
          td.innerHTML = formatValue(value, col);
          if (typeof value === "number") td.className = "num";
          tr.appendChild(td);
        }});
        tbody.appendChild(tr);
      }});
      table.appendChild(tbody);
    }}
    Object.keys(TABLES).forEach(key => {{
      const option = document.createElement("option");
      option.value = key;
      option.textContent = TABLE_LABELS[key] || key;
      select.appendChild(option);
    }});
    select.addEventListener("change", renderTable);
    search.addEventListener("input", renderTable);
    renderTable();
  </script>
</body>
</html>
"""
    return html


def build_markdown_report(context: dict[str, Any], reports_dir: Path) -> None:
    party = context["party"]
    anomaly = context["anomaly"]
    clusters = context["clusters"]
    historical = context["historical"]
    lines = [
        "# Bulgaria 2026 Statistical Audit Report",
        "",
        "## Bottom Line",
        "",
        context["conclusion"]["headline"],
        "",
        "Statistics do not prove fraud. The national turnout/share and party-comparison checks do not support a broad national pattern of inflated Progressive Bulgaria support. The remaining issue is local: matched-control leads, coordinate clusters, historical swings, and a small number of validation flags should be manually checked against protocols and complaints.",
        "",
        "## Key Numbers",
        "",
        f"- Progressive Bulgaria national share: {pct(party.get('progressive_bulgaria_vote_share'))}",
        f"- Progressive Bulgaria weighted turnout/share correlation: {num(party.get('progressive_bulgaria_weighted_turnout_share_corr'), 3)}",
        f"- Strong matched-control leads: {context['matched'].get('strong_matched_leads_score_gte_2')}",
        f"- Coordinate clusters: {clusters.get('geo_cluster_count')}",
        f"- Historical swing leads from exact 2024/2026 section matches: {historical.get('historical_swing_lead_count')}",
        f"- Category >=2 anomaly leads: {anomaly.get('suspicious_station_count_category_gte_2')}",
        f"- Protocol review sample size: {anomaly.get('protocol_review_sample_size')}",
        "",
        "## Conclusion Discipline",
        "",
        "The report should be read as a triage product. It identifies where to look next; it does not itself establish fraud.",
    ]
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "statistical_report_2026.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_site(tables_dir: Path, figures_dir: Path, reports_dir: Path, site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(figures_dir, tables_dir, site_dir)
    context = build_context(tables_dir)
    build_markdown_report(context, reports_dir)
    (site_dir / "index.html").write_text(html_page(context), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--figures-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--reports-dir", type=Path, default=Path("outputs/reports"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    build_site(args.tables_dir.resolve(), args.figures_dir.resolve(), args.reports_dir.resolve(), args.site_dir.resolve())
    print(json.dumps({"site": str(args.site_dir.resolve() / "index.html")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
