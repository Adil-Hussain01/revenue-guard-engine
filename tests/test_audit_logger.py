import pytest
from datetime import datetime, date, timedelta, timezone
import os
import json
import uuid

from backend.core.audit_logger import AuditLogger
from backend.core.audit_store import AuditStore
from backend.core.audit_models import AuditLogEntry, RuleResult, ValidationResult

@pytest.fixture
def mock_store_path(tmp_path):
    """Fixture providing a temporary directory for audit storage."""
    return str(tmp_path / "logs")

@pytest.fixture
def audit_store(mock_store_path):
    """Fixture to provide a real or mock audit store."""
    store = AuditStore(log_dir=mock_store_path)
    return store

@pytest.fixture
def audit_logger(audit_store):
    """Fixture to provide the AuditLogger instance."""
    return AuditLogger(store=audit_store)


class TestAuditLogger:

    def test_log_creation(self, audit_logger):
        """Log an event -> assert it's retrievable by log_id"""
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type="validation_started",
            transaction_id="TX-001",
            source="test"
        )
        log_id = audit_logger.log_event(entry)
        
        logs = audit_logger.get_logs_for_transaction("TX-001")
        assert len(logs) == 1
        assert logs[0].log_id == log_id

    def test_correlation_grouping(self, audit_logger):
        """Log 5 events with same correlation_id -> assert all returned together"""
        corr_id = str(uuid.uuid4())
        for i in range(5):
            entry = AuditLogEntry(
                log_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="rule_evaluated",
                transaction_id=f"TX-{i}",
                source="test",
                correlation_id=corr_id
            )
            audit_logger.log_event(entry)
            
        logs = audit_logger.store.get_by_correlation(corr_id)
        assert len(logs) == 5
        assert all(log.correlation_id == corr_id for log in logs)

    def test_transaction_lookup(self, audit_logger):
        """Log events for transaction -> query by transaction_id -> assert complete"""
        tx_id = "TX-999"
        audit_logger.log_validation_start(tx_id, "CORR-999")
        
        rule_res = RuleResult(rule_id="R1", rule_name="Test Rule", passed=True)
        audit_logger.log_rule_result(tx_id, "R1", rule_res, "CORR-999")
        
        audit_logger.log_risk_score(tx_id, 10, "safe", "CORR-999")
        
        logs = audit_logger.get_logs_for_transaction(tx_id)
        assert len(logs) == 3
        event_types = {log.event_type for log in logs}
        assert "validation_started" in event_types
        assert "rule_evaluated" in event_types
        assert "risk_score_calculated" in event_types

    def test_filter_by_severity(self, audit_logger):
        """Log mixed severity events -> filter by 'critical' -> assert only critical"""
        for sev in ["low", "medium", "critical", "critical", "high"]:
            entry = AuditLogEntry(
                log_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                event_type="system_error",
                transaction_id="TX-ERR",
                source="test",
                severity=sev
            )
            audit_logger.log_event(entry)
            
        logs, count = audit_logger.store.query_logs(severity="critical")
        assert count == 2
        assert all(log.severity == "critical" for log in logs)

    def test_date_range_filter(self, audit_logger):
        """Filter logs by date range -> assert correct boundaries"""
        # Log events on different days
        for day in [14, 15, 16, 17, 18]:
            entry = AuditLogEntry(
                log_id=str(uuid.uuid4()),
                timestamp=datetime(2025, 1, day, 12, 0, 0, tzinfo=timezone.utc),
                event_type="order_created",
                transaction_id="TX-DATE",
                source="test"
            )
            audit_logger.log_event(entry)
            
        date_from = datetime(2025, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        date_to = datetime(2025, 1, 17, 23, 59, 59, tzinfo=timezone.utc)
        
        logs, count = audit_logger.store.query_logs(date_from=date_from, date_to=date_to)
        assert count == 3
        days = {log.timestamp.day for log in logs}
        assert days == {15, 16, 17}

    def test_file_persistence(self, mock_store_path):
        """Log events -> restart store -> assert events still queryable"""
        # Store 1
        store1 = AuditStore(log_dir=mock_store_path)
        logger1 = AuditLogger(store=store1)
        
        entry = AuditLogEntry(
            log_id="PERSIST-123",
            timestamp=datetime.now(timezone.utc),
            event_type="invoice_created",
            transaction_id="TX-PERSIST",
            source="test"
        )
        logger1.log_event(entry)
        
        # Store 2 (simulating restart)
        store2 = AuditStore(log_dir=mock_store_path)
        logger2 = AuditLogger(store=store2)
        
        logs = logger2.get_logs_for_transaction("TX-PERSIST")
        assert len(logs) == 1
        assert logs[0].log_id == "PERSIST-123"

    def test_summary_accuracy(self, audit_logger):
        """Log known events -> assert summary counts match"""
        audit_logger.log_risk_score("TX-A", 90, "critical", "CORR-A")
        audit_logger.log_risk_score("TX-B", 10, "safe", "CORR-B")
        
        res = ValidationResult(transaction_id="TX-C", decision="fail", risk_score=100, risk_classification="critical", rule_results=[])
        audit_logger.log_validation_complete("TX-C", res, "CORR-C")
        
        summary = audit_logger.get_summary()
        assert summary.total_events == 3
        assert summary.events_by_type["risk_score_calculated"] == 2
        assert summary.events_by_type["validation_completed"] == 1
        assert summary.events_by_decision.get("fail") == 1

    def test_export(self, audit_logger):
        """Export logs -> parse output -> assert valid JSON"""
        target_date = date(2025, 5, 5)
        entry = AuditLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime(2025, 5, 5, 12, 0, 0, tzinfo=timezone.utc),
            event_type="payment_recorded",
            transaction_id="TX-EXP",
            source="test"
        )
        audit_logger.log_event(entry)
        
        export_json = audit_logger.export_logs(date_from=target_date, date_to=target_date)
        parsed = json.loads(export_json)
        
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["transaction_id"] == "TX-EXP"
