from datetime import datetime

from pydantic import ConfigDict, Field, model_validator

from app.schemas.profile import Identifier, MediumText, ProfileInput, ProfileUpdate, ShortText


class StudentProfileCreate(ProfileInput):
    student_number: Identifier
    department: ShortText
    program: MediumText
    year_level: int = Field(ge=1)
    enrollment_year: int = Field(ge=1900, le=2200)
    expected_graduation_year: int = Field(ge=1900, le=2200)

    @model_validator(mode="after")
    def validate_years(self):
        if self.expected_graduation_year < self.enrollment_year:
            raise ValueError("Expected graduation year must not precede enrollment year")
        return self


class StudentProfileUpdate(ProfileUpdate):
    student_number: Identifier | None = None
    department: ShortText | None = None
    program: MediumText | None = None
    year_level: int | None = Field(default=None, ge=1)
    enrollment_year: int | None = Field(default=None, ge=1900, le=2200)
    expected_graduation_year: int | None = Field(default=None, ge=1900, le=2200)


class StudentProfileRead(StudentProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
