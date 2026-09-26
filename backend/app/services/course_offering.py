from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CourseOffering, Enrollment, EnrollmentStatus
from app.schemas.course_offering import CourseOfferingCreate, CourseOfferingUpdate
from app.services.academic import AcademicConflictError
from app.services.academic_term import get_term
from app.services.course import get_course, validate_professor
from app.services.delivery import ensure_combination, get_record, save_unique


def get_offering(db: Session, offering_id: int, *, lock=False) -> CourseOffering:
    return get_record(db, CourseOffering, offering_id, "Offering", lock=lock)


def occupied_seats(db: Session, offering_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Enrollment).where(
        Enrollment.course_offering_id == offering_id, Enrollment.status != EnrollmentStatus.DROPPED
    ))


def list_offerings(db: Session, skip=0, limit=20, **filters) -> list[CourseOffering]:
    query = select(CourseOffering)
    for field in ("course_id", "professor_id", "term_id", "is_open"):
        if filters.get(field) is not None:
            query = query.where(getattr(CourseOffering, field) == filters[field])
    return list(db.scalars(query.order_by(CourseOffering.id).offset(skip).limit(limit)))


def create_offering(db: Session, payload: CourseOfferingCreate) -> CourseOffering:
    get_course(db, payload.course_id)
    validate_professor(db, payload.professor_id)
    get_term(db, payload.term_id)
    ensure_combination(db, CourseOffering, payload.model_dump(include={"course_id", "term_id", "section"}))
    offering = CourseOffering(**payload.model_dump())
    db.add(offering)
    return save_unique(db, offering, ("course_id", "term_id", "section"))


def update_offering(db: Session, offering_id: int, payload: CourseOfferingUpdate) -> CourseOffering:
    offering = get_offering(db, offering_id, lock=True)
    changes = payload.model_dump(exclude_unset=True)
    if "course_id" in changes:
        get_course(db, changes["course_id"])
    if "professor_id" in changes:
        validate_professor(db, changes["professor_id"])
    if "term_id" in changes:
        get_term(db, changes["term_id"])
    if "capacity" in changes and changes["capacity"] < occupied_seats(db, offering_id):
        raise AcademicConflictError("Capacity cannot be below occupied seats")
    ensure_combination(db, CourseOffering, {field: changes.get(field, getattr(offering, field))
                                             for field in ("course_id", "term_id", "section")}, offering.id)
    for field, value in changes.items():
        setattr(offering, field, value)
    return save_unique(db, offering, ("course_id", "term_id", "section"))
