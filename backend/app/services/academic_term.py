from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.academic_term import AcademicTerm
from app.schemas.academic_term import AcademicTermCreate, AcademicTermUpdate
from app.services.delivery import AcademicValidationError, ensure_combination, get_record, save_unique


def get_term(db: Session, term_id: int) -> AcademicTerm:
    return get_record(db, AcademicTerm, term_id, "Term")


def list_terms(db: Session, skip=0, limit=20) -> list[AcademicTerm]:
    return list(db.scalars(select(AcademicTerm).order_by(AcademicTerm.id).offset(skip).limit(limit)))


def create_term(db: Session, payload: AcademicTermCreate) -> AcademicTerm:
    ensure_combination(db, AcademicTerm, {"name": payload.name, "academic_year": payload.academic_year})
    term = AcademicTerm(**payload.model_dump())
    db.add(term)
    return save_unique(db, term, ("name", "academic_year"))


def update_term(db: Session, term_id: int, payload: AcademicTermUpdate) -> AcademicTerm:
    term = get_record(db, AcademicTerm, term_id, "Term", lock=True)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("start_date", term.start_date) >= changes.get("end_date", term.end_date):
        raise AcademicValidationError("start_date must be before end_date")
    ensure_combination(db, AcademicTerm, {field: changes.get(field, getattr(term, field))
                                          for field in ("name", "academic_year")}, term.id)
    for field, value in changes.items():
        setattr(term, field, value)
    return save_unique(db, term, ("name", "academic_year"))
