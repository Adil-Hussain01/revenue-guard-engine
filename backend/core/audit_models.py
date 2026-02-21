from datetime import datetime
from typing import Literal, Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field

class RuleResult(BaseModel):
    """Result of a single rule evaluation."""
    rule_id: str
    rule_name: str
    passed: bool
    drift: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class ValidationResult(BaseModel):
    """Aggregate result of a validation run on a transaction."""
    transaction_id: str
    decision: Literal["pass", "warn", "fail", "block"]
    risk_score: int
    risk_classification: str
    rule_results: List[RuleResult] = Field(default_factory=list)

class AuditSummary(BaseModel):
    """Aggregate statistical summary of audit logs."""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_severity: Dict[str, int]
    events_by_decision: Dict[str, int]
    date_range: Dict[str, str]

class AuditLogEntry(BaseModel):
    """A generic audit log event entry for the system."""
    model_config = ConfigDict(extra="ignore")

    log_id: str                          
    timestamp: datetime                  
    event_type: Literal[
        "validation_started",
        "rule_evaluated",
        "rule_violation",
        "risk_score_calculated",
        "validation_completed",
        "order_created",
        "invoice_created",
        "payment_recorded",
        "system_startup",
        "system_shutdown",
        "system_error"
    ]
    transaction_id: Optional[str] = None                  
    rule_id: Optional[str] = None               
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[int] = None
    risk_classification: Optional[str] = None
    decision: Optional[Literal["pass", "warn", "fail", "block"]] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    source: str                          
    correlation_id: Optional[str] = None        
