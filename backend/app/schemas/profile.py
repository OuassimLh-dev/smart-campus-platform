from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
MediumText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProfileUpdate(ProfileInput):
    @field_validator("*", check_fields=False)
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field must not be null")
        return value
