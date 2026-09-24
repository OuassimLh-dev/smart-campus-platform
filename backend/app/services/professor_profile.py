from sqlalchemy.orm import Session

from app.models.professor_profile import ProfessorProfile
from app.models.user import User, UserRole
from app.schemas.professor_profile import ProfessorProfileCreate, ProfessorProfileUpdate
from app.services.profile import ensure_available, get_profile, require_profile_role, save_profile


def get_by_id(db: Session, profile_id: int) -> ProfessorProfile:
    return get_profile(db, ProfessorProfile, profile_id=profile_id)


def get_by_user(db: Session, user_id: int) -> ProfessorProfile:
    return get_profile(db, ProfessorProfile, user_id=user_id)


def create_profile(db: Session, user: User, payload: ProfessorProfileCreate) -> ProfessorProfile:
    require_profile_role(db, user, UserRole.PROFESSOR)
    ensure_available(db, ProfessorProfile, "employee_number", payload.employee_number, user_id=user.id)
    profile = ProfessorProfile(user_id=user.id, **payload.model_dump())
    db.add(profile)
    return save_profile(db, profile, "employee_number")


def update_profile(db: Session, user: User, payload: ProfessorProfileUpdate) -> ProfessorProfile:
    require_profile_role(db, user, UserRole.PROFESSOR)
    profile = get_by_user(db, user.id)
    changes = payload.model_dump(exclude_unset=True)
    if "employee_number" in changes:
        ensure_available(db, ProfessorProfile, "employee_number", changes["employee_number"], profile_id=profile.id)
    for field, value in changes.items():
        setattr(profile, field, value)
    return save_profile(db, profile, "employee_number")
