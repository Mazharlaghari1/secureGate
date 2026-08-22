from datetime import datetime
from bson import ObjectId
from typing import Optional
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
from app.security.auth import hash_password
from app.services.audit import log_audit
from app.models.constants import AuditStatus, UserRole

def create_staff_user(db: Database, current_admin: dict, name: str, email: str, password: str) -> dict:
    """
    Creates a new staff member account. Force role to staff and lowercase email.
    Checks uniqueness constraints and triggers a STAFF_CREATE audit log.
    """
    email_normalized = email.strip().lower()
    
    existing = db.users.find_one({"email": email_normalized})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"User with email '{email_normalized}' already exists."
            }
        )
        
    password_hash = hash_password(password)
    
    staff_doc = {
        "name": name.strip(),
        "email": email_normalized,
        "password_hash": password_hash,
        "role": UserRole.STAFF.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = db.users.insert_one(staff_doc)
        staff_doc["_id"] = result.inserted_id
        
        log_audit(
            db=db,
            action="STAFF_CREATE",
            actor_id=current_admin["_id"],
            actor_email=current_admin["email"],
            target_type="user",
            target_id=result.inserted_id,
            status=AuditStatus.SUCCESS
        )
        
        return staff_doc
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"User with email '{email_normalized}' already exists."
            }
        )

def list_staff_users(
    db: Database,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> dict:
    """
    Lists staff members with query search (name/email), status filters, and pagination.
    """
    query = {"role": UserRole.STAFF.value}
    
    if is_active is not None:
        query["is_active"] = is_active
        
    if search:
        clean_search = search.strip()
        query["$or"] = [
            {"name": {"$regex": clean_search, "$options": "i"}},
            {"email": {"$regex": clean_search, "$options": "i"}}
        ]
        
    skip = (page - 1) * page_size
    cursor = db.users.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    items = list(cursor)
    total = db.users.count_documents(query)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }

def get_staff_by_id(db: Database, user_id: ObjectId) -> dict:
    """
    Retrieves detail fields for a single staff member by ObjectId.
    """
    user = db.users.find_one({"_id": user_id, "role": UserRole.STAFF.value})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Staff member not found."
            }
        )
    return user

def update_staff_user(
    db: Database,
    current_admin: dict,
    user_id: ObjectId,
    name: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    is_active: Optional[bool] = None
) -> dict:
    """
    Updates staff information. Normal staff update blocks role escalation.
    Audits the fields modified.
    """
    staff = db.users.find_one({"_id": user_id, "role": UserRole.STAFF.value})
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Staff member not found."
            }
        )
        
    update_data = {"updated_at": datetime.utcnow()}
    metadata = {}
    
    if name is not None:
        update_data["name"] = name.strip()
        metadata["name"] = name.strip()
        
    if email is not None:
        email_normalized = email.strip().lower()
        if email_normalized != staff["email"]:
            existing = db.users.find_one({"email": email_normalized})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "CONFLICT",
                        "message": f"User with email '{email_normalized}' already exists."
                    }
                )
            update_data["email"] = email_normalized
            metadata["email"] = email_normalized
            
    if password is not None:
        update_data["password_hash"] = hash_password(password)
        metadata["password"] = "[REDACTED]"
        
    if is_active is not None:
        # Prevent self-deactivation if target is the calling admin
        if user_id == current_admin["_id"] and is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "BAD_REQUEST",
                    "message": "Admins cannot deactivate themselves."
                }
            )
        update_data["is_active"] = is_active
        metadata["is_active"] = is_active

    db.users.update_one({"_id": user_id}, {"$set": update_data})
    updated_staff = db.users.find_one({"_id": user_id})
    
    log_audit(
        db=db,
        action="STAFF_UPDATE",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="user",
        target_id=user_id,
        status=AuditStatus.SUCCESS,
        metadata=metadata
    )
    
    return updated_staff

def deactivate_staff_user(db: Database, current_admin: dict, user_id: ObjectId) -> dict:
    """
    Deactivates a staff account setting is_active to false. Prevents self-deactivation.
    """
    staff = db.users.find_one({"_id": user_id, "role": UserRole.STAFF.value})
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": "Staff member not found."
            }
        )
        
    if not staff.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": "Staff member is already inactive."
            }
        )
        
    if user_id == current_admin["_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": "Admins cannot deactivate themselves."
            }
        )
        
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    log_audit(
        db=db,
        action="STAFF_DEACTIVATE",
        actor_id=current_admin["_id"],
        actor_email=current_admin["email"],
        target_type="user",
        target_id=user_id,
        status=AuditStatus.SUCCESS
    )
    
    return {"status": "deactivated"}

def create_attendee_user(db: Database, name: str, email: str, password: str) -> dict:
    """
    Creates a new attendee user account. Force role to attendee and lowercase email.
    Checks uniqueness constraints and triggers an ATTENDEE_REGISTER audit log.
    """
    email_normalized = email.strip().lower()
    
    existing = db.users.find_one({"email": email_normalized})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"User with email '{email_normalized}' already exists."
            }
        )
        
    password_hash = hash_password(password)
    
    attendee_doc = {
        "name": name.strip(),
        "email": email_normalized,
        "password_hash": password_hash,
        "role": UserRole.ATTENDEE.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = db.users.insert_one(attendee_doc)
        attendee_doc["_id"] = result.inserted_id
        
        log_audit(
            db=db,
            action="ATTENDEE_REGISTER",
            actor_id=result.inserted_id,
            actor_email=email_normalized,
            target_type="user",
            target_id=result.inserted_id,
            status=AuditStatus.SUCCESS
        )
        
        return attendee_doc
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CONFLICT",
                "message": f"User with email '{email_normalized}' already exists."
            }
        )
