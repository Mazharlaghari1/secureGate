from fastapi import APIRouter, Depends, Query, status
from pymongo.database import Database
from typing import Optional, List
from app.database import get_db
from app.schemas.base import SuccessResponse
from app.schemas.entities import UserResponse
from app.schemas.users import StaffCreate, StaffUpdate
from app.security.auth import require_admin
from app.utils.objectid import str_to_object_id
from app.services.users import (
    create_staff_user,
    list_staff_users,
    get_staff_by_id,
    update_staff_user,
    deactivate_staff_user,
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/users", tags=["Staff Management"])

class StaffSingleResponse(BaseModel):
    success: bool = True
    data: UserResponse

class StaffListResponse(BaseModel):
    success: bool = True
    data: List[UserResponse]
    page: int
    page_size: int
    total: int

@router.post("/staff", response_model=StaffSingleResponse, status_code=status.HTTP_201_CREATED)
def post_staff(
    payload: StaffCreate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Creates a new staff member account. Force role to staff and lowercase email.
    Checks uniqueness constraints and triggers a STAFF_CREATE audit log.
    """
    staff = create_staff_user(db, current_admin, payload.name, payload.email, payload.password)
    return {
        "success": True,
        "data": staff
    }

@router.get("/staff", response_model=StaffListResponse)
def get_staff(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Lists staff members with search query filters and page indexing.
    """
    result = list_staff_users(db, page, page_size, search, is_active)
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }

@router.get("/staff/{id}", response_model=StaffSingleResponse)
def get_staff_detail(
    id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Retrieves safe detail fields for a single staff member by ObjectId.
    """
    obj_id = str_to_object_id(id)
    staff = get_staff_by_id(db, obj_id)
    return {
        "success": True,
        "data": staff
    }

@router.put("/staff/{id}", response_model=StaffSingleResponse)
def put_staff(
    id: str,
    payload: StaffUpdate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Updates details of a staff member. Does not permit role changes.
    """
    obj_id = str_to_object_id(id)
    staff = update_staff_user(
        db=db,
        current_admin=current_admin,
        user_id=obj_id,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        is_active=payload.is_active
    )
    return {
        "success": True,
        "data": staff
    }

@router.delete("/staff/{id}", response_model=SuccessResponse)
def delete_staff(
    id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Deactivates a staff member setting is_active to false. Prevents admins deactivating themselves.
    """
    obj_id = str_to_object_id(id)
    result = deactivate_staff_user(db, current_admin, obj_id)
    return {
        "success": True,
        "data": result
    }
