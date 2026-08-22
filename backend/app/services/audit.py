from datetime import datetime
from bson import ObjectId
from typing import Optional, Any, Dict
from pymongo.database import Database
from app.models.constants import AuditStatus

def log_audit(
    db: Database,
    action: str,
    actor_id: Optional[ObjectId],
    actor_email: Optional[str],
    target_type: str,
    target_id: Optional[ObjectId],
    status: AuditStatus,
    metadata: Optional[Dict[str, Any]] = None
) -> ObjectId:
    """
    Synchronously creates an audit log entry in the MongoDB database.
    Ensures that passwords, secret tokens, and auth headers are automatically redacted.
    """
    clean_metadata = {}
    if metadata:
        # Define fields to redact
        redact_keys = {
            "password", "password_hash", "token", "secret", "jwt", 
            "authorization", "key", "access_token", "bearer", "authorization_header"
        }
        for k, v in metadata.items():
            if k.lower() in redact_keys:
                clean_metadata[k] = "[REDACTED]"
            else:
                clean_metadata[k] = v

    log_entry = {
        "actor_id": actor_id,
        "actor_email": actor_email,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "status": status.value if hasattr(status, "value") else status,
        "metadata": clean_metadata,
        "timestamp": datetime.utcnow()
    }
    
    result = db.audit_logs.insert_one(log_entry)
    return result.inserted_id

def list_audit_logs(
    db: Database,
    page: int = 1,
    page_size: int = 20,
    action: Optional[str] = None,
    status: Optional[str] = None
) -> dict:
    """
    Retrieves a paginated list of system audit logs, sorted newest first (Admin only).
    """
    query = {}
    if action:
        query["action"] = action
    if status:
        query["status"] = status

    skip = (page - 1) * page_size
    cursor = db.audit_logs.find(query).skip(skip).limit(page_size).sort("timestamp", -1)
    items = list(cursor)
    total = db.audit_logs.count_documents(query)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }
