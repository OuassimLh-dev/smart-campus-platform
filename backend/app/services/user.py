from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.models import StudentProfile, ProfessorProfile, UserRole
from app.services.profile import ProfileConflictError


class DuplicateEmailError(Exception):
    """The requested email belongs to another user."""


def get_user(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session, skip: int = 0, limit: int = 20) -> list[User]:
    # Include inactive users and keep pagination ordering deterministic.
    return list(db.scalars(select(User).order_by(User.id).offset(skip).limit(limit)))


def _ensure_email_available(db: Session, email: str, user_id: int | None = None) -> None:
    statement = select(User.id).where(User.email == email)
    if user_id is not None:
        statement = statement.where(User.id != user_id)
    if db.scalar(statement) is not None:
        raise DuplicateEmailError


def _save(db: Session, user: User) -> User:
    email, user_id = user.email, user.id
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handle an email claimed after the initial check, without disguising
        # unrelated integrity failures as duplicate emails.
        _ensure_email_available(db, email, user_id)
        raise
    db.refresh(user)
    return user


def create_user(
    db: Session, payload: UserCreate, *, hashed_password: str | None = None
) -> User:
    _ensure_email_available(db, str(payload.email))
    user = User(**payload.model_dump(), hashed_password=hashed_password)
    db.add(user)
    return _save(db, user)


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    changes = payload.model_dump(exclude_unset=True)
    if "role" in changes:
        db.scalar(select(User).where(User.id == user.id).with_for_update()
                  .execution_options(populate_existing=True))
        for model, required_role in ((StudentProfile, UserRole.STUDENT), (ProfessorProfile, UserRole.PROFESSOR)):
            if changes["role"] != required_role and db.scalar(select(model.id).where(model.user_id == user.id)) is not None:
                raise ProfileConflictError("Cannot change role while an incompatible academic profile exists")
    if "email" in changes:
        _ensure_email_available(db, changes["email"], user.id)
    for field, value in changes.items():
        setattr(user, field, value)
    return _save(db, user)


def delete_user(db: Session, user: User) -> User:
    user.is_active = False
    return _save(db, user)
