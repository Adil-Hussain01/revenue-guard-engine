import json
import uuid
from datetime import datetime, date, timezone
from typing import List

from backend.core.audit_models import AuditLogEntry, AuditSummary, RuleResult, ValidationResult
from backend.core.audit_store import AuditStore


class AuditLogger:
    """Central audit logging service."""

    def __init__(self, store: AuditStore):
        self.store = store

    def log_event(self, entry: AuditLogEntry) -> str:
        """Logs a raw event and returns the log_id."""
        if not entry.log_id:
            entry.log_id = str(uuid.uuid4())
        self.store.save_log(entry)
        return entry.log_id

    def log_validation_start(self, transaction_id: str, correlation_id: str) -> None:
        """Logs the start of a validation run."""
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type="validation_started",
            transaction_id=transaction_id,
            source="validation_engine",
            correlation_id=correlation_id
        )
        self.log_event(entry)

    def log_rule_result(self, transaction_id: str, rule_id: str, result: RuleResult, correlation_id: str) -> None:
        """Logs the result of a single rule evaluation."""
        decision_map = {True: "pass", False: "fail"}
        details = result.details.copy()
        if result.drift is not None:
            details["drift"] = result.drift
            
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type="rule_evaluated" if result.passed else "rule_violation",
            transaction_id=transaction_id,
            rule_id=rule_id,
            rule_name=result.rule_name,
            decision=decision_map[result.passed],
            details=details,
            source="validation_engine",
            correlation_id=correlation_id
        )
        self.log_event(entry)

    def log_risk_score(self, transaction_id: str, score: int, classification: str, correlation_id: str) -> None:
        """Logs the final computed risk score for a transaction."""
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type="risk_score_calculated",
            transaction_id=transaction_id,
            risk_score=score,
            risk_classification=classification,
            source="validation_engine",
            correlation_id=correlation_id
        )
        self.log_event(entry)

    def log_validation_complete(self, transaction_id: str, result: ValidationResult, correlation_id: str) -> None:
        """Logs the completion of a validation run and the final decision."""
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type="validation_completed",
            transaction_id=transaction_id,
            risk_score=result.risk_score,
            risk_classification=result.risk_classification,
            decision=result.decision,
            source="validation_engine",
            correlation_id=correlation_id
        )
        self.log_event(entry)

    def get_logs_for_transaction(self, transaction_id: str) -> List[AuditLogEntry]:
        """Retrieve all logs for a specific transaction."""
        return self.store.get_by_transaction(transaction_id)

    def get_summary(self) -> AuditSummary:
        """Compute an overview of the audit traces."""
        logs = self.store.get_all_logs()
        
        events_by_type = {}
        events_by_severity = {}
        events_by_decision = {}
        
        earliest_date = None
        latest_date = None

        for log in logs:
            events_by_type[log.event_type] = events_by_type.get(log.event_type, 0) + 1
            if log.severity:
                events_by_severity[log.severity] = events_by_severity.get(log.severity, 0) + 1
            if log.decision:
                events_by_decision[log.decision] = events_by_decision.get(log.decision, 0) + 1

            if earliest_date is None or log.timestamp < earliest_date:
                earliest_date = log.timestamp
            if latest_date is None or log.timestamp > latest_date:
                latest_date = log.timestamp

        date_range = {}
        if earliest_date:
            date_range["earliest"] = earliest_date.isoformat()
        if latest_date:
            date_range["latest"] = latest_date.isoformat()

        return AuditSummary(
            total_events=len(logs),
            events_by_type=events_by_type,
            events_by_severity=events_by_severity,
            events_by_decision=events_by_decision,
            date_range=date_range
        )

    def export_logs(self, date_from: date, date_to: date) -> str:
        """Exports logs to a JSON formatted string based on date."""
        dt_from = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
        dt_to = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        logs, _ = self.store.query_logs(date_from=dt_from, date_to=dt_to, page=1, page_size=1000000)
        
        # Helper to serialize datetimes
        def default_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
            
        export_data = [log.model_dump() for log in logs]
        return json.dumps(export_data, default=default_serializer, indent=2)
