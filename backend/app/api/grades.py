from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.enrollment_authorization import CurrentStudent
from app.db.session import get_db
from app.schemas.grade import GradeRead
from app.services.grade import own_grades

router = APIRouter(prefix="/grades", tags=["grades"])


@router.get("/me", response_model=list[GradeRead])
def get_own_grades(student: CurrentStudent, db: Annotated[Session, Depends(get_db)]):
    return own_grades(db, student.id)
