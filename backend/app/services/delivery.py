from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.services.academic import AcademicConflictError, AcademicNotFoundError


class AcademicValidationError(Exception):
    pass


class AcademicPermissionError(Exception):
    pass


def get_record(db: Session, model, record_id: int, label: str, *, lock: bool = False):
    query = select(model).where(model.id == record_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    record = db.scalar(query)
    if record is None:
        raise AcademicNotFoundError(f"{label} not found")
    return record


def ensure_combination(db: Session, model, values: dict, record_id=None) -> None:
    query = select(model.id).where(*(getattr(model, field) == value for field, value in values.items()))
    if record_id is not None:
        query = query.where(model.id != record_id)
    if db.scalar(query) is not None:
        raise AcademicConflictError(f"{model.__name__} already exists")


def save_unique(db: Session, record, fields: tuple[str, ...]):
    model, record_id = type(record), record.id
    values = {field: getattr(record, field) for field in fields}
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        ensure_combination(db, model, values, record_id)
        raise
    db.refresh(record)
    return record
