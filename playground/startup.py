"""
Application Lifecycle Handlers
"""
from playground.app_config import settings
from backend.data.data_ingestor import DataIngestor
from backend.api.ghl_connector import get_store as get_crm_store
from backend.api.qb_engine import get_store as get_finance_store
from backend.api.audit_controller import get_audit_logger
from backend.core.audit_models import AuditLogEntry
import os
import uuid
from datetime import datetime, timezone

async def startup_event():
    """
    Seeds data stores with synthetic dataset if they are empty or configured to seed.
    """
    crm_store = get_crm_store()
    finance_store = get_finance_store()
    audit_logger = get_audit_logger()
    
    # Check if we should seed (e.g., if data dir is empty or explicitly requested)
    contacts_path = os.path.join(settings.DATA_DIR, "contacts.json")
    
    if not os.path.exists(contacts_path) or settings.SEED_ON_STARTUP:
        print(f"Ingesting production data to {settings.DATA_DIR}...")
        ingestor = DataIngestor()
        dataset = ingestor.generate()
        ingestor.save(dataset, output_dir=settings.DATA_DIR)
        
        # Reload stores
        crm_store.load_seed_data()
        finance_store._load_seed_data()
        
    audit_logger.log_event(AuditLogEntry(
        log_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        event_type="system_startup",
        severity="info",
        details={"message": "API Playground started and data stores initialized."},
        source="system"
    ))

async def shutdown_event():
    """
    Clean up or log shutdown.
    """
    audit_logger = get_audit_logger()
    audit_logger.log_event(AuditLogEntry(
        log_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        event_type="system_shutdown",
        severity="info",
        details={"message": "API Playground is shutting down."},
        source="system"
    ))
