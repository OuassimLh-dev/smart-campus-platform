from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_admin
from app.api.dependencies import get_current_user
from app.api.enrollment_authorization import managed_offering
from app.db.session import get_db
from app.models import CourseOffering
from app.schemas.course_offering import CourseOfferingCreate, CourseOfferingRead, CourseOfferingUpdate
from app.schemas.enrollment import RosterEntry
from app.schemas.grade import GradeRead
from app.services import course_offering as service
from app.services.enrollment import roster
from app.services.grade import offering_grades

router = APIRouter(prefix="/course-offerings", tags=["course-offerings"], dependencies=[Depends(get_current_user)])
DatabaseSession = Annotated[Session, Depends(get_db)]
ManagedOffering = Annotated[CourseOffering, Depends(managed_offering)]


@router.post("", response_model=CourseOfferingRead, status_code=201, dependencies=[Depends(require_admin)])
def create_offering(payload: CourseOfferingCreate, db: DatabaseSession):
    return service.create_offering(db, payload)


@router.get("", response_model=list[CourseOfferingRead])
def list_offerings(db: DatabaseSession, skip: Annotated[int, Query(ge=0)] = 0,
                   limit: Annotated[int, Query(ge=1, le=100)] = 20,
                   course_id: Annotated[int | None, Query(gt=0)] = None,
                   professor_id: Annotated[int | None, Query(gt=0)] = None,
                   term_id: Annotated[int | None, Query(gt=0)] = None, is_open: bool | None = None):
    return service.list_offerings(db, skip, limit, course_id=course_id, professor_id=professor_id,
                                  term_id=term_id, is_open=is_open)


@router.get("/{offering_id}", response_model=CourseOfferingRead)
def get_offering(offering_id: int, db: DatabaseSession):
    return service.get_offering(db, offering_id)


@router.patch("/{offering_id}", response_model=CourseOfferingRead, dependencies=[Depends(require_admin)])
def update_offering(offering_id: int, payload: CourseOfferingUpdate, db: DatabaseSession):
    return service.update_offering(db, offering_id, payload)


@router.get("/{offering_id}/students", response_model=list[RosterEntry])
def get_roster(offering: ManagedOffering, db: DatabaseSession):
    return roster(db, offering.id)


@router.get("/{offering_id}/grades", response_model=list[GradeRead])
def get_grades(offering: ManagedOffering, db: DatabaseSession):
    return offering_grades(db, offering.id)
