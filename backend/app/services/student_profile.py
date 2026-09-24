from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.student_profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.student_profile import StudentProfileCreate, StudentProfileUpdate
from app.services.profile import (
    ProfileValidationError, ensure_available, get_profile, require_profile_role, save_profile,
)


def get_by_id(db: Session, profile_id: int) -> StudentProfile:
    return get_profile(db, StudentProfile, profile_id=profile_id)


def get_by_user(db: Session, user_id: int) -> StudentProfile:
    return get_profile(db, StudentProfile, user_id=user_id)


def create_profile(db: Session, user: User, payload: StudentProfileCreate) -> StudentProfile:
    require_profile_role(db, user, UserRole.STUDENT)
    ensure_available(db, StudentProfile, "student_number", payload.student_number, user_id=user.id)
    profile = StudentProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    return save_profile(db, profile, "student_number")


def update_profile(db: Session, user: User, payload: StudentProfileUpdate) -> StudentProfile:
    require_profile_role(db, user, UserRole.STUDENT)
    profile = get_by_user(db, user.id)
    changes = payload.model_dump(exclude_unset=True)
    values = {field: getattr(profile, field) for field in StudentProfileCreate.model_fields}
    try:
        StudentProfileCreate.model_validate(values | changes)
    except ValidationError as exc:
        raise ProfileValidationError("Expected graduation year must not precede enrollment year") from exc
    if "student_number" in changes:
        ensure_available(db, StudentProfile, "student_number", changes["student_number"], profile_id=profile.id)
    for field, value in changes.items():
        setattr(profile, field, value)
    return save_profile(db, profile, "student_number")
