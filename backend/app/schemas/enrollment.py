from datetime import datetime

from pydantic import ConfigDict, Field

from app.models.enrollment import EnrollmentStatus
from app.schemas.academic import AcademicInput


class EnrollmentCreate(AcademicInput):
    course_offering_id: int = Field(gt=0)


class EnrollmentRead(AcademicInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_offering_id: int
    status: EnrollmentStatus
    enrolled_at: datetime
    created_at: datetime
    updated_at: datetime


class RosterEntry(EnrollmentRead):
    student_number: str
    first_name: str
    last_name: str
