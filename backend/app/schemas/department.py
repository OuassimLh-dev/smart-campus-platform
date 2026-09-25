from datetime import datetime

from pydantic import ConfigDict

from app.schemas.academic import AcademicInput, AcademicUpdate, Code, Description, Title


class DepartmentCreate(AcademicInput):
    code: Code
    name: Title
    description: Description | None = None
    is_active: bool = True


class DepartmentUpdate(AcademicUpdate):
    code: Code | None = None
    name: Title | None = None
    description: Description | None = None
    is_active: bool | None = None


class DepartmentRead(DepartmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
