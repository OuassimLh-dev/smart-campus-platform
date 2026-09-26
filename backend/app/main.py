from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.api.auth import router as auth_router
from app.api.errors import PROFILE_ERROR_STATUS, profile_error_handler, validation_error_handler
from app.api.students import router as students_router
from app.api.professors import router as professors_router

from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.departments import router as departments_router
from app.api.courses import router as courses_router
from app.api.errors import ACADEMIC_ERROR_STATUS, academic_error_handler
from app.api.terms import router as terms_router
from app.api.course_offerings import router as offerings_router
from app.api.enrollments import router as enrollments_router
from app.api.grades import router as grades_router

app = FastAPI(title="Smart Campus Management Platform API")
app.include_router(terms_router, prefix="/api/v1")
app.include_router(offerings_router, prefix="/api/v1")
app.include_router(enrollments_router, prefix="/api/v1")
app.include_router(grades_router, prefix="/api/v1")
app.add_exception_handler(RequestValidationError, validation_error_handler)
for error_type in ACADEMIC_ERROR_STATUS:
    app.add_exception_handler(error_type, academic_error_handler)
app.include_router(departments_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
for error_type in PROFILE_ERROR_STATUS:
    app.add_exception_handler(error_type, profile_error_handler)
app.include_router(students_router, prefix="/api/v1")
app.include_router(professors_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
