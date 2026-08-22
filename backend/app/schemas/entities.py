from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from app.models.constants import UserRole, EventStatus, TicketStatus, AuditStatus
from app.schemas.base import PyObjectId

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: EmailStr
    role: UserRole
    name: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

class UserResponse(UserBase):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)

# --- EVENT SCHEMAS ---
class EventBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    venue: str = Field(..., min_length=2, max_length=150)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Format: YYYY-MM-DD")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Format: HH:MM")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Format: HH:MM")
    timezone: str = Field(default="Asia/Karachi")
    capacity: int = Field(..., ge=1)
    status: EventStatus = Field(default=EventStatus.DRAFT)

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    utc_start: datetime
    utc_end: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)

# --- PARTICIPANT SCHEMAS ---
class ParticipantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: bool = True

class ParticipantCreate(ParticipantBase):
    pass

class ParticipantResponse(ParticipantBase):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    event_id: PyObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)

# --- TICKET SCHEMAS ---
class TicketBase(BaseModel):
    ticket_code: str
    status: TicketStatus = Field(default=TicketStatus.ACTIVE)
    expires_at: datetime

class TicketResponse(TicketBase):
    """
    Safe administrative response for a ticket.
    Strictly does NOT expose the secret QR token string.
    """
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    event_id: PyObjectId
    participant_id: PyObjectId
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(populate_by_name=True)

class TicketPublicResponse(BaseModel):
    """
    Strictly limited public ticket details for display.
    Excludes secret token, database IDs, and sensitive contact fields.
    """
    ticket_code: str
    participant_name: str
    event_name: str
    venue: str
    date: str
    time: str
    timezone: str
    status: TicketStatus

# --- ATTENDANCE SCHEMAS ---
class AttendanceResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    event_id: PyObjectId
    ticket_id: PyObjectId
    participant_id: PyObjectId
    scanned_by: PyObjectId
    scanned_at: datetime

    model_config = ConfigDict(populate_by_name=True)

# --- AUDIT LOG SCHEMAS ---
class AuditLogResponse(BaseModel):
    id: PyObjectId = Field(alias="_id", serialization_alias="id")
    actor_id: Optional[PyObjectId] = None
    actor_email: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[PyObjectId] = None
    status: AuditStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime

    model_config = ConfigDict(populate_by_name=True)
