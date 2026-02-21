import json
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Tuple

from backend.core.audit_models import AuditLogEntry


class AuditStore:
    """Handles file-based persistence and in-memory indexing of audit logs."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        
        # In-memory indexes
        self._logs_by_tx: Dict[str, List[AuditLogEntry]] = {}
        self._logs_by_corr: Dict[str, List[AuditLogEntry]] = {}
        self._all_logs: List[AuditLogEntry] = []
        
        self._load_all_logs()

    def _get_log_file_path(self, log_date: date) -> str:
        date_str = log_date.strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"audit_logs_{date_str}.json")

    def _load_all_logs(self):
        """Loads all logs from disk into memory on startup."""
        for filename in sorted(os.listdir(self.log_dir)):
            if filename.startswith("audit_logs_") and filename.endswith(".json"):
                filepath = os.path.join(self.log_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        for line in f:
                            if not line.strip():
                                continue
                            data = json.loads(line)
                            entry = AuditLogEntry(**data)
                            self._index_log(entry)
                except Exception as e:
                    # Depending on strictness, we might log this or raise
                    print(f"Error loading logs from {filepath}: {e}")

    def _index_log(self, entry: AuditLogEntry):
        """Indexes a single log entry into memory."""
        self._all_logs.append(entry)
        if entry.transaction_id:
            if entry.transaction_id not in self._logs_by_tx:
                self._logs_by_tx[entry.transaction_id] = []
            self._logs_by_tx[entry.transaction_id].append(entry)
            
        if entry.correlation_id:
            if entry.correlation_id not in self._logs_by_corr:
                self._logs_by_corr[entry.correlation_id] = []
            self._logs_by_corr[entry.correlation_id].append(entry)

    def save_log(self, entry: AuditLogEntry):
        """Saves a single log entry to disk and memory."""
        self._index_log(entry)
        
        filepath = self._get_log_file_path(entry.timestamp.date())
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def get_by_transaction(self, transaction_id: str) -> List[AuditLogEntry]:
        """Get all logs for a specific transaction_id."""
        return self._logs_by_tx.get(transaction_id, [])

    def get_by_correlation(self, correlation_id: str) -> List[AuditLogEntry]:
        """Get all logs for a specific correlation_id."""
        return self._logs_by_corr.get(correlation_id, [])

    def query_logs(self, 
                   event_type: Optional[str] = None,
                   severity: Optional[str] = None,
                   decision: Optional[str] = None,
                   transaction_id: Optional[str] = None,
                   date_from: Optional[datetime] = None,
                   date_to: Optional[datetime] = None,
                   source: Optional[str] = None,
                   page: int = 1,
                   page_size: int = 50) -> Tuple[List[AuditLogEntry], int]:
        """Queries logs with given filters and returns paginated results and total count."""
        results = self._all_logs

        if transaction_id:
            results = [log for log in results if log.transaction_id == transaction_id]
        if event_type:
            results = [log for log in results if log.event_type == event_type]
        if severity:
            results = [log for log in results if log.severity == severity]
        if decision:
            results = [log for log in results if log.decision == decision]
        if source:
            results = [log for log in results if log.source == source]
        if date_from:
            results = [log for log in results if log.timestamp >= date_from]
        if date_to:
            results = [log for log in results if log.timestamp <= date_to]

        # Sort descending by timestamp
        results = sorted(results, key=lambda x: x.timestamp, reverse=True)
        
        total_count = len(results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return results[start_idx:end_idx], total_count

    def get_all_logs(self) -> List[AuditLogEntry]:
        """Returns all logs in memory."""
        return self._all_logs

    def purge_logs(self, before_date: datetime) -> int:
        """Removes log entries older than the given date."""
        self._all_logs = [log for log in self._all_logs if log.timestamp >= before_date]
        
        # Rebuild indexes
        self._logs_by_tx.clear()
        self._logs_by_corr.clear()
        for log in self._all_logs:
            if log.transaction_id:
                if log.transaction_id not in self._logs_by_tx:
                    self._logs_by_tx[log.transaction_id] = []
                self._logs_by_tx[log.transaction_id].append(log)
            if log.correlation_id:
                if log.correlation_id not in self._logs_by_corr:
                    self._logs_by_corr[log.correlation_id] = []
                self._logs_by_corr[log.correlation_id].append(log)
                
        # Remove flat files completely if they are strictly older.
        date_cutoff = before_date.date()
        deleted_count = 0
        deleted_files = 0
        
        for filename in list(os.listdir(self.log_dir)):
            if filename.startswith("audit_logs_") and filename.endswith(".json"):
                # Extract date from filename audit_logs_YYYY-MM-DD.json
                date_str = filename[len("audit_logs_"):-len(".json")]
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if file_date < date_cutoff:
                        # Find how many lines are in here roughly, though it might be faster to just count how length dropped
                        filepath = os.path.join(self.log_dir, filename)
                        os.remove(filepath)
                        deleted_files += 1
                except ValueError:
                    continue

        return deleted_files  # In a robust system we'd return actual row count but this represents files deleted
