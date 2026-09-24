from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import ProfessorProfile, StudentProfile, UserRole

STUDENT = {
    "student_number": "S-001", "department": "Computing", "program": "Software Engineering",
    "year_level": 2, "enrollment_year": 2025, "expected_graduation_year": 2029,
}
PROFESSOR = {
    "employee_number": "P-001", "department": "Computing", "academic_title": "Professor",
    "office_location": "Building A, 101", "research_interests": "Distributed systems",
}
CASES = [
    ("students", UserRole.STUDENT, StudentProfile, STUDENT, "student_number"),
    ("professors", UserRole.PROFESSOR, ProfessorProfile, PROFESSOR, "employee_number"),
]


@pytest.fixture(params=CASES, ids=["student", "professor"])
def profile_case(request):
    return request.param


def create(client, kind, headers, payload):
    response = client.post(f"/api/v1/{kind}/profile", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_read_update_own_profile(client, make_actor, db_session, profile_case):
    kind, role, model, payload, number = profile_case
    user, headers = make_actor(role)
    result = create(client, kind, headers, payload)
    assert result.items() >= payload.items()
    assert result["user_id"] == user.id
    assert result["created_at"] and result["updated_at"]
    profile = db_session.get(model, result["id"])
    assert profile.user.id == user.id
    db_session.expire(user)
    assert getattr(user, "student_profile" if role == UserRole.STUDENT else "professor_profile").id == profile.id
    assert client.get(f"/api/v1/{kind}/me", headers=headers).json() == result
    assert client.get(f"/api/v1/{kind}/{result['id']}", headers=headers).json() == result
    # Use an old timestamp to test onupdate without sleeps or clock precision assumptions.
    profile.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    db_session.commit()
    response = client.patch(f"/api/v1/{kind}/me", headers=headers, json={"department": "Mathematics"})
    assert response.status_code == 200
    assert response.json()["department"] == "Mathematics"
    assert response.json()[number] == payload[number]
    assert response.json()["created_at"] == result["created_at"]
    assert not response.json()["updated_at"].startswith("2000")
    db_session.refresh(profile)
    assert profile.department == "Mathematics"


@pytest.mark.parametrize("caller_role", list(UserRole))
def test_wrong_role_operations(client, make_actor, profile_case, caller_role):
    kind, role, _, payload, _ = profile_case
    if caller_role == role:
        return
    _, headers = make_actor(caller_role)
    assert client.post(f"/api/v1/{kind}/profile", headers=headers, json=payload).status_code == 403
    assert client.get(f"/api/v1/{kind}/me", headers=headers).status_code == 403
    assert client.patch(f"/api/v1/{kind}/me", headers=headers, json={"department": "Math"}).status_code == 403


def test_unauthenticated_requests(client, profile_case):
    kind, _, _, payload, _ = profile_case
    for method, path, body in [
        ("post", "profile", payload), ("get", "me", None),
        ("get", "1", None), ("patch", "me", {"department": "Math"}),
    ]:
        response = client.request(method, f"/api/v1/{kind}/{path}", json=body)
        assert response.status_code == 401


def test_duplicates_on_create_and_update(client, make_actor, profile_case):
    kind, role, _, payload, number = profile_case
    _, first_headers = make_actor(role)
    first = create(client, kind, first_headers, payload)
    assert client.post(f"/api/v1/{kind}/profile", headers=first_headers,
                       json=payload | {number: "different"}).status_code == 409
    _, second_headers = make_actor(role)
    assert client.post(f"/api/v1/{kind}/profile", headers=second_headers, json=payload).status_code == 409
    second = create(client, kind, second_headers, payload | {number: "different"})
    response = client.patch(f"/api/v1/{kind}/me", headers=second_headers,
                            json={number: first[number], "department": "Changed"})
    assert response.status_code == 409
    assert client.get(f"/api/v1/{kind}/me", headers=second_headers).json() == second
    assert client.patch(f"/api/v1/{kind}/me", headers=first_headers,
                        json={number: payload[number]}).status_code == 200


def test_missing_profiles(client, make_actor, profile_case):
    kind, role, _, _, _ = profile_case
    _, headers = make_actor(role)
    for method, path, body in [("get", "me", None), ("get", "999", None),
                               ("patch", "me", {"department": "Math"})]:
        assert client.request(method, f"/api/v1/{kind}/{path}", headers=headers, json=body).status_code == 404


@pytest.mark.parametrize("field,value", [("user_id", 999), ("id", 999), ("created_at", "2026-01-01")])
def test_ownership_and_server_fields_cannot_be_submitted(client, make_actor, profile_case, field, value):
    kind, role, _, payload, _ = profile_case
    user, headers = make_actor(role)
    other, _ = make_actor(role)
    value = other.id if field == "user_id" else value
    assert client.post(f"/api/v1/{kind}/profile", headers=headers,
                       json=payload | {field: value}).status_code == 422
    result = create(client, kind, headers, payload)
    assert client.patch(f"/api/v1/{kind}/me", headers=headers,
                        json={field: value}).status_code == 422
    assert client.get(f"/api/v1/{kind}/me", headers=headers).json() == result
    assert result["user_id"] == user.id


@pytest.mark.parametrize("value", [None, "", "   "])
def test_invalid_patch(client, make_actor, profile_case, value):
    kind, role, _, payload, _ = profile_case
    _, headers = make_actor(role)
    result = create(client, kind, headers, payload)
    assert client.patch(f"/api/v1/{kind}/me", headers=headers, json={"department": value}).status_code == 422
    assert client.get(f"/api/v1/{kind}/me", headers=headers).json() == result


@pytest.mark.parametrize("viewer_role", list(UserRole))
def test_student_privacy(client, make_actor, viewer_role):
    _, owner_headers = make_actor(UserRole.STUDENT)
    profile = create(client, "students", owner_headers, STUDENT)
    _, headers = make_actor(viewer_role)
    response = client.get(f"/api/v1/students/{profile['id']}", headers=headers)
    if viewer_role == UserRole.STUDENT:
        assert response.status_code == 403
        assert STUDENT["student_number"] not in response.text
    else:
        assert response.status_code == 200
        assert response.json() == profile


@pytest.mark.parametrize("viewer_role", list(UserRole))
def test_professor_public_and_admin_views(client, make_actor, viewer_role):
    _, owner_headers = make_actor(UserRole.PROFESSOR)
    profile = create(client, "professors", owner_headers, PROFESSOR)
    _, headers = make_actor(viewer_role)
    response = client.get(f"/api/v1/professors/{profile['id']}", headers=headers)
    assert response.status_code == 200
    if viewer_role == UserRole.ADMIN:
        assert response.json() == profile
    else:
        assert set(response.json()) == {"id", "department", "academic_title", "office_location", "research_interests"}
        assert PROFESSOR["employee_number"] not in response.text


def test_student_year_validation(client, make_actor):
    _, headers = make_actor(UserRole.STUDENT)
    assert client.post("/api/v1/students/profile", headers=headers,
                       json=STUDENT | {"year_level": 0}).status_code == 422
    assert client.post("/api/v1/students/profile", headers=headers,
                       json=STUDENT | {"expected_graduation_year": 2020}).status_code == 422
    profile = create(client, "students", headers, STUDENT)
    assert client.patch("/api/v1/students/me", headers=headers,
                        json={"enrollment_year": 2030}).status_code == 422
    assert client.get("/api/v1/students/me", headers=headers).json() == profile


def test_role_change_cannot_orphan_profile(client, make_actor, profile_case):
    kind, role, _, payload, _ = profile_case
    user, headers = make_actor(role)
    create(client, kind, headers, payload)
    _, admin_headers = make_actor(UserRole.ADMIN)
    assert client.patch(f"/api/v1/users/{user.id}", headers=admin_headers,
                        json={"role": "admin", "first_name": "Changed"}).status_code == 409
    response = client.get(f"/api/v1/users/{user.id}", headers=admin_headers)
    assert response.json()["role"] == role.value
    assert response.json()["first_name"] == "Test"
    assert client.patch(f"/api/v1/users/{user.id}", headers=admin_headers,
                        json={"role": role.value}).status_code == 200


@pytest.mark.parametrize("violation", ["foreign_key", "duplicate_user", "duplicate_number"])
def test_database_constraints(db_session, make_actor, profile_case, violation):
    _, role, model, payload, number = profile_case
    user, _ = make_actor(role)
    db_session.add(model(user_id=user.id, **payload))
    db_session.commit()
    other, _ = make_actor(role)
    user_id = other.id
    values = payload | {number: "another-number"}
    if violation == "foreign_key":
        user_id = 99999
    elif violation == "duplicate_user":
        user_id = user.id
    else:
        values = payload
    db_session.add(model(user_id=user_id, **values))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
