from fastapi import APIRouter, Depends, Query, status, File, UploadFile, HTTPException
from pymongo.database import Database
from typing import Optional, List
from app.database import get_db
from app.schemas.base import SuccessResponse
from app.schemas.entities import ParticipantResponse
from app.schemas.participants import ParticipantCreate, ParticipantUpdate
from app.security.auth import require_admin, require_staff
from app.utils.objectid import str_to_object_id
from app.services.participants import (
    create_participant,
    list_participants,
    get_participant_by_id,
    update_participant,
    deactivate_participant,
    import_participants_csv,
)
from pydantic import BaseModel

router = APIRouter(tags=["Participant Management"])

class ParticipantSingleResponse(BaseModel):
    success: bool = True
    data: ParticipantResponse

class ParticipantListResponse(BaseModel):
    success: bool = True
    data: List[ParticipantResponse]
    page: int
    page_size: int
    total: int

@router.post("/api/events/{event_id}/participants", response_model=ParticipantSingleResponse, status_code=status.HTTP_201_CREATED)
def post_participant(
    event_id: str,
    payload: ParticipantCreate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Enrolls a participant in an event. Validates status bounds and capacity (Admin only).
    """
    event_obj_id = str_to_object_id(event_id)
    participant = create_participant(
        db=db,
        current_admin=current_admin,
        event_id=event_obj_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone
    )
    return {
        "success": True,
        "data": participant
    }

@router.get("/api/events/{event_id}/participants", response_model=ParticipantListResponse)
def get_participants(
    event_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Lists registered participants for a given event (Admin/Staff).
    """
    event_obj_id = str_to_object_id(event_id)
    result = list_participants(db, event_obj_id, page, page_size, search)
    return {
        "success": True,
        "data": result["items"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"]
    }

@router.get("/api/participants/{id}", response_model=ParticipantSingleResponse)
def get_participant_detail(
    id: str,
    current_user: dict = Depends(require_staff),
    db: Database = Depends(get_db)
):
    """
    Retrieves full details of a specific participant profile (Admin/Staff).
    """
    obj_id = str_to_object_id(id)
    participant = get_participant_by_id(db, obj_id)
    return {
        "success": True,
        "data": participant
    }

@router.put("/api/participants/{id}", response_model=ParticipantSingleResponse)
def put_participant(
    id: str,
    payload: ParticipantUpdate,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Updates details of a participant registration (Admin only).
    """
    obj_id = str_to_object_id(id)
    participant = update_participant(db, current_admin, obj_id, payload.model_dump(exclude_unset=True))
    return {
        "success": True,
        "data": participant
    }

@router.delete("/api/participants/{id}", response_model=SuccessResponse)
def delete_participant(
    id: str,
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Deactivates a participant's active registration status. Excludes hard deletions (Admin only).
    """
    obj_id = str_to_object_id(id)
    result = deactivate_participant(db, current_admin, obj_id)
    return {
        "success": True,
        "data": result
    }

class BulkImportResponseData(BaseModel):
    imported: int

class BulkImportResponse(BaseModel):
    success: bool = True
    data: BulkImportResponseData

@router.post("/api/events/{event_id}/participants/bulk", response_model=BulkImportResponse, status_code=status.HTTP_201_CREATED)
def post_participants_bulk(
    event_id: str,
    file: UploadFile = File(...),
    current_admin: dict = Depends(require_admin),
    db: Database = Depends(get_db)
):
    """
    Imports participants in bulk via a CSV file (Admin only, Max 2MB).
    """
    event_obj_id = str_to_object_id(event_id)
    content = file.file.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": "CSV file size exceeds the 2 MB limit."
            }
        )
    result = import_participants_csv(db, current_admin, event_obj_id, content)
    return {
        "success": True,
        "data": result
    }
