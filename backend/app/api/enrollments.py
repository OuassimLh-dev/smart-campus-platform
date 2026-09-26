from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.enrollment_authorization import CurrentStudent, managed_enrollment, own_enrollment
from app.db.session import get_db
from app.models import Enrollment
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead
from app.schemas.grade import GradeCreate, GradeRead, GradeUpdate
from app.services import enrollment as service
from app.services import grade as grade_service

router = APIRouter(prefix="/enrollments", tags=["enrollments"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ManagedEnrollment = Annotated[Enrollment, Depends(managed_enrollment)]


@router.post("", response_model=EnrollmentRead, status_code=201)
def enroll(payload: EnrollmentCreate, student: CurrentStudent, db: DatabaseSession):
    return service.enroll(db, student, payload.course_offering_id)


@router.get("/me", response_model=list[EnrollmentRead])
def own_enrollments(student: CurrentStudent, db: DatabaseSession):
    return service.own_enrollments(db, student.id)


@router.patch("/{enrollment_id}/drop", response_model=EnrollmentRead)
def drop(enrollment: Annotated[Enrollment, Depends(own_enrollment)], db: DatabaseSession):
    return service.drop_enrollment(db, enrollment)


@router.post("/{enrollment_id}/grade", response_model=GradeRead, status_code=201)
def create_grade(payload: GradeCreate, enrollment: ManagedEnrollment, db: DatabaseSession):
    return grade_service.create_grade(db, enrollment, payload)


@router.patch("/{enrollment_id}/grade", response_model=GradeRead)
def update_grade(payload: GradeUpdate, enrollment: ManagedEnrollment, db: DatabaseSession):
    return grade_service.update_grade(db, enrollment, payload)
