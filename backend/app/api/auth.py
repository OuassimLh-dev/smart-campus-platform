from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, unauthorized
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth import authenticate_user, register_user
from app.services.user import DuplicateEmailError

router = APIRouter(prefix="/auth", tags=["auth"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: DatabaseSession) -> User:
    try:
        return register_user(db, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, db: DatabaseSession,
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    user = authenticate_user(db, str(payload.email), payload.password.get_secret_value())
    if user is None:
        raise unauthorized()
    return TokenResponse(access_token=create_access_token(user.id, settings))


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
