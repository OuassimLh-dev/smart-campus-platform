from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.profile_authorization import StudentUser, accessible_student_profile
from app.db.session import get_db
from app.models.student_profile import StudentProfile
from app.schemas.student_profile import StudentProfileCreate, StudentProfileRead, StudentProfileUpdate
from app.services import student_profile as service

router = APIRouter(prefix="/students", tags=["students"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/profile", response_model=StudentProfileRead, status_code=201)
def create_profile(payload: StudentProfileCreate, user: StudentUser, db: DatabaseSession):
    return service.create_profile(db, user, payload)


@router.get("/me", response_model=StudentProfileRead)
def own_profile(user: StudentUser, db: DatabaseSession):
    return service.get_by_user(db, user.id)


@router.patch("/me", response_model=StudentProfileRead)
def update_profile(payload: StudentProfileUpdate, user: StudentUser, db: DatabaseSession):
    return service.update_profile(db, user, payload)


@router.get("/{student_id}", response_model=StudentProfileRead)
def get_profile(profile: Annotated[StudentProfile, Depends(accessible_student_profile)]):
    return profile
