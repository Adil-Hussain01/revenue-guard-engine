# Epic 5 — Audit Logging System

> **Priority:** P1 (Core)  
> **Estimated Effort:** 2–3 days  
> **Dependencies:** None (can be built independently, consumed by Epic 4)  
> **Owner:** Backend Engineer

---

## 1. Objective

Build a structured, queryable audit logging system that records every validation event, rule evaluation, risk score decision, and system action. This provides the **audit trail** required for compliance-grade transparency and the data backbone for the Audit Log Inspector in the OpenAPI Playground.

---

## 2. Business Context

In enterprise finance operations, every automated decision must be traceable. Auditors and compliance teams need to answer:

- **What happened?** — Which rules were triggered?
- **Why?** — What data caused the violation?
- **When?** — Exact timestamp of the decision
- **What was the outcome?** — Was the transaction approved, flagged, or blocked?

---

## 3. Functional Requirements

### 3.1 Audit Log Entry Schema

Every log entry must capture the following:

```python
class AuditLogEntry(BaseModel):
    log_id: str                          # UUID
    timestamp: datetime                  # ISO 8601
    event_type: Literal[
        "validation_started",
        "rule_evaluated",
        "rule_violation",
        "risk_score_calculated",
        "validation_completed",
        "order_created",
        "invoice_created",
        "payment_recorded",
        "system_error"
    ]
    transaction_id: str                  # order_id being processed
    rule_id: Optional[str]               # e.g., "PRC-001"
    rule_name: Optional[str]
    severity: Optional[str]
    risk_score: Optional[int]
    risk_classification: Optional[str]
    decision: Optional[Literal["pass", "warn", "fail", "block"]]
    details: dict                        # Flexible payload for additional context
    source: str                          # "validation_engine", "crm_api", "finance_api"
    correlation_id: Optional[str]        # Groups related events together
```

### 3.2 API Endpoints

Prefixed with `/api/v1/audit/`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/logs` | List audit logs (paginated, filterable) |
| `GET` | `/logs/{log_id}` | Get specific log entry |
| `GET` | `/logs/transaction/{transaction_id}` | Get all logs for a transaction |
| `GET` | `/logs/summary` | Aggregated log statistics |
| `GET` | `/logs/export` | Export logs as JSON file |
| `DELETE` | `/logs/purge` | Purge logs older than a retention period |

### 3.3 Filtering & Search

The `/logs` endpoint must support:

| Parameter | Type | Description |
|---|---|---|
| `event_type` | string | Filter by event type |
| `severity` | string | Filter by severity level |
| `decision` | string | Filter by decision outcome |
| `transaction_id` | string | Filter by transaction |
| `date_from` | datetime | Start of date range |
| `date_to` | datetime | End of date range |
| `source` | string | Filter by source system |
| `page` | int | Page number |
| `page_size` | int | Items per page |

### 3.4 Storage

- **Primary store:** Structured JSON files on disk (one file per day)
- **In-memory index:** Fast lookup by `transaction_id` and `correlation_id`
- **File naming:** `audit_logs_YYYY-MM-DD.json`
- **Retention:** Configurable (default: 90 days)

---

## 4. Technical Design

### 4.1 File Structure

```
backend/
  core/
    audit_logger.py              # AuditLogger class — core logging interface
    audit_store.py               # File-based persistence + in-memory index
    audit_models.py              # Pydantic models for log entries
    __init__.py
  api/
    audit_controller.py          # FastAPI router for audit endpoints
```

### 4.2 Logger Interface

```python
class AuditLogger:
    """Central audit logging service."""

    def __init__(self, store: AuditStore): ...
    
    def log_event(self, entry: AuditLogEntry) -> str: ...
    def log_validation_start(self, transaction_id: str, correlation_id: str) -> None: ...
    def log_rule_result(self, transaction_id: str, rule_id: str, result: RuleResult, correlation_id: str) -> None: ...
    def log_risk_score(self, transaction_id: str, score: int, classification: str, correlation_id: str) -> None: ...
    def log_validation_complete(self, transaction_id: str, result: ValidationResult, correlation_id: str) -> None: ...
    
    def get_logs_for_transaction(self, transaction_id: str) -> list[AuditLogEntry]: ...
    def get_summary(self) -> AuditSummary: ...
    def export_logs(self, date_from: date, date_to: date) -> str: ...
```

### 4.3 Correlation IDs

Every validation run generates a unique `correlation_id` that links all events in that run:

```
correlation_id: "VAL-2026-0221-001"
  ├── validation_started (transaction_id: ORD-0042)
  ├── rule_evaluated (PRC-001 → pass)
  ├── rule_evaluated (PRC-002 → pass)
  ├── rule_violation (PRC-003 → fail, drift = 8%)
  ├── rule_evaluated (OIC-001 → pass)
  ├── risk_score_calculated (score: 30, classification: safe)
  └── validation_completed (decision: pass)
```

### 4.4 Summary Statistics

```json
{
  "total_events": 15420,
  "events_by_type": {
    "validation_completed": 1000,
    "rule_violation": 342,
    "risk_score_calculated": 1000
  },
  "events_by_severity": {
    "critical": 87,
    "high": 123,
    "medium": 132
  },
  "events_by_decision": {
    "pass": 712,
    "warn": 198,
    "fail": 90
  },
  "date_range": {
    "earliest": "2025-03-01T00:00:00Z",
    "latest": "2026-02-21T15:00:00Z"
  }
}
```

---

## 5. Acceptance Criteria

- [ ] AuditLogger records all validation events with complete metadata
- [ ] Correlation IDs correctly group related events
- [ ] Logs are persisted to structured JSON files on disk
- [ ] All query/filter endpoints work correctly
- [ ] Export endpoint produces downloadable JSON
- [ ] Purge endpoint correctly removes old logs
- [ ] Summary statistics are accurate
- [ ] Unit tests cover logging, querying, persistence, and edge cases

---

## 6. Testing Strategy

| Test | Description |
|---|---|
| `test_log_creation` | Log an event → assert it's retrievable by log_id |
| `test_correlation_grouping` | Log 5 events with same correlation_id → assert all returned together |
| `test_transaction_lookup` | Log events for transaction → query by transaction_id → assert complete |
| `test_filter_by_severity` | Log mixed severity events → filter by "critical" → assert only critical |
| `test_date_range_filter` | Filter logs by date range → assert correct boundaries |
| `test_file_persistence` | Log events → restart store → assert events still queryable |
| `test_summary_accuracy` | Log known events → assert summary counts match |
| `test_export` | Export logs → parse output → assert valid JSON |

---

## 7. Integration Points

| Direction | Counterpart | Description |
|---|---|---|
| **← Inbound** | Epic 4 | Receives validation events from the engine |
| **← Inbound** | Epic 2 | Optionally logs CRM API operations |
| **← Inbound** | Epic 3 | Optionally logs Finance API operations |
| **→ Outbound** | Epic 7 | Audit log inspection in the playground |
| **→ Outbound** | Epic 6 | Audit event data for dashboard |

---

## 8. Out of Scope

- Database-backed storage (e.g., PostgreSQL)
- Log streaming to external services (e.g., ELK, Datadog)
- Role-based access control for log viewing
- Log encryption at rest
