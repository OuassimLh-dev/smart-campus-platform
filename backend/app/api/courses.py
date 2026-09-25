from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_admin
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate
from app.services import course as service

router = APIRouter(prefix="/courses", tags=["courses"], dependencies=[Depends(get_current_user)])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=CourseRead, status_code=201, dependencies=[Depends(require_admin)])
def create_course(payload: CourseCreate, db: DatabaseSession):
    return service.create_course(db, payload)


@router.get("", response_model=list[CourseRead])
def list_courses(db: DatabaseSession, skip: Annotated[int, Query(ge=0)] = 0,
                 limit: Annotated[int, Query(ge=1, le=100)] = 20,
                 department_id: Annotated[int | None, Query(gt=0)] = None,
                 professor_id: Annotated[int | None, Query(gt=0)] = None):
    return service.list_courses(db, skip, limit, department_id, professor_id)


@router.get("/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: DatabaseSession):
    return service.get_course(db, course_id)


@router.patch("/{course_id}", response_model=CourseRead, dependencies=[Depends(require_admin)])
def update_course(course_id: int, payload: CourseUpdate, db: DatabaseSession):
    return service.update_course(db, course_id, payload)


@router.delete("/{course_id}", response_model=CourseRead, dependencies=[Depends(require_admin)])
def delete_course(course_id: int, db: DatabaseSession):
    return service.delete_course(db, course_id)
