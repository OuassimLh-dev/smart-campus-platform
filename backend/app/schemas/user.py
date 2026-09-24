from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.models.user import UserRole

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class UserBase(BaseModel):
    first_name: Name
    last_name: Name
    email: EmailStr = Field(max_length=254)
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Name | None = None
    last_name: Name | None = None
    email: EmailStr | None = Field(default=None, max_length=254)
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("*")
    @classmethod
    def reject_null(cls, value):
        # Fields may be omitted, but database columns cannot be set to NULL.
        if value is None:
            raise ValueError("Field must not be null")
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
