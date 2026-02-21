# Epic 6 — Visualization & Dashboard

> **Priority:** P1  
> **Estimated Effort:** 3–4 days  
> **Dependencies:** Epic 1 (Data), Epic 4 (Validation Engine)  
> **Owner:** Frontend / Data Visualization Engineer

---

## 1. Objective

Build a visualization suite and dashboard presenting risk scores, validation results, and revenue leakage metrics using matplotlib (strict rules: one chart per plot, no subplot grids).

---

## 2. Required Charts

### Chart 1 — Risk Score Distribution (Histogram)

- X-axis: Risk Score (0–100), Y-axis: Transaction count
- 20 bins, color zones: Safe (green), Monitor (yellow), Critical (red)
- Mean and median annotation lines

### Chart 2 — Revenue Leakage Prevention (Grouped Bar)

- Categories: Before Automation vs After Engine
- Metrics: Manual Review Time (40→8 hrs, -80%), Error Detection Rate (35→94%, +169%), Audit Visibility (20→98%, +390%)

### Chart 3 — Validation Result Breakdown (Donut)

- Segments: Passed (green), Warning (amber), Failed (red)
- Center text: total transaction count

### Chart 4 — Leakage by Category (Horizontal Bar)

- Categories: Pricing Drift, Missing Invoice, Duplicate Invoice, Unauthorized Discount, Payment Mismatch, Stale Invoice

### Chart 5 — Risk Score Over Time (Line Chart)

- Monthly average risk score with Safe/Monitor/Critical zone bands

---

## 3. Interactive Dashboard

Single-page dashboard with:

| Section | Content |
|---|---|
| Header | Project title, last scan timestamp, health indicator |
| KPI Cards | Total transactions, Pass rate, Avg risk score, Critical count |
| Charts | All 5 charts embedded |
| Table | Sortable high-risk transaction listing |

---

## 4. File Structure

```
frontend/dashboard/
  risk_visualization.py
  transaction_viewer.py

visualization/
  leakage_chart.py
  risk_distribution_chart.py
  validation_results_chart.py
  chart_config.py
  chart_exporter.py
```

---

## 5. Acceptance Criteria

- [ ] All 5 charts render correctly with validation data
- [ ] Strict rules followed (one chart per plot, no subplots, no hardcoded colors)
- [ ] Charts exported as 150 DPI PNG files
- [ ] Dashboard displays all charts, KPIs, and transaction table
- [ ] Visualizations are client-presentation-ready

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_risk_histogram` | Correct bin counts with known data |
| `test_donut_percentages` | Correct labels for known pass/warn/fail counts |
| `test_chart_export` | File exists and size > 0 after save |
| `test_no_subplots` | All figures have exactly 1 axes object |
| `test_dashboard_loads` | HTTP 200 and required sections present |

---

## 7. Integration Points

- **← Epic 4:** Validation results and risk scores
- **← Epic 5:** Audit log summaries
- **← Epic 1:** Synthetic data statistics

## 8. Out of Scope

- Real-time WebSocket updates, interactive drill-down, PDF reports, email alerting
