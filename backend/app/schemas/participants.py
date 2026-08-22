from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator

class ParticipantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the participant")
    email: EmailStr = Field(..., description="Email address of the participant")
    phone: Optional[str] = Field(default=None, max_length=20, description="Optional phone number")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or only whitespace")
        return trimmed

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> str:
        return v.strip().lower()

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

class ParticipantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Name cannot be empty or only whitespace")
            return trimmed
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[str]:
        if v is not None:
            return v.strip().lower()
        return v

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v
