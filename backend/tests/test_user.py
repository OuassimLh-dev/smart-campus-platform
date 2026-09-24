from datetime import datetime, timezone

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, StatementError

from app.models import User, UserRole
from app.schemas.user import UserCreate, UserRead


def make_user(role=UserRole.STUDENT):
    return User(
        first_name="Ada", last_name="Lovelace", email="ada@example.com", role=role
    )


def test_user_can_be_created(db_session):
    payload = UserCreate(
        first_name="Ada", last_name="Lovelace", email="ada@example.com", role="student"
    )
    user = User(**payload.model_dump())
    db_session.add(user)
    db_session.commit()
    user_id = user.id
    db_session.expunge_all()

    saved = db_session.get(User, user_id)
    assert saved.first_name == "Ada"
    assert saved.last_name == "Lovelace"
    assert saved.email == "ada@example.com"
    assert saved.is_active is True
    assert saved.created_at is not None
    assert saved.updated_at is not None
    result = UserRead.model_validate(saved)
    assert result.id == user_id
    assert result.model_dump(mode="json")["role"] == "student"


def test_email_is_unique(db_session):
    db_session.add(make_user())
    db_session.commit()
    db_session.add(make_user())
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("role", list(UserRole))
def test_roles_round_trip(db_session, role):
    payload = UserCreate(
        first_name="Ada", last_name="Lovelace", email="ada@example.com", role=role.value
    )
    assert payload.role is role
    user = make_user(role.value)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.role is role
    assert db_session.execute(text("SELECT role FROM users")).scalar_one() == role.value


def test_updated_at_changes_on_update(db_session):
    user = make_user()
    user.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    previous_updated_at = user.updated_at
    created_at = user.created_at

    user.first_name = "Augusta"
    db_session.commit()
    db_session.refresh(user)
    assert user.updated_at > previous_updated_at
    assert user.created_at == created_at


def test_invalid_role_rejected_by_orm(db_session):
    db_session.add(make_user("invalid"))
    with pytest.raises(StatementError):
        db_session.commit()
    db_session.rollback()


def test_invalid_role_rejected_by_database(db_session):
    with pytest.raises(IntegrityError):
        db_session.execute(text(
            "INSERT INTO users (first_name, last_name, email, role) "
            "VALUES ('Ada', 'Lovelace', 'ada@example.com', 'invalid')"
        ))
    db_session.rollback()


@pytest.mark.parametrize("overrides", [
    {"email": "invalid"}, {"role": "invalid"}, {"first_name": " "},
])
def test_user_schema_rejects_invalid_input(overrides):
    values = dict(first_name="Ada", last_name="Lovelace", email="ada@example.com", role="student")
    with pytest.raises(ValidationError):
        UserCreate(**(values | overrides))
