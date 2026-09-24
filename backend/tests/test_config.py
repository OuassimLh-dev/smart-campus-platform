import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_database_url_from_environment(monkeypatch):
    url = "postgresql+psycopg://test:test@localhost:5432/campus"
    monkeypatch.setenv("DATABASE_URL", url)
    assert str(Settings(_env_file=None).database_url) == url


def test_database_url_is_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_application_config_rejects_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
