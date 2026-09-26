from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict, Field, field_validator

from app.schemas.academic import AcademicInput, Description


class GradeCreate(AcademicInput):
    grade: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    feedback: Description | None = None


class GradeUpdate(AcademicInput):
    grade: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    feedback: Description | None = None

    @field_validator("grade")
    @classmethod
    def reject_null_grade(cls, value):
        if value is None:
            raise ValueError("Grade must not be null")
        return value


class GradeRead(AcademicInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enrollment_id: int
    grade: float
    feedback: str | None
    graded_at: datetime
    created_at: datetime
    updated_at: datetime
