import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_from_environment(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-secret-not-for-production-123456")
    url = "postgresql+psycopg://test:test@localhost:5432/campus"
    monkeypatch.setenv("DATABASE_URL", url)
    assert str(Settings(_env_file=None).database_url) == url


def test_database_url_is_required(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-secret-not-for-production-123456")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_application_config_rejects_sqlite(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-secret-not-for-production-123456")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


@pytest.mark.parametrize("changes", [
    {"jwt_secret_key": "short"}, {"jwt_algorithm": "none"},
    {"access_token_expire_minutes": 0},
])
def test_invalid_auth_configuration(changes):
    values = dict(database_url="postgresql://test:test@localhost/campus",
                  jwt_secret_key="test-only-secret-not-for-production-123456")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(values | changes))


def test_jwt_secret_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://test:test@localhost/campus")
