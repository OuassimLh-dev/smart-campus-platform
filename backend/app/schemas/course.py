from datetime import datetime

from pydantic import ConfigDict, Field

from app.schemas.academic import AcademicInput, AcademicUpdate, Code, Description, Title


class CourseCreate(AcademicInput):
    code: Code
    title: Title
    description: Description | None = None
    credits: int = Field(gt=0, strict=True)
    department_id: int = Field(gt=0)
    professor_id: int | None = Field(default=None, gt=0)
    is_active: bool = True


class CourseUpdate(AcademicUpdate):
    code: Code | None = None
    title: Title | None = None
    description: Description | None = None
    credits: int | None = Field(default=None, gt=0, strict=True)
    department_id: int | None = Field(default=None, gt=0)
    professor_id: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class CourseRead(CourseCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
