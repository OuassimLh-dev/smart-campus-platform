from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.auth import router as auth_router
from app.api.errors import PROFILE_ERROR_STATUS, profile_error_handler, validation_error_handler
from app.api.students import router as students_router
from app.api.professors import router as professors_router

from app.api.health import router as health_router
from app.api.users import router as users_router

app = FastAPI(title="Smart Campus Management Platform API")
app.add_exception_handler(RequestValidationError, validation_error_handler)
for error_type in PROFILE_ERROR_STATUS:
    app.add_exception_handler(error_type, profile_error_handler)
app.include_router(students_router, prefix="/api/v1")
app.include_router(professors_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
