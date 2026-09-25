from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class AcademicNotFoundError(Exception):
    pass


class AcademicConflictError(Exception):
    pass


def ensure_unique(db: Session, model, values: dict, record_id: int | None = None) -> None:
    for field, value in values.items():
        query = select(model.id).where(getattr(model, field) == value)
        if record_id is not None:
            query = query.where(model.id != record_id)
        if db.scalar(query) is not None:
            raise AcademicConflictError(f"{model.__name__} {field} already exists")


def save_record(db: Session, record, unique_fields: tuple[str, ...]):
    model, record_id = type(record), record.id
    values = {field: getattr(record, field) for field in unique_fields}
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Handle uniqueness races without masking unrelated database errors.
        ensure_unique(db, model, values, record_id)
        raise
    db.refresh(record)
    return record
