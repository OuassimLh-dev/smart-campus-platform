from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.profile import Identifier, LongText, MediumText, ProfileInput, ProfileUpdate, ShortText


class ProfessorProfileCreate(ProfileInput):
    employee_number: Identifier
    department: ShortText
    academic_title: ShortText
    office_location: MediumText
    research_interests: LongText


class ProfessorProfileUpdate(ProfileUpdate):
    employee_number: Identifier | None = None
    department: ShortText | None = None
    academic_title: ShortText | None = None
    office_location: MediumText | None = None
    research_interests: LongText | None = None


class ProfessorProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department: str
    academic_title: str
    office_location: str
    research_interests: str


class ProfessorProfileRead(ProfessorProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
