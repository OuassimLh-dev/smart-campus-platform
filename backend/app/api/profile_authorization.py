from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.authorization import AuthenticatedUser, require_roles
from app.db.session import get_db
from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.services.student_profile import get_by_id

require_student = require_roles(UserRole.STUDENT)
require_professor = require_roles(UserRole.PROFESSOR)
StudentUser = Annotated[User, Depends(require_student)]
ProfessorUser = Annotated[User, Depends(require_professor)]


def accessible_student_profile(
    student_id: int, current_user: AuthenticatedUser,
    db: Annotated[Session, Depends(get_db)],
) -> StudentProfile:
    profile = get_by_id(db, student_id)
    if current_user.role not in {UserRole.ADMIN, UserRole.PROFESSOR} and profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return profile


def can_read_private_professor_profile(current_user: User, profile_user_id: int) -> bool:
    return current_user.role == UserRole.ADMIN or current_user.id == profile_user_id
