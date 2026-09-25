from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationInfo, field_validator

Code = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
Description = Annotated[str, Field(max_length=5000)]


class AcademicInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AcademicUpdate(AcademicInput):
    @field_validator("*", check_fields=False)
    @classmethod
    def reject_null_required_fields(cls, value, info: ValidationInfo):
        if value is None and info.field_name not in {"description", "professor_id"}:
            raise ValueError("Field must not be null")
        return value
