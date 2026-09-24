from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.models.user import User

AUTH = "/api/v1/auth"
PASSWORD = "a-long-test-password"


def registration(**changes):
    return {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com",
            "password": PASSWORD, "role": "student", **changes}


def register(client):
    response = client.post(f"{AUTH}/register", json=registration())
    assert response.status_code == 201
    return response.json()


def login(client, **changes):
    return client.post(f"{AUTH}/login", json={
        "email": "ada@example.com", "password": PASSWORD, **changes,
    })


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def assert_no_credentials(response):
    assert PASSWORD not in response.text
    assert "hashed_password" not in response.text
    assert '"password"' not in response.text
    assert "$argon2" not in response.text


def test_password_hashing():
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert first.startswith("$argon2id$")
    assert first != second
    assert PASSWORD not in first
    assert verify_password(PASSWORD, first)
    assert not verify_password("wrong", first)
    assert not verify_password(PASSWORD, None)


@pytest.mark.parametrize("role", ["student", "professor", "admin"])
def test_registration(client, db_session, role):
    response = client.post(f"{AUTH}/register", json=registration(role=role))
    assert response.status_code == 201
    user = response.json()
    assert user["role"] == role
    assert user["is_active"] is True
    assert user["email"] == "ada@example.com"
    stored = db_session.get(User, user["id"])
    assert stored.hashed_password != PASSWORD
    assert verify_password(PASSWORD, stored.hashed_password)
    assert_no_credentials(response)


def test_duplicate_registration(client):
    register(client)
    response = client.post(f"{AUTH}/register", json=registration())
    assert response.status_code == 409
    assert_no_credentials(response)


def test_valid_login_and_me(client, auth_settings):
    user = register(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    token = response.json()["access_token"]
    claims = jwt.decode(token, auth_settings.jwt_secret_key.get_secret_value(), algorithms=["HS256"])
    assert claims["sub"] == str(user["id"])
    assert claims["exp"] - claims["iat"] == 30 * 60
    assert set(claims) == {"sub", "iat", "exp"}
    me = client.get(f"{AUTH}/me", headers=bearer(token))
    assert me.status_code == 200
    assert me.json() == user
    assert_no_credentials(response)
    assert_no_credentials(me)


@pytest.mark.parametrize("changes", [{"password": "wrong"}, {"email": "nobody@example.com"}])
def test_invalid_credentials(client, changes):
    register(client)
    response = login(client, **changes)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": "Invalid authentication credentials"}
    assert_no_credentials(response)


@pytest.mark.parametrize("headers", [{}, bearer("invalid"), {"Authorization": "Basic abc"}])
def test_me_rejects_missing_or_invalid_token(client, headers):
    response = client.get(f"{AUTH}/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("kind", ["expired", "wrong_key", "wrong_algorithm", "missing_exp", "bad_sub", "huge_sub", "unknown_user"])
def test_me_rejects_invalid_claims(client, auth_settings, kind):
    user = register(client)
    now = datetime.now(timezone.utc)
    claims = {"sub": str(user["id"]), "iat": now, "exp": now + timedelta(minutes=30)}
    key = auth_settings.jwt_secret_key.get_secret_value()
    algorithm = "HS256"
    if kind == "expired":
        claims["exp"] = now - timedelta(seconds=1)
    elif kind == "wrong_key":
        key = "different-test-secret-abcdefghijklmnopqrstuvwxyz"
    elif kind == "wrong_algorithm":
        algorithm = "HS384"
        key = key * 2
    elif kind == "missing_exp":
        del claims["exp"]
    elif kind == "bad_sub":
        claims["sub"] = "not-an-id"
    elif kind == "huge_sub":
        claims["sub"] = "9" * 100
    else:
        claims["sub"] = "9999"
    token = jwt.encode(claims, key, algorithm=algorithm)
    assert client.get(f"{AUTH}/me", headers=bearer(token)).status_code == 401


def test_inactive_user_cannot_authenticate(client):
    user = register(client)
    token = login(client).json()["access_token"]
    client.delete(f"/api/v1/users/{user['id']}")
    assert login(client).status_code == 401
    assert client.get(f"{AUTH}/me", headers=bearer(token)).status_code == 401


def test_passwordless_user_cannot_login(client):
    payload = registration()
    del payload["password"]
    assert client.post("/api/v1/users", json=payload).status_code == 201
    assert login(client).status_code == 401


def test_existing_user_endpoints_never_expose_hash(client, db_session):
    user = register(client)
    path = f"/api/v1/users/{user['id']}"
    stored_hash = db_session.scalar(select(User.hashed_password))
    for response in (
        client.get("/api/v1/users"), client.get(path),
        client.patch(path, json={"first_name": "Grace"}), client.delete(path),
    ):
        assert response.status_code == 200
        assert_no_credentials(response)
        assert stored_hash not in response.text


@pytest.mark.parametrize("password", ["abc!7", "x" * 129])
def test_registration_password_validation_redacts_input(client, password):
    response = client.post(f"{AUTH}/register", json=registration(password=password))
    assert response.status_code == 422
    assert password not in response.text
    assert "input" not in response.text


def test_validation_error_does_not_echo_entire_payload(client):
    response = client.post(f"{AUTH}/register", json=[registration()])
    assert response.status_code == 422
    assert PASSWORD not in response.text
