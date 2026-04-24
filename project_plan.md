# Bulgaria 2026 Election Statistical Audit

_A reproducible investigation into whether the 19 April 2026 Bulgarian parliamentary election results show statistically unusual patterns consistent with irregularities, or whether the official results look explainable from available data._

---

## 0. Investigation Principles

- [ ] Treat statistical anomalies as leads, not proof of fraud.
- [ ] Start from a neutral null hypothesis: the published result is valid unless evidence shows otherwise.
- [ ] Keep the project transparent: the subject is the Bulgaria 2026 parliamentary election.
- [ ] Use only official, public, legally accessible data and clearly cited secondary sources.
- [ ] Preserve raw files exactly as downloaded, with timestamps and checksums.
- [ ] Make every chart, table, and conclusion reproducible from code.
- [ ] Distinguish between:
  - [ ] strong evidence of tabulation/data inconsistency;
  - [ ] statistical anomaly needing human review;
  - [ ] politically surprising but statistically plausible results;
  - [ ] no meaningful anomaly found.

---

## 1. Core Questions

- [ ] Did Progressive Bulgaria's roughly 45% national result behave unusually at polling-station level?
- [ ] Are high Progressive Bulgaria vote shares concentrated in unusually high-turnout stations?
- [ ] Are there sharp swings from previous elections that cannot be explained by broader national/regional swings?
- [ ] Do machine voting, paper voting, machine-failure, or paper-only sections show different patterns?
- [ ] Do suspicious statistical patterns overlap with complaints, protocol corrections, scanned-protocol issues, or local RIK decisions?
- [ ] Are anomalies large enough to have affected seat allocation or only local/noisy artifacts?

---

## 2. Data Acquisition

### 2.1 Official 2026 CIK Data

- [ ] Use the official CIK results site for the 19 April 2026 election:
  - [ ] `https://results.cik.bg/pe202604/`
  - [ ] `https://results.cik.bg/pe202604/opendata/index.html`
- [ ] Download machine-readable results and spreadsheet exports from the CIK open-data page.
- [ ] Download or reference:
  - [ ] polling-station level vote totals;
  - [ ] registered voters;
  - [ ] valid and invalid votes;
  - [ ] "I do not support anyone" votes;
  - [ ] party/coalition vote counts;
  - [ ] domestic vs abroad sections;
  - [ ] region, municipality, settlement, and station identifiers;
  - [ ] voting method indicators, where available;
  - [ ] scanned protocols;
  - [ ] machine files / machine-voting audit files, where available;
  - [ ] video links, where available.

### 2.2 Election Administration and Complaint Data

- [ ] Collect CIK decisions relevant to the election.
- [ ] Collect RIK decisions and complaints for all regions, especially:
  - [ ] machine-voting failures;
  - [ ] paper-only transitions;
  - [ ] protocol corrections;
  - [ ] complaints about secrecy of vote;
  - [ ] complaints about controlled voting, crowding, or procedural irregularities;
  - [ ] section commission replacements on election day.
- [ ] Link complaints and decisions to station IDs whenever possible.

### 2.3 Historical Baseline Data

- [ ] Download prior parliamentary election results from CIK, ideally at the same polling-station granularity:
  - [ ] October 2024;
  - [ ] June 2024;
  - [ ] April 2023;
  - [ ] October 2022;
  - [ ] November 2021;
  - [ ] July 2021;
  - [ ] April 2021.
- [ ] Build municipality-level historical baselines if polling-station IDs are not stable across elections.
- [ ] Track polling-station boundary changes and avoid false comparisons when sections were split, merged, renamed, or moved.

### 2.4 Polling and Observation Context

- [ ] Save pre-election polls, exit polls, and parallel-count reports from reputable sources.
- [ ] Save OSCE/ODIHR materials:
  - [ ] Needs Assessment Mission report;
  - [ ] interim report;
  - [ ] statement of preliminary findings;
  - [ ] final report when published.
- [ ] Record dates, sample sizes, methods, and stated margins of error for polling sources.

---

## 3. Data Storage

- [ ] Create this structure:

```text
data/
  raw/
    cik_2026/
    cik_historical/
    rik_decisions/
    polling/
    osce_odihr/
  interim/
  processed/
outputs/
  figures/
  tables/
  reports/
src/
tests/
notebooks/
```

- [ ] Store each raw download with:
  - [ ] source URL;
  - [ ] download timestamp;
  - [ ] file checksum;
  - [ ] brief metadata note.

---

## 4. Data Validation

- [ ] Parse official open-data files into normalized tables.
- [ ] Reproduce official national totals exactly.
- [ ] Reproduce official regional totals exactly.
- [ ] Reproduce official party totals exactly.
- [ ] Reconcile totals against CIK web pages and spreadsheet exports.
- [ ] Flag but do not silently fix:
  - [ ] missing station IDs;
  - [ ] duplicate station IDs;
  - [ ] impossible turnout;
  - [ ] negative or non-numeric vote counts;
  - [ ] party vote totals greater than valid votes;
  - [ ] registered voters equal to zero with votes cast;
  - [ ] protocol totals that do not sum correctly.

No forensic analysis should be trusted until the official totals are reproduced.

---

## 5. Derived Variables

For every polling station:

- [ ] `turnout = votes_cast / registered_voters`
- [ ] `valid_vote_rate = valid_votes / votes_cast`
- [ ] `party_vote_share = party_votes / valid_votes`
- [ ] `winner_margin = top_party_share - second_party_share`
- [ ] `progressive_bulgaria_share`
- [ ] `progressive_bulgaria_votes`
- [ ] `domestic_or_abroad`
- [ ] `machine_or_paper`
- [ ] `paper_only_or_machine_failure`, if available
- [ ] `historical_turnout_delta`
- [ ] `historical_party_or_bloc_delta`
- [ ] `regional_residual`
- [ ] `municipality_residual`
- [ ] `complaint_or_protocol_flag`

---

## 6. Main Statistical Tests

### 6.1 Turnout vs Vote Share

- [ ] Plot Progressive Bulgaria vote share against turnout for all stations.
- [ ] Repeat by region, municipality, and domestic/abroad status.
- [ ] Compare against other parties.
- [ ] Estimate whether high turnout disproportionately benefits one party.
- [ ] Use robust regression or non-parametric smoothing rather than simple eyeballing.

Reason: ballot stuffing or controlled voting can sometimes appear as high turnout combined with high vote share for one party.

### 6.2 Historical Swing Analysis

- [ ] Compare 2026 turnout to previous elections at station or municipality level.
- [ ] Compare Progressive Bulgaria support to plausible predecessor blocs or vote pools, with assumptions documented.
- [ ] Identify stations with extreme swings after subtracting regional/national swing.
- [ ] Separate new political realignment from local outliers.

Reason: a national landslide can be real, but unexplained local jumps are more informative than the national headline.

### 6.3 Matched Controls

- [ ] Compare suspicious stations to similar nearby stations using:
  - [ ] same municipality or neighboring municipality;
  - [ ] similar registered-voter count;
  - [ ] similar prior turnout;
  - [ ] similar prior party mix;
  - [ ] same voting method where possible.
- [ ] Flag stations only when they remain anomalous relative to matched controls.

Reason: raw national thresholds can falsely flag places with legitimate local political differences.

### 6.4 Voting Method Analysis

- [ ] Compare machine, paper, mixed, and paper-only sections.
- [ ] Test whether machine-failure sections have unusual turnout or party shares.
- [ ] Compare paper-only sections to matched machine-voting sections.
- [ ] Check whether voting-method effects persist after controlling for geography and historical voting patterns.

Reason: procedural changes are more suspicious when they coincide with unusual result shifts.

### 6.5 Spatial Clustering

- [ ] Map turnout, Progressive Bulgaria share, and residual anomalies by municipality/section.
- [ ] Use Local Moran's I, Getis-Ord Gi*, DBSCAN, or simpler neighbor-based clustering depending on available geography.
- [ ] Identify clusters of high-turnout/high-share anomalies.
- [ ] Cross-reference clusters with complaints and protocol issues.

Reason: isolated outliers can be noise; geographically coherent clusters deserve more attention.

### 6.6 Protocol and Arithmetic Checks

- [ ] Compare machine-readable totals against scanned protocols for a sample of stations.
- [ ] Prioritize:
  - [ ] statistical outliers;
  - [ ] high-impact stations;
  - [ ] stations with complaints;
  - [ ] paper-only or machine-failure stations.
- [ ] Check arithmetic consistency inside protocols.
- [ ] Record whether discrepancies are clerical, explainable, or unresolved.

Reason: direct protocol inconsistencies are stronger evidence than distributional tests.

### 6.7 Digit Tests as Low-Priority Diagnostics

- [ ] Run last-digit tests on vote counts where sample sizes are large enough.
- [ ] Run Benford-style first/second-digit tests only as exploratory diagnostics.
- [ ] Do not present Benford failures as evidence of fraud by themselves.
- [ ] Require corroboration from turnout, historical, spatial, or protocol evidence.

Reason: precinct vote counts often violate Benford assumptions even in clean elections.

---

## 7. Anomaly Scoring

Create an explainable score for each station. The score should be additive and auditable, not a black-box fraud label.

Potential indicators:

- [ ] extreme turnout;
- [ ] extreme Progressive Bulgaria share;
- [ ] high turnout plus high Progressive Bulgaria share;
- [ ] large unexplained historical swing;
- [ ] large residual after regional/municipality model;
- [ ] unusual result compared with matched controls;
- [ ] voting-method anomaly;
- [ ] local spatial cluster membership;
- [ ] complaint or RIK decision linked to the station;
- [ ] scanned-protocol or arithmetic issue;
- [ ] large electoral impact.

Suggested categories:

- [ ] `0 = normal/no flag`
- [ ] `1 = mild statistical outlier`
- [ ] `2 = strong statistical outlier`
- [ ] `3 = strong outlier with administrative/protocol corroboration`
- [ ] `4 = high-impact unresolved anomaly needing manual/legal review`

---

## 8. Outputs

### 8.1 Data Files

- [ ] `data/processed/polling_stations_2026.csv`
- [ ] `data/processed/historical_baselines.csv`
- [ ] `outputs/tables/anomaly_scores.csv`
- [ ] `outputs/tables/suspicious_stations.csv`
- [ ] `outputs/tables/protocol_review_sample.csv`

### 8.2 Figures

- [ ] national turnout histogram;
- [ ] Progressive Bulgaria vote-share histogram;
- [ ] turnout vs Progressive Bulgaria share scatterplot;
- [ ] same scatterplots by region;
- [ ] historical turnout change map;
- [ ] historical vote-share swing map;
- [ ] voting-method comparison plots;
- [ ] anomaly cluster maps;
- [ ] ranked stations by anomaly score and electoral impact.

### 8.3 Report

- [ ] Executive summary with cautious language.
- [ ] Data sources and reproducibility notes.
- [ ] Validation results proving official totals were reproduced.
- [ ] Main findings.
- [ ] Strongest anomalous stations/clusters.
- [ ] Tests that found no suspicious pattern.
- [ ] Limitations and false-positive risks.
- [ ] Appendix with station-level evidence links.

The report must be able to conclude either:

- [ ] "There are statistically meaningful anomalies requiring further review"; or
- [ ] "We do not find meaningful statistical evidence of fraud in the available data."

---

## 9. Implementation Plan

### 9.1 Scripts

- [ ] `src/fetch_cik_data.py`
  - [ ] download CIK open data;
  - [ ] store checksums and source metadata.
- [ ] `src/fetch_historical_data.py`
  - [ ] download prior CIK election data.
- [ ] `src/fetch_rik_decisions.py`
  - [ ] collect RIK/CIK decisions and complaints.
- [ ] `src/preprocess.py`
  - [ ] normalize station, party, and geography data.
- [ ] `src/validate_totals.py`
  - [ ] reproduce official totals and fail loudly on mismatch.
- [ ] `src/build_baselines.py`
  - [ ] create historical comparison features.
- [ ] `src/analyze_turnout_share.py`
  - [ ] turnout/share regressions and plots.
- [ ] `src/analyze_voting_method.py`
  - [ ] machine/paper/machine-failure comparisons.
- [ ] `src/analyze_spatial.py`
  - [ ] maps and cluster tests.
- [ ] `src/score_anomalies.py`
  - [ ] explainable station-level anomaly scores.
- [ ] `src/review_protocols.py`
  - [ ] sample and track manual protocol checks.
- [ ] `src/build_report.py`
  - [ ] generate HTML/Markdown report.

### 9.2 Tests

- [ ] Unit tests for parsers and numeric conversions.
- [ ] Regression tests for official aggregate totals.
- [ ] Tests for impossible values and missing IDs.
- [ ] Snapshot tests for generated anomaly-score schemas.
- [ ] Reproducibility test that rebuilds processed data from raw files.

---

## 10. Evidence Standards

Use this language discipline throughout the project:

- [ ] "Anomalous" means statistically unusual, not fraudulent.
- [ ] "Suspicious" requires more than one independent signal.
- [ ] "Evidence of fraud" requires corroborating administrative, protocol, witness, legal, or physical evidence beyond statistics.
- [ ] A surprising national result is not itself evidence of fraud.
- [ ] Polling misses are context, not proof.
- [ ] Negative findings should be reported clearly.

---

## 11. First Milestone

- [ ] Initialize repository.
- [ ] Add Python project structure.
- [ ] Download 2026 CIK open data.
- [ ] Parse polling-station results.
- [ ] Reproduce official national and regional totals.
- [ ] Produce the first turnout vs Progressive Bulgaria share plot.
- [ ] Write a short note stating whether the raw official data imported cleanly.
