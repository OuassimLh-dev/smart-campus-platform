from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole


class ProfileNotFoundError(Exception):
    pass


class ProfileConflictError(Exception):
    pass


class ProfileRoleError(Exception):
    pass


class ProfileValidationError(Exception):
    pass


def require_profile_role(db: Session, user: User, role: UserRole) -> None:
    # Serialize creation against administrative role changes on PostgreSQL.
    db.scalar(select(User).where(User.id == user.id).with_for_update()
              .execution_options(populate_existing=True))
    if user.role != role:
        raise ProfileRoleError("User role does not match profile type")


def get_profile(db: Session, model, *, profile_id=None, user_id=None):
    profile = (db.get(model, profile_id) if profile_id is not None
               else db.scalar(select(model).where(model.user_id == user_id)))
    if profile is None:
        raise ProfileNotFoundError("Profile not found")
    return profile


def ensure_available(db: Session, model, number_field: str, number: str,
                     *, user_id=None, profile_id=None) -> None:
    if user_id is not None and db.scalar(select(model.id).where(model.user_id == user_id)) is not None:
        raise ProfileConflictError("Profile already exists")
    query = select(model.id).where(getattr(model, number_field) == number)
    if profile_id is not None:
        query = query.where(model.id != profile_id)
    if db.scalar(query) is not None:
        raise ProfileConflictError(f"{number_field} already exists")


def save_profile(db: Session, profile, number_field: str):
    model, profile_id, user_id = type(profile), profile.id, profile.user_id
    number = getattr(profile, number_field)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Convert uniqueness races to 409 without hiding unrelated DB failures.
        ensure_available(db, model, number_field, number,
                         user_id=user_id if profile_id is None else None, profile_id=profile_id)
        raise
    db.refresh(profile)
    return profile
