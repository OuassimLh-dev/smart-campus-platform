from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException

from app.api.dependencies import get_current_user
from app.models.user import User, UserRole
from app.schemas.user import UserUpdate

AuthenticatedUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable:
    """Authorize against the current database role, not a token claim."""
    def dependency(current_user: AuthenticatedUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return dependency


require_professor_or_admin = require_roles(UserRole.PROFESSOR, UserRole.ADMIN)
require_admin = require_roles(UserRole.ADMIN)


def require_self_or_admin(user_id: int, current_user: AuthenticatedUser) -> User:
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return current_user


def authorize_user_update(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(require_self_or_admin)],
) -> UserUpdate:
    allowed_fields = {"first_name", "last_name", "email"}
    if current_user.role != UserRole.ADMIN and payload.model_fields_set - allowed_fields:
        raise HTTPException(status_code=403, detail="Only admins may change role or is_active")
    return payload
