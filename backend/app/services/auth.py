from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.schemas.user import UserCreate
from app.services.user import create_user


def register_user(db: Session, payload: RegisterRequest) -> User:
    user_data = UserCreate(**payload.model_dump(exclude={"password"}))
    return create_user(
        db, user_data, hashed_password=hash_password(payload.password.get_secret_value())
    )


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    valid = verify_password(password, user.hashed_password if user else None)
    if not valid or user is None or not user.is_active:
        return None
    return user
