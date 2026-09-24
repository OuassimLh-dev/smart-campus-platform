import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.main import app
from app.models import User  # noqa: F401 -- register model metadata


@pytest.fixture
def db_session():
    # A fresh, isolated database for each test; never read DATABASE_URL.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def auth_settings():
    return Settings(
        _env_file=None, database_url="postgresql+psycopg://test:test@localhost/campus",
        jwt_secret_key="test-only-secret-not-for-production-123456",
        jwt_algorithm="HS256", access_token_expire_minutes=30,
    )


@pytest.fixture
def client(db_session, auth_settings):
    def override_get_db():
        with Session(db_session.get_bind()) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: auth_settings
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        del app.dependency_overrides[get_db]
        del app.dependency_overrides[get_settings]
