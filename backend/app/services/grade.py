from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Enrollment, EnrollmentStatus, Grade
from app.schemas.grade import GradeCreate, GradeUpdate
from app.services.academic import AcademicConflictError, AcademicNotFoundError
from app.services.delivery import ensure_combination, save_unique


def create_grade(db: Session, enrollment: Enrollment, payload: GradeCreate) -> Grade:
    if enrollment.status == EnrollmentStatus.DROPPED:
        raise AcademicConflictError("Dropped enrollment cannot be graded")
    ensure_combination(db, Grade, {"enrollment_id": enrollment.id})
    grade = Grade(enrollment_id=enrollment.id, **payload.model_dump())
    db.add(grade)
    enrollment.status = EnrollmentStatus.COMPLETED
    return save_unique(db, grade, ("enrollment_id",))


def update_grade(db: Session, enrollment: Enrollment, payload: GradeUpdate) -> Grade:
    grade = db.scalar(select(Grade).where(Grade.enrollment_id == enrollment.id))
    if grade is None:
        raise AcademicNotFoundError("Grade not found")
    if enrollment.status == EnrollmentStatus.DROPPED:
        raise AcademicConflictError("Dropped enrollment cannot be graded")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(grade, field, value)
    if changes:
        grade.graded_at = func.now()
    return save_unique(db, grade, ("enrollment_id",))


def own_grades(db: Session, student_id: int) -> list[Grade]:
    return list(db.scalars(select(Grade).join(Enrollment).where(
        Enrollment.student_id == student_id).order_by(Grade.id)))


def offering_grades(db: Session, offering_id: int) -> list[Grade]:
    return list(db.scalars(select(Grade).join(Enrollment).where(
        Enrollment.course_offering_id == offering_id).order_by(Grade.id)))
