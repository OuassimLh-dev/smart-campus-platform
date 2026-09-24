from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.profile import (
    ProfileConflictError, ProfileNotFoundError, ProfileRoleError, ProfileValidationError,
)

PROFILE_ERROR_STATUS = {
    ProfileConflictError: 409,
    ProfileNotFoundError: 404,
    ProfileRoleError: 403,
    ProfileValidationError: 422,
}


async def profile_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=PROFILE_ERROR_STATUS[type(exc)], content={"detail": str(exc)})


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Validation errors must not echo request input, which may contain passwords.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})
