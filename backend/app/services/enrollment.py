from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Enrollment, EnrollmentStatus, StudentProfile
from app.schemas.enrollment import EnrollmentRead, RosterEntry
from app.services.academic import AcademicConflictError
from app.services.course_offering import get_offering, occupied_seats
from app.services.delivery import ensure_combination, get_record, save_unique


def get_enrollment(db: Session, enrollment_id: int, *, lock=False) -> Enrollment:
    return get_record(db, Enrollment, enrollment_id, "Enrollment", lock=lock)


def lock_enrollment(db: Session, enrollment_id: int) -> Enrollment:
    enrollment = get_enrollment(db, enrollment_id)
    # Use the same lock ordering everywhere: offering first, enrollment second.
    get_offering(db, enrollment.course_offering_id, lock=True)
    return get_enrollment(db, enrollment_id, lock=True)


def enroll(db: Session, student: StudentProfile, offering_id: int) -> Enrollment:
    offering = get_offering(db, offering_id, lock=True)
    ensure_combination(db, Enrollment, {"student_id": student.id, "course_offering_id": offering_id})
    if not offering.is_open:
        raise AcademicConflictError("Offering is closed")
    if occupied_seats(db, offering_id) >= offering.capacity:
        raise AcademicConflictError("Offering is full")
    enrollment = Enrollment(student_id=student.id, course_offering_id=offering_id)
    db.add(enrollment)
    return save_unique(db, enrollment, ("student_id", "course_offering_id"))


def own_enrollments(db: Session, student_id: int) -> list[Enrollment]:
    return list(db.scalars(select(Enrollment).where(Enrollment.student_id == student_id).order_by(Enrollment.id)))


def drop_enrollment(db: Session, enrollment: Enrollment) -> Enrollment:
    if enrollment.status == EnrollmentStatus.COMPLETED:
        raise AcademicConflictError("Completed enrollment cannot be dropped")
    enrollment.status = EnrollmentStatus.DROPPED
    return save_unique(db, enrollment, ("student_id", "course_offering_id"))


def roster(db: Session, offering_id: int) -> list[RosterEntry]:
    records = db.scalars(select(Enrollment).where(
        Enrollment.course_offering_id == offering_id, Enrollment.status != EnrollmentStatus.DROPPED
    ).options(joinedload(Enrollment.student).joinedload(StudentProfile.user)).order_by(Enrollment.id))
    return [RosterEntry(**EnrollmentRead.model_validate(record).model_dump(),
                        student_number=record.student.student_number,
                        first_name=record.student.user.first_name, last_name=record.student.user.last_name)
            for record in records]
