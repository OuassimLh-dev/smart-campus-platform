import pytest

from app.models.user import User

URL = "/api/v1/users"


@pytest.fixture(autouse=True)
def authenticate_admin(client, admin_headers):
    client.headers.update(admin_headers)


def user_payload(**overrides):
    return {
        "first_name": "Ada", "last_name": "Lovelace",
        "email": "ada@example.com", "role": "student", **overrides,
    }


def create_user(client, **overrides):
    response = client.post(URL, json=user_payload(**overrides))
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("role", ["student", "professor", "admin"])
def test_create_user(client, db_session, role):
    user = create_user(client, role=role)
    assert user.items() >= user_payload(role=role).items()
    assert user["is_active"] is True
    assert user["created_at"]
    assert user["updated_at"]
    assert db_session.get(User, user["id"]).email == user["email"]


def test_duplicate_email(client):
    create_user(client)
    response = client.post(URL, json=user_payload())
    assert response.status_code == 409
    assert len(client.get(URL).json()) == 2
    create_user(client, email="another@example.com")


def test_list_users(client):
    initial_users = client.get(URL).json()
    first = create_user(client)
    second = create_user(client, email="grace@example.com")
    response = client.get(URL)
    assert response.status_code == 200
    assert response.json() == initial_users + [first, second]


def test_pagination(client):
    users = client.get(URL).json()
    users += [create_user(client, email=f"user{i}@example.com") for i in range(22)]
    assert client.get(URL).json() == users[:20]
    assert client.get(URL, params={"skip": 2, "limit": 3}).json() == users[2:5]
    assert client.get(URL, params={"limit": 100}).json() == users
    assert client.get(URL, params={"skip": len(users)}).json() == []


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}])
def test_invalid_pagination(client, params):
    assert client.get(URL, params=params).status_code == 422


def test_get_user(client):
    user = create_user(client)
    response = client.get(f"{URL}/{user['id']}")
    assert response.status_code == 200
    assert response.json() == user


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_nonexistent_user(client, method):
    kwargs = {"json": {"first_name": "Grace"}} if method == "patch" else {}
    assert getattr(client, method)(f"{URL}/999", **kwargs).status_code == 404


def test_update_user(client):
    user = create_user(client)
    changes = user_payload(
        first_name="Grace", last_name="Hopper", email="grace@example.com",
        role="professor", is_active=False,
    )
    response = client.patch(f"{URL}/{user['id']}", json=changes)
    assert response.status_code == 200
    assert response.json().items() >= changes.items()
    assert response.json()["id"] == user["id"]
    assert client.get(f"{URL}/{user['id']}").json() == response.json()


def test_partial_update_and_unchanged_email(client):
    user = create_user(client)
    path = f"{URL}/{user['id']}"
    response = client.patch(path, json={"first_name": "Grace", "email": user["email"]})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Grace"
    for field in ("last_name", "email", "role", "is_active", "created_at"):
        assert response.json()[field] == user[field]
    assert client.patch(path, json={}).status_code == 200


def test_duplicate_email_on_update(client):
    first = create_user(client)
    second = create_user(client, email="second@example.com")
    path = f"{URL}/{second['id']}"
    response = client.patch(path, json={"email": first["email"], "first_name": "Changed"})
    assert response.status_code == 409
    assert client.get(path).json() == second


def test_soft_delete(client, db_session):
    user = create_user(client)
    path = f"{URL}/{user['id']}"
    response = client.delete(path)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert response.json()["id"] == user["id"]
    stored = db_session.get(User, user["id"])
    assert stored is not None
    assert stored.is_active is False
    assert client.get(path).json()["is_active"] is False
    assert len(client.get(URL).json()) == 2
    assert client.delete(path).status_code == 200
    assert client.post(URL, json=user_payload()).status_code == 409


@pytest.mark.parametrize("changes", [
    {"first_name": None}, {"last_name": None}, {"email": None},
    {"role": None}, {"is_active": None}, {"first_name": " "},
    {"email": "invalid"}, {"role": "invalid"}, {"id": 50},
])
def test_invalid_update(client, changes):
    user = create_user(client)
    path = f"{URL}/{user['id']}"
    assert client.patch(path, json=changes).status_code == 422
    assert client.get(path).json() == user
