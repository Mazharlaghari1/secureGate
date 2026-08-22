from fastapi import APIRouter, Depends, status
from pymongo.database import Database
from app.database import get_db
from app.schemas.auth import LoginRequest, LoginResponse, AttendeeRegisterRequest
from app.schemas.entities import UserResponse
from app.services.auth import authenticate_user
from app.services.users import create_attendee_user
from app.security.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class MeResponse(BaseModel):
    success: bool = True
    data: UserResponse

class RegisterResponse(BaseModel):
    success: bool = True
    data: UserResponse

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Database = Depends(get_db)):
    """
    Performs user authentication and returns a JWT access token on success.
    """
    result = authenticate_user(db, payload.email, payload.password)
    return {
        "success": True,
        "data": {
            "token": result["token"],
            "user": result["user"]
        }
    }

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AttendeeRegisterRequest, db: Database = Depends(get_db)):
    """
    Registers a new attendee user account.
    """
    user = create_attendee_user(db, payload.name, payload.email, payload.password)
    return {
        "success": True,
        "data": user
    }

@router.get("/me", response_model=MeResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retrieves safe profile details of the currently authenticated user session.
    """
    return {
        "success": True,
        "data": current_user
    }
