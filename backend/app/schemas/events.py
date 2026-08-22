from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.timezone import is_valid_timezone
from app.models.constants import EventStatus

class EventCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the event")
    description: Optional[str] = Field(default=None, max_length=500, description="Optional description of the event")
    venue: str = Field(..., min_length=2, max_length=150, description="Venue name/location")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Format: YYYY-MM-DD")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Format: HH:MM")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Format: HH:MM")
    timezone: str = Field(default="Asia/Karachi", description="IANA timezone name")
    capacity: int = Field(..., ge=1, description="Event seating/attendance capacity")

    @field_validator("timezone")
    @classmethod
    def validate_tz(cls, v: str) -> str:
        if not is_valid_timezone(v):
            raise ValueError("Invalid IANA timezone name")
        return v

    @field_validator("name", "venue")
    @classmethod
    def trim_strings(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or only whitespace")
        return trimmed

class EventUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    venue: Optional[str] = Field(default=None, min_length=2, max_length=150)
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    end_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    timezone: Optional[str] = Field(default=None)
    capacity: Optional[int] = Field(default=None, ge=1)
    status: Optional[EventStatus] = Field(default=None)

    @field_validator("timezone")
    @classmethod
    def validate_tz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not is_valid_timezone(v):
            raise ValueError("Invalid IANA timezone name")
        return v

    @field_validator("name", "venue")
    @classmethod
    def trim_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Field cannot be empty or only whitespace")
            return trimmed
        return v
