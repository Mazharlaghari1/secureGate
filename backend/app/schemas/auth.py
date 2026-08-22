from pydantic import BaseModel, EmailStr, Field
from app.schemas.entities import UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Login password")

class LoginResponseData(BaseModel):
    token: str
    user: UserResponse

class LoginResponse(BaseModel):
    success: bool = True
    data: LoginResponseData

class AttendeeRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

