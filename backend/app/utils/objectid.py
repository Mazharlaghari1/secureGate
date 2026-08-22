from typing import Any
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

def validate_object_id(v: Any) -> str:
    """
    Validates that a value is a valid ObjectId representation.
    Normalizes it to a string.
    Used as a Pydantic validator.
    """
    if isinstance(v, ObjectId):
        return str(v)
    if not isinstance(v, str) or not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId format")
    return v

def str_to_object_id(val: str) -> ObjectId:
    """
    Safely converts a string to a MongoDB ObjectId.
    Raises an HTTPException with 400 status code if conversion fails.
    """
    try:
        return ObjectId(val)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": f"Invalid ID: '{val}'. ID must be a 24-character hexadecimal string."
            }
        )
