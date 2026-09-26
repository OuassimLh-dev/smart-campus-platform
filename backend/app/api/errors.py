from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.academic import AcademicConflictError, AcademicNotFoundError
from app.services.delivery import AcademicPermissionError, AcademicValidationError
from app.services.profile import (
    ProfileConflictError, ProfileNotFoundError, ProfileRoleError, ProfileValidationError,
)

ACADEMIC_ERROR_STATUS = {AcademicConflictError: 409, AcademicNotFoundError: 404,
                         AcademicPermissionError: 403, AcademicValidationError: 422}

PROFILE_ERROR_STATUS = {
    ProfileConflictError: 409,
    ProfileNotFoundError: 404,
    ProfileRoleError: 403,
    ProfileValidationError: 422,
}


async def academic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=ACADEMIC_ERROR_STATUS[type(exc)], content={"detail": str(exc)})


async def profile_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=PROFILE_ERROR_STATUS[type(exc)], content={"detail": str(exc)})


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Validation errors must not echo request input, which may contain passwords.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]})
