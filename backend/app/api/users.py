from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user as user_service

router = APIRouter(prefix="/users", tags=["users"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def require_user(user_id: int, db: DatabaseSession) -> User:
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


ExistingUser = Annotated[User, Depends(require_user)]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DatabaseSession) -> User:
    try:
        return user_service.create_user(db, payload)
    except user_service.DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc


@router.get("", response_model=list[UserRead])
def list_users(
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[User]:
    return user_service.list_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user: ExistingUser) -> User:
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(payload: UserUpdate, user: ExistingUser, db: DatabaseSession) -> User:
    try:
        return user_service.update_user(db, user, payload)
    except user_service.DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(user: ExistingUser, db: DatabaseSession) -> User:
    return user_service.delete_user(db, user)
