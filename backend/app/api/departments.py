from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_admin
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services import department as service

router = APIRouter(prefix="/departments", tags=["departments"], dependencies=[Depends(get_current_user)])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=DepartmentRead, status_code=201, dependencies=[Depends(require_admin)])
def create_department(payload: DepartmentCreate, db: DatabaseSession):
    return service.create_department(db, payload)


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: DatabaseSession, skip: Annotated[int, Query(ge=0)] = 0,
                     limit: Annotated[int, Query(ge=1, le=100)] = 20):
    return service.list_departments(db, skip, limit)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(department_id: int, db: DatabaseSession):
    return service.get_department(db, department_id)


@router.patch("/{department_id}", response_model=DepartmentRead, dependencies=[Depends(require_admin)])
def update_department(department_id: int, payload: DepartmentUpdate, db: DatabaseSession):
    return service.update_department(db, department_id, payload)


@router.delete("/{department_id}", response_model=DepartmentRead, dependencies=[Depends(require_admin)])
def delete_department(department_id: int, db: DatabaseSession):
    return service.delete_department(db, department_id)
