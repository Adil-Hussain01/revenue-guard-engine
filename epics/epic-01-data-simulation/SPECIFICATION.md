# Epic 1 — Data Simulation & Synthetic Dataset Generation

> **Priority:** P0 (Foundation)  
> **Estimated Effort:** 3–4 days  
> **Dependencies:** None — this is the foundational epic  
> **Owner:** Backend Engineer

---

## 1. Objective

Build a synthetic enterprise dataset generator that produces realistic transactional data simulating the pipeline between a CRM system (GoHighLevel) and an Accounting system (QuickBooks). The dataset must include intentional anomalies and business noise to power the validation and risk-scoring epics downstream.

---

## 2. Business Context

Real-world revenue leakage stems from subtle data inconsistencies across systems. To demonstrate detection capabilities without access to live APIs, we need a high-fidelity synthetic dataset that mirrors production-grade data quality issues:

- **Missing records** — invoices that were never created for completed orders
- **Pricing drift** — unit prices that silently change between order and invoice
- **Duplicate billing** — the same order invoiced more than once
- **Unauthorized discounts** — discounts exceeding the 15% approval threshold
- **Payment status mismatches** — orders marked paid in CRM but unpaid in finance

---

## 3. Functional Requirements

### 3.1 Dataset Volume & Shape

| Attribute | Requirement |
|---|---|
| Minimum transactions | 1,000 |
| Contacts / Customers | ~200 unique |
| Products / Line Items | ~50 SKUs |
| Date range | Rolling 12 months |
| Output format | JSON + CSV |

### 3.2 CRM-Side Data Entities

Each generated transaction must produce:

| Entity | Key Fields |
|---|---|
| **Contact** | `contact_id`, `name`, `email`, `company`, `created_at` |
| **Deal** | `deal_id`, `contact_id`, `stage`, `value`, `assigned_to`, `created_at` |
| **Opportunity** | `opportunity_id`, `deal_id`, `product_id`, `quantity`, `unit_price`, `discount_pct`, `approval_status` |
| **Order** | `order_id`, `opportunity_id`, `contact_id`, `total_amount`, `discount_applied`, `order_date`, `status` |

### 3.3 Finance-Side Data Entities

| Entity | Key Fields |
|---|---|
| **Invoice** | `invoice_id`, `order_id`, `amount_due`, `amount_paid`, `status`, `issue_date`, `due_date` |
| **Payment** | `payment_id`, `invoice_id`, `amount`, `payment_method`, `payment_date`, `status` |
| **Ledger Entry** | `entry_id`, `invoice_id`, `debit`, `credit`, `account`, `posted_date` |

### 3.4 Anomaly Injection Rules

The generator must inject anomalies at configurable rates (defaults shown):

| Anomaly Type | Default Rate | Description |
|---|---|---|
| Missing Invoice | 5% | Order exists in CRM, no matching invoice in finance |
| Pricing Drift | 8% | Invoice amount differs from order amount by > 1% |
| Duplicate Invoice | 3% | Same `order_id` linked to 2+ invoices |
| Unauthorized Discount | 6% | `discount_pct > 15%` with `approval_status != "approved"` |
| Payment Mismatch | 4% | `invoice.status = "paid"` but `payment.amount < invoice.amount_due` |
| Stale Unpaid | 5% | Invoice older than 60 days with `status = "unpaid"` |

### 3.5 Configurability

All parameters must be configurable via a single `config` dictionary or YAML file:

```python
GENERATOR_CONFIG = {
    "num_transactions": 1000,
    "num_contacts": 200,
    "num_products": 50,
    "date_range_months": 12,
    "anomaly_rates": {
        "missing_invoice": 0.05,
        "pricing_drift": 0.08,
        "duplicate_invoice": 0.03,
        "unauthorized_discount": 0.06,
        "payment_mismatch": 0.04,
        "stale_unpaid": 0.05,
    },
    "seed": 42,  # reproducibility
}
```

### 3.6 Reproducibility

- Accept a `seed` parameter for deterministic generation.
- Same seed + same config = byte-identical output.

---

## 4. Technical Design

### 4.1 File Structure

```
backend/
  data/
    synthetic_data_generator.py   # Main generator class
    config.py                     # Default configuration
    models.py                     # Pydantic data models for all entities
    anomaly_injector.py           # Anomaly injection logic
    __init__.py
```

### 4.2 Class Design

```python
class SyntheticDataGenerator:
    """Orchestrates end-to-end dataset generation."""

    def __init__(self, config: dict): ...
    def generate(self) -> GeneratedDataset: ...
    def save(self, path: str, formats: list[str] = ["json", "csv"]): ...

class AnomalyInjector:
    """Applies business-realistic anomalies to clean data."""

    def __init__(self, rates: dict, rng: Random): ...
    def inject(self, dataset: GeneratedDataset) -> GeneratedDataset: ...

@dataclass
class GeneratedDataset:
    contacts: list[Contact]
    deals: list[Deal]
    opportunities: list[Opportunity]
    orders: list[Order]
    invoices: list[Invoice]
    payments: list[Payment]
    ledger_entries: list[LedgerEntry]
    anomaly_manifest: list[AnomalyRecord]  # ground truth for testing
```

### 4.3 Key Libraries

| Library | Purpose |
|---|---|
| `Faker` | Realistic names, emails, companies |
| `random` / `numpy` | Statistical distributions for amounts, dates |
| `Pydantic` | Data model validation |
| `pandas` | CSV export |

### 4.4 Anomaly Manifest

Every injected anomaly is recorded in an `anomaly_manifest` list with:

```json
{
  "anomaly_id": "ANO-0042",
  "type": "pricing_drift",
  "affected_entity": "invoice",
  "entity_id": "INV-0312",
  "related_entity_id": "ORD-0312",
  "expected_value": 1500.00,
  "actual_value": 1620.00,
  "drift_pct": 8.0,
  "injected_at": "2026-02-21T12:00:00Z"
}
```

This manifest serves as **ground truth** for validating the detection engine in Epic 4.

---

## 5. Acceptance Criteria

- [ ] Generator produces ≥ 1,000 transactions with all required entity types
- [ ] Anomalies are injected at configurable, verifiable rates
- [ ] Output is available in both JSON and CSV formats
- [ ] Anomaly manifest is generated as a separate JSON file for validation
- [ ] Generator is deterministic when given the same seed
- [ ] All data models pass Pydantic validation
- [ ] Code is fully documented with business-context comments
- [ ] Unit tests cover generation, anomaly injection, and edge cases

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_volume` | Assert ≥ 1,000 transactions generated |
| `test_anomaly_rates` | Assert injected anomaly counts within ±2% of configured rates |
| `test_determinism` | Generate twice with same seed, assert identical output |
| `test_entity_integrity` | All foreign keys (e.g., `order_id` in invoice) reference valid entities |
| `test_date_ranges` | All dates fall within configured 12-month window |
| `test_export_formats` | JSON and CSV files are valid and parseable |

---

## 7. Downstream Dependencies

| Consuming Epic | What It Needs |
|---|---|
| Epic 2 (CRM Layer) | Contacts, Deals, Opportunities, Orders |
| Epic 3 (Finance Layer) | Invoices, Payments, Ledger Entries |
| Epic 4 (Validation Engine) | Full dataset + anomaly manifest for accuracy benchmarking |
| Epic 6 (Visualization) | Aggregated statistics for charts |

---

## 8. Out of Scope

- Real API connections (handled in Epic 2 and Epic 3)
- Streaming / real-time generation
- UI for configuring the generator
