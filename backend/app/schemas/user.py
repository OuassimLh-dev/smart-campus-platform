from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

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


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
