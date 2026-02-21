from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from backend.core.audit_models import AuditLogEntry, AuditSummary
from backend.core.audit_logger import AuditLogger
from backend.core.audit_store import AuditStore

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Log Inspector"])

# Instantiate the singletons. In a real app we might use Dependency Injection deeper,
# but since this epic is self-contained initially we initialize here.
_audit_store = AuditStore(log_dir="logs")
_audit_logger = AuditLogger(store=_audit_store)

def get_audit_logger() -> AuditLogger:
    return _audit_logger

def get_audit_store() -> AuditStore:
    return _audit_store

@router.get("/logs/summary", response_model=AuditSummary)
async def get_summary(logger: AuditLogger = Depends(get_audit_logger)):
    """Aggregated log statistics."""
    return logger.get_summary()

@router.get("/logs/export", response_class=JSONResponse)
async def export_logs(
    date_from: date = Query(..., description="Start of date range (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End of date range (YYYY-MM-DD)"),
    logger: AuditLogger = Depends(get_audit_logger)
):
    """Export logs as a JSON file."""
    # We use a custom response because export_logs returns a stringified JSON blob
    json_str = logger.export_logs(date_from, date_to)
    import json
    parsed = json.loads(json_str) # Decode memory block and wrap as response
    return JSONResponse(
        content=parsed,
        headers={"Content-Disposition": f"attachment; filename=audit_logs_{date_from}_to_{date_to}.json"}
    )

@router.delete("/logs/purge")
async def purge_logs(
    before_date: datetime = Query(..., description="Purge logs older than this date (ISO 8601)"),
    store: AuditStore = Depends(get_audit_store)
):
    """Purge logs older than a retention period."""
    deleted_files = store.purge_logs(before_date)
    return {"status": "success", "message": f"Purged logs before {before_date}. Files deleted: {deleted_files}"}

@router.get("/logs/transaction/{transaction_id}", response_model=List[AuditLogEntry])
async def get_logs_for_transaction(
    transaction_id: str,
    logger: AuditLogger = Depends(get_audit_logger)
):
    """Get all logs for a transaction."""
    return logger.get_logs_for_transaction(transaction_id)

@router.get("/logs/{log_id}", response_model=AuditLogEntry)
async def get_log(
    log_id: str,
    store: AuditStore = Depends(get_audit_store)
):
    """Get specific log entry."""
    logs = store.get_all_logs()
    for log in logs:
        if log.log_id == log_id:
            return log
    raise HTTPException(status_code=404, detail="Log not found")

@router.get("/logs", response_model=Dict[str, Any])
async def list_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    decision: Optional[str] = Query(None, description="Filter by decision outcome"),
    transaction_id: Optional[str] = Query(None, description="Filter by transaction"),
    date_from: Optional[datetime] = Query(None, description="Start of date range"),
    date_to: Optional[datetime] = Query(None, description="End of date range"),
    source: Optional[str] = Query(None, description="Filter by source system"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    store: AuditStore = Depends(get_audit_store)
):
    """List audit logs (paginated, filterable)."""
    results, total_count = store.query_logs(
        event_type=event_type,
        severity=severity,
        decision=decision,
        transaction_id=transaction_id,
        date_from=date_from,
        date_to=date_to,
        source=source,
        page=page,
        page_size=page_size
    )
    return {
        "items": results,
        "total": total_count,
        "page": page,
        "page_size": page_size
    }
