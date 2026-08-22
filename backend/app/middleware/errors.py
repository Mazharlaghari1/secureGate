import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("event_access")

def get_error_code_from_status(status_code: int) -> str:
    if status_code == status.HTTP_400_BAD_REQUEST:
        return "BAD_REQUEST"
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        return "AUTHENTICATION_FAILED"
    elif status_code == status.HTTP_403_FORBIDDEN:
        return "INSUFFICIENT_PERMISSIONS"
    elif status_code == status.HTTP_404_NOT_FOUND:
        return "NOT_FOUND"
    elif status_code == status.HTTP_409_CONFLICT:
        return "CONFLICT"
    elif status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return "VALIDATION_ERROR"
    return "INTERNAL_SERVER_ERROR"

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = {}
    for error in exc.errors():
        # Formulate field location path
        loc = ".".join(str(x) for x in error.get("loc", []) if x != "body")
        errors[loc] = error.get("msg", "Validation error")
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed for request parameters.",
                "details": errors
            }
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    code = None
    message = None
    details = {}
    
    if isinstance(detail, dict):
        code = detail.get("code")
        message = detail.get("message")
        details = detail.get("details", {})
        
    if not code:
        code = get_error_code_from_status(exc.status_code)
    if not message:
        message = str(detail) if detail else "HTTP Exception occurred."
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": {}
            }
        }
    )
