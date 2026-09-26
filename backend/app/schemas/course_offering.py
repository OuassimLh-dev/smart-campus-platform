from datetime import datetime

from pydantic import ConfigDict, Field, field_validator

from app.schemas.academic import AcademicInput, AcademicUpdate, Code


class CourseOfferingCreate(AcademicInput):
    course_id: int = Field(gt=0)
    professor_id: int = Field(gt=0)
    term_id: int = Field(gt=0)
    section: Code
    capacity: int = Field(gt=0, strict=True)
    is_open: bool = True


class CourseOfferingUpdate(AcademicUpdate):
    course_id: int | None = Field(default=None, gt=0)
    professor_id: int | None = Field(default=None, gt=0)
    term_id: int | None = Field(default=None, gt=0)
    section: Code | None = None
    capacity: int | None = Field(default=None, gt=0, strict=True)
    is_open: bool | None = None

    @field_validator("professor_id")
    @classmethod
    def professor_required(cls, value):
        if value is None:
            raise ValueError("Offering professor must not be null")
        return value


class CourseOfferingRead(CourseOfferingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
