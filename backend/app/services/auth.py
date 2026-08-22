from fastapi import HTTPException, status
from pymongo.database import Database
from app.security.auth import verify_password, create_access_token
from app.services.audit import log_audit
from app.models.constants import AuditStatus

def authenticate_user(db: Database, email: str, password: str) -> dict:
    """
    Authenticates a user by checking email and verifying password hash.
    Generates a JWT on success. Audit logs are written for both success and failure.
    Throws a generic 401 AUTHENTICATION_FAILED exception on any credentials mismatch.
    """
    email_normalized = email.strip().lower()
    
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "code": "AUTHENTICATION_FAILED",
            "message": "Invalid email or credentials."
        }
    )

    user = db.users.find_one({"email": email_normalized})
    if not user:
        # Audit login failure without revealing that user doesn't exist
        log_audit(
            db=db,
            action="USER_LOGIN",
            actor_id=None,
            actor_email=email_normalized,
            target_type="user",
            target_id=None,
            status=AuditStatus.FAILURE,
            metadata={"reason": "User not found"}
        )
        raise auth_exception

    if not user.get("is_active", True):
        log_audit(
            db=db,
            action="USER_LOGIN",
            actor_id=user["_id"],
            actor_email=user["email"],
            target_type="user",
            target_id=user["_id"],
            status=AuditStatus.FAILURE,
            metadata={"reason": "Account is deactivated"}
        )
        raise auth_exception

    if not verify_password(password, user["password_hash"]):
        log_audit(
            db=db,
            action="USER_LOGIN",
            actor_id=user["_id"],
            actor_email=user["email"],
            target_type="user",
            target_id=user["_id"],
            status=AuditStatus.FAILURE,
            metadata={"reason": "Password mismatch"}
        )
        raise auth_exception

    # Generate JWT
    token = create_access_token(data={
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    })

    # Log successful audit
    log_audit(
        db=db,
        action="USER_LOGIN",
        actor_id=user["_id"],
        actor_email=user["email"],
        target_type="user",
        target_id=user["_id"],
        status=AuditStatus.SUCCESS
    )

    return {
        "token": token,
        "user": user
    }
