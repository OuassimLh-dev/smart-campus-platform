from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_admin
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.academic_term import AcademicTermCreate, AcademicTermRead, AcademicTermUpdate
from app.services import academic_term as service

router = APIRouter(prefix="/terms", tags=["terms"], dependencies=[Depends(get_current_user)])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=AcademicTermRead, status_code=201, dependencies=[Depends(require_admin)])
def create_term(payload: AcademicTermCreate, db: DatabaseSession):
    return service.create_term(db, payload)


@router.get("", response_model=list[AcademicTermRead])
def list_terms(db: DatabaseSession, skip: Annotated[int, Query(ge=0)] = 0,
               limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return service.list_terms(db, skip, limit)


@router.get("/{term_id}", response_model=AcademicTermRead)
def get_term(term_id: int, db: DatabaseSession):
    return service.get_term(db, term_id)


@router.patch("/{term_id}", response_model=AcademicTermRead, dependencies=[Depends(require_admin)])
def update_term(term_id: int, payload: AcademicTermUpdate, db: DatabaseSession):
    return service.update_term(db, term_id, payload)
