from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.authorization import require_professor_or_admin
from app.api.profile_authorization import StudentUser
from app.db.session import get_db
from app.models import CourseOffering, Enrollment, StudentProfile, User, UserRole
from app.services.course_offering import get_offering
from app.services.delivery import AcademicPermissionError
from app.services.enrollment import lock_enrollment
from app.services.student_profile import get_by_user

DatabaseSession = Annotated[Session, Depends(get_db)]
TeachingUser = Annotated[User, Depends(require_professor_or_admin)]


def current_student(user: StudentUser, db: DatabaseSession) -> StudentProfile:
    return get_by_user(db, user.id)


CurrentStudent = Annotated[StudentProfile, Depends(current_student)]


def check_offering_manager(user: User, offering: CourseOffering) -> None:
    if user.role != UserRole.ADMIN and offering.professor.user_id != user.id:
        raise AcademicPermissionError("Only the assigned professor or an admin may access this offering")


def managed_offering(offering_id: int, user: TeachingUser, db: DatabaseSession) -> CourseOffering:
    offering = get_offering(db, offering_id, lock=True)
    check_offering_manager(user, offering)
    return offering


def managed_enrollment(enrollment_id: int, user: TeachingUser, db: DatabaseSession) -> Enrollment:
    enrollment = lock_enrollment(db, enrollment_id)
    check_offering_manager(user, enrollment.offering)
    return enrollment


def own_enrollment(enrollment_id: int, student: CurrentStudent, db: DatabaseSession) -> Enrollment:
    enrollment = lock_enrollment(db, enrollment_id)
    if enrollment.student_id != student.id:
        raise AcademicPermissionError("Cannot drop another student's enrollment")
    return enrollment
