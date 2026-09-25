from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.academic import AcademicNotFoundError, ensure_unique, save_record


def get_department(db: Session, department_id: int) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise AcademicNotFoundError("Department not found")
    return department


def list_departments(db: Session, skip: int = 0, limit: int = 20) -> list[Department]:
    return list(db.scalars(select(Department).where(Department.is_active.is_(True))
                           .order_by(Department.id).offset(skip).limit(limit)))


def create_department(db: Session, payload: DepartmentCreate) -> Department:
    ensure_unique(db, Department, {"code": payload.code, "name": payload.name})
    department = Department(**payload.model_dump())
    db.add(department)
    return save_record(db, department, ("code", "name"))


def update_department(db: Session, department_id: int, payload: DepartmentUpdate) -> Department:
    department = get_department(db, department_id)
    changes = payload.model_dump(exclude_unset=True)
    ensure_unique(db, Department, {field: changes[field] for field in ("code", "name") if field in changes}, department.id)
    for field, value in changes.items():
        setattr(department, field, value)
    return save_record(db, department, ("code", "name"))


def delete_department(db: Session, department_id: int) -> Department:
    department = get_department(db, department_id)
    department.is_active = False
    return save_record(db, department, ("code", "name"))
