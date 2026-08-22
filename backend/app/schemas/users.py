from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class StaffCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the staff member")
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Login password")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Name cannot be empty or only whitespace")
        return trimmed

class StaffUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)
    is_active: Optional[bool] = Field(default=None)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Name cannot be empty or only whitespace")
            return trimmed
        return v
