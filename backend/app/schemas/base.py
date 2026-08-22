from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated
from app.utils.objectid import validate_object_id

# Reusable custom ObjectId type for Pydantic models
PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]

# Standard API Error Schema
class ErrorDetails(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetails

# Standard API Success Schema
class SuccessResponse(BaseModel):
    success: bool = True
    data: Any

# Reusable Pagination Parameters
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page (max 100)")

# Reusable Generic Paginated Response Schema
T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    page: int
    page_size: int
    total: int
