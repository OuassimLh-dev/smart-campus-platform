from datetime import date, datetime

from pydantic import ConfigDict, Field, model_validator

from app.schemas.academic import AcademicInput, AcademicUpdate, Code, Title


class AcademicTermCreate(AcademicInput):
    name: Title = Field(max_length=100)
    academic_year: Code
    start_date: date
    end_date: date
    is_active: bool = True

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class AcademicTermUpdate(AcademicUpdate):
    name: Title | None = Field(default=None, max_length=100)
    academic_year: Code | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None


class AcademicTermRead(AcademicTermCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
