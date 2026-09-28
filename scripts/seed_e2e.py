"""Test-only seed streamed into the disposable backend; never bundled in images."""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_engine, get_session_factory
from app.models import User, UserRole

engine = get_engine()
if engine.url.host != "db" or engine.url.database != "smart_campus_e2e":
    raise SystemExit("Refusing to seed anything except the disposable E2E database")

with get_session_factory()() as session:
    if session.scalar(select(User.id).limit(1)) is not None:
        raise SystemExit("E2E seed requires a fresh, empty users table")
    for role in UserRole:
        session.add(User(
            first_name=role.value.capitalize(), last_name="E2E",
            email=f"{role.value}.e2e@example.com", role=role,
            hashed_password=hash_password("Fake-E2E-Password-Only-123!"),
            is_active=True,
        ))
    session.commit()
print("Seeded three fake E2E accounts")
