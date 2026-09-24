from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.authorization import AuthenticatedUser
from app.api.profile_authorization import ProfessorUser, can_read_private_professor_profile
from app.db.session import get_db
from app.schemas.professor_profile import (
    ProfessorProfileCreate, ProfessorProfilePublic, ProfessorProfileRead, ProfessorProfileUpdate,
)
from app.services import professor_profile as service

router = APIRouter(prefix="/professors", tags=["professors"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/profile", response_model=ProfessorProfileRead, status_code=201)
def create_profile(payload: ProfessorProfileCreate, user: ProfessorUser, db: DatabaseSession):
    return service.create_profile(db, user, payload)


@router.get("/me", response_model=ProfessorProfileRead)
def own_profile(user: ProfessorUser, db: DatabaseSession):
    return service.get_by_user(db, user.id)


@router.patch("/me", response_model=ProfessorProfileRead)
def update_profile(payload: ProfessorProfileUpdate, user: ProfessorUser, db: DatabaseSession):
    return service.update_profile(db, user, payload)


@router.get("/{professor_id}", response_model=ProfessorProfileRead | ProfessorProfilePublic)
def get_profile(professor_id: int, user: AuthenticatedUser, db: DatabaseSession):
    profile = service.get_by_id(db, professor_id)
    if can_read_private_professor_profile(user, profile.user_id):
        return ProfessorProfileRead.model_validate(profile)
    # Construct the public schema explicitly so private fields cannot leak.
    return ProfessorProfilePublic.model_validate(profile)
