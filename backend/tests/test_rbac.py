import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.authorization import require_professor_or_admin
from app.models.user import User, UserRole

URL = "/api/v1/users"
NORMAL_ROLES = [UserRole.STUDENT, UserRole.PROFESSOR]


@pytest.mark.parametrize("method,path,body", [
    ("get", URL, None), ("post", URL, {"first_name": "Ada", "last_name": "Lovelace",
                                       "email": "ada@example.com", "role": "admin"}),
    ("get", f"{URL}/1", None), ("patch", f"{URL}/1", {"first_name": "Ada"}),
    ("delete", f"{URL}/1", None),
])
def test_unauthenticated_user_management(client, method, path, body):
    response = client.request(method, path, json=body)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("role", list(UserRole))
def test_list_users_permissions(client, make_actor, role):
    _, headers = make_actor(role)
    response = client.get(URL, headers=headers)
    assert response.status_code == (200 if role == UserRole.ADMIN else 403)


@pytest.mark.parametrize("role", NORMAL_ROLES)
def test_normal_user_can_read_and_edit_self(client, make_actor, role):
    user, headers = make_actor(role)
    path = f"{URL}/{user.id}"
    response = client.get(path, headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == user.id
    changes = {"first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com"}
    response = client.patch(path, headers=headers, json=changes)
    assert response.status_code == 200
    assert response.json().items() >= changes.items()
    assert response.json()["role"] == role.value
    assert response.json()["is_active"] is True
    assert client.get(path, headers=headers).json() == response.json()


@pytest.mark.parametrize("role", NORMAL_ROLES)
@pytest.mark.parametrize("changes", [
    {"role": "admin"}, {"role": "student"}, {"is_active": False},
    {"is_active": True}, {"first_name": "Changed", "role": "admin"},
])
def test_normal_user_cannot_modify_privileged_fields(client, make_actor, db_session, role, changes):
    user, headers = make_actor(role)
    response = client.patch(f"{URL}/{user.id}", json=changes, headers=headers)
    assert response.status_code == 403
    db_session.refresh(user)
    assert user.role == role
    assert user.is_active is True
    assert user.first_name == "Test"


@pytest.mark.parametrize("role", NORMAL_ROLES)
@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_normal_user_cannot_access_others(client, make_actor, db_session, role, method):
    _, headers = make_actor(role)
    target, _ = make_actor()
    kwargs = {"json": {"first_name": "Changed"}} if method == "patch" else {}
    response = client.request(method, f"{URL}/{target.id}", headers=headers, **kwargs)
    assert response.status_code == 403
    db_session.refresh(target)
    assert target.first_name == "Test"
    assert target.is_active is True
    # Do not disclose whether another user's identifier exists.
    assert client.request(method, f"{URL}/99999", headers=headers, **kwargs).status_code == 403


@pytest.mark.parametrize("role", NORMAL_ROLES)
def test_normal_user_cannot_delete_self_or_create_users(client, make_actor, role):
    user, headers = make_actor(role)
    assert client.delete(f"{URL}/{user.id}", headers=headers).status_code == 403
    response = client.post(URL, headers=headers, json={
        "first_name": "New", "last_name": "Admin", "email": "admin@example.com", "role": "admin",
    })
    assert response.status_code == 403


def test_admin_can_manage_another_user(client, make_actor, db_session):
    _, headers = make_actor(UserRole.ADMIN)
    target, _ = make_actor()
    path = f"{URL}/{target.id}"
    assert client.get(path, headers=headers).json()["id"] == target.id
    response = client.patch(path, headers=headers, json={"role": "professor", "is_active": False})
    assert response.status_code == 200
    assert response.json()["role"] == "professor"
    assert response.json()["is_active"] is False
    assert client.patch(path, headers=headers, json={"is_active": True}).status_code == 200
    response = client.delete(path, headers=headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    db_session.expire_all()
    assert db_session.get(User, target.id) is not None
    assert db_session.get(User, target.id).is_active is False


def test_role_changes_apply_to_existing_token(client, make_actor, db_session):
    actor, headers = make_actor(UserRole.ADMIN)
    assert client.get(URL, headers=headers).status_code == 200
    actor.role = UserRole.STUDENT
    db_session.commit()
    assert client.get(URL, headers=headers).status_code == 403
    actor.is_active = False
    db_session.commit()
    assert client.get(URL, headers=headers).status_code == 401


@pytest.mark.parametrize("role", ["professor", "admin"])
def test_public_registration_cannot_grant_privileges(client, role):
    response = client.post("/api/v1/auth/register", json={
        "first_name": "New", "last_name": "User", "email": "new@example.com",
        "password": "long-test-password", "role": role,
    })
    assert response.status_code == 422


@pytest.mark.parametrize("role,expected", [
    (None, 401), (UserRole.STUDENT, 403), (UserRole.PROFESSOR, 200), (UserRole.ADMIN, 200),
])
def test_professor_or_admin_dependency(client, make_actor, role, expected):
    # Exercise the reusable dependency without adding a production endpoint.
    probe = FastAPI()
    probe.dependency_overrides.update(client.app.dependency_overrides)

    @probe.get("/probe", dependencies=[Depends(require_professor_or_admin)])
    def protected():
        return {"ok": True}

    headers = make_actor(role)[1] if role is not None else {}
    with TestClient(probe) as probe_client:
        assert probe_client.get("/probe", headers=headers).status_code == expected
