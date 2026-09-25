from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Course, Department, ProfessorProfile, UserRole

DEPARTMENTS = "/api/v1/departments"
COURSES = "/api/v1/courses"


@pytest.fixture
def department(db_session):
    record = Department(code="SE", name="Software Engineering")
    db_session.add(record)
    db_session.commit()
    return record


@pytest.fixture
def professor(db_session, make_actor):
    user, _ = make_actor(UserRole.PROFESSOR)
    record = ProfessorProfile(user_id=user.id, employee_number="EMP-001", department="Computing",
                              academic_title="Professor", office_location="A-101", research_interests="Systems")
    db_session.add(record)
    db_session.commit()
    return record


@pytest.fixture(params=["department", "course"])
def resource(request, department):
    if request.param == "department":
        return DEPARTMENTS, Department, {"code": "CS", "name": "Computer Science"}
    return COURSES, Course, {"code": "SE101", "title": "Introduction to Software Engineering",
                             "credits": 3, "department_id": department.id}


def create(client, url, headers, payload):
    response = client.post(url, headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_admin_create_defaults(client, admin_headers, db_session, resource):
    url, model, payload = resource
    record = create(client, url, admin_headers, payload)
    assert record.items() >= payload.items()
    assert record["is_active"] is True
    assert record["description"] is None
    assert record["created_at"] and record["updated_at"]
    assert db_session.get(model, record["id"]).code == payload["code"]
    if model is Course:
        assert record["professor_id"] is None


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.PROFESSOR])
def test_nonadmin_cannot_write(client, make_actor, admin_headers, db_session, resource, role):
    url, model, payload = resource
    record = create(client, url, admin_headers, payload)
    _, headers = make_actor(role)
    assert client.post(url, headers=headers, json=payload).status_code == 403
    assert client.patch(f"{url}/{record['id']}", headers=headers, json={"code": "Changed"}).status_code == 403
    assert client.delete(f"{url}/{record['id']}", headers=headers).status_code == 403
    saved = db_session.get(model, record["id"])
    assert saved.code == payload["code"] and saved.is_active


def test_unauthenticated_requests(client, resource):
    url, _, payload = resource
    for method, path, body in [("post", url, payload), ("get", url, None),
                               ("get", f"{url}/1", None), ("patch", f"{url}/1", {"code": "X"}),
                               ("delete", f"{url}/1", None)]:
        response = client.request(method, path, json=body)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("role", list(UserRole))
def test_authenticated_read(client, make_actor, admin_headers, resource, role):
    url, _, payload = resource
    record = create(client, url, admin_headers, payload)
    _, headers = make_actor(role)
    response = client.get(url, headers=headers)
    assert response.status_code == 200
    assert record in response.json()
    response = client.get(f"{url}/{record['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json() == record


def test_duplicate_code_and_atomic_update(client, admin_headers, resource):
    url, model, payload = resource
    first = create(client, url, admin_headers, payload)
    assert client.post(url, headers=admin_headers, json=payload).status_code == 409
    changes = {"code": "OTHER"}
    if model is Department:
        changes["name"] = "Other department"
    second = create(client, url, admin_headers, payload | changes)
    response = client.patch(f"{url}/{second['id']}", headers=admin_headers,
                            json={"code": first["code"], "description": "Should not persist"})
    assert response.status_code == 409
    assert client.get(f"{url}/{second['id']}", headers=admin_headers).json() == second
    assert client.patch(f"{url}/{first['id']}", headers=admin_headers, json={"code": first["code"]}).status_code == 200


def test_duplicate_department_name(client, admin_headers):
    first = create(client, DEPARTMENTS, admin_headers, {"code": "SE", "name": "Software Engineering"})
    assert client.post(DEPARTMENTS, headers=admin_headers,
                       json={"code": "OTHER", "name": first["name"]}).status_code == 409
    second = create(client, DEPARTMENTS, admin_headers, {"code": "CS", "name": "Computer Science"})
    assert client.patch(f"{DEPARTMENTS}/{second['id']}", headers=admin_headers,
                        json={"name": first["name"]}).status_code == 409


def test_update_and_soft_delete(client, admin_headers, db_session, resource):
    url, model, payload = resource
    record = create(client, url, admin_headers, payload)
    path = f"{url}/{record['id']}"
    stored = db_session.get(model, record["id"])
    stored.updated_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
    db_session.commit()
    changes = {"code": "NEW", "description": "Updated description"}
    changes["name" if model is Department else "title"] = "Updated title"
    if model is Course:
        changes["credits"] = 4
    response = client.patch(path, headers=admin_headers, json=changes)
    assert response.status_code == 200
    assert response.json().items() >= changes.items()
    assert response.json()["created_at"] == record["created_at"]
    assert not response.json()["updated_at"].startswith("2000")
    assert client.patch(path, headers=admin_headers, json={"description": None}).json()["description"] is None
    response = client.delete(path, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    db_session.refresh(stored)
    assert stored.is_active is False
    assert client.get(path, headers=admin_headers).status_code == 200
    assert record["id"] not in [item["id"] for item in client.get(url, headers=admin_headers).json()]
    assert client.delete(path, headers=admin_headers).status_code == 200
    assert client.patch(path, headers=admin_headers, json={"is_active": True}).json()["is_active"] is True


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_record(client, admin_headers, resource, method):
    url, _, _ = resource
    kwargs = {"json": {"code": "X"}} if method == "patch" else {}
    assert client.request(method, f"{url}/99999", headers=admin_headers, **kwargs).status_code == 404


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}, {"limit": "invalid"}])
def test_invalid_pagination(client, admin_headers, resource, params):
    assert client.get(resource[0], headers=admin_headers, params=params).status_code == 422


def test_active_pagination(client, admin_headers, db_session, resource):
    url, model, payload = resource
    for index in range(23):
        values = payload | {"code": f"CODE-{index}", "is_active": index != 0}
        if model is Department:
            values["name"] = f"Department {index}"
        db_session.add(model(**values))
    db_session.commit()
    all_records = client.get(url, headers=admin_headers, params={"limit": 100}).json()
    assert all(item["is_active"] for item in all_records)
    assert [item["id"] for item in all_records] == sorted(item["id"] for item in all_records)
    assert client.get(url, headers=admin_headers).json() == all_records[:20]
    assert client.get(url, headers=admin_headers, params={"skip": 2, "limit": 3}).json() == all_records[2:5]
    assert client.get(url, headers=admin_headers, params={"skip": 100}).json() == []


@pytest.mark.parametrize("changes", [{"code": None}, {"code": " "}, {"is_active": None}, {"id": 99}])
def test_invalid_patch(client, admin_headers, resource, changes):
    url, _, payload = resource
    record = create(client, url, admin_headers, payload)
    path = f"{url}/{record['id']}"
    assert client.patch(path, headers=admin_headers, json=changes).status_code == 422
    assert client.get(path, headers=admin_headers).json() == record


@pytest.mark.parametrize("credits", [0, -1, 1.5, True, None])
def test_invalid_credits(client, admin_headers, department, credits):
    payload = {"code": "C1", "title": "Course", "credits": 3, "department_id": department.id}
    assert client.post(COURSES, headers=admin_headers, json=payload | {"credits": credits}).status_code == 422
    record = create(client, COURSES, admin_headers, payload)
    assert client.patch(f"{COURSES}/{record['id']}", headers=admin_headers,
                        json={"credits": credits}).status_code == 422


@pytest.mark.parametrize("field", ["department_id", "professor_id"])
def test_invalid_references(client, admin_headers, department, field):
    payload = {"code": "C1", "title": "Course", "credits": 3, "department_id": department.id}
    response = client.post(COURSES, headers=admin_headers, json=payload | {field: 99999})
    assert response.status_code == 404
    record = create(client, COURSES, admin_headers, payload)
    assert client.patch(f"{COURSES}/{record['id']}", headers=admin_headers,
                        json={field: 99999, "title": "Changed"}).status_code == 404
    assert client.get(f"{COURSES}/{record['id']}", headers=admin_headers).json() == record


def test_assign_reassign_unassign_and_relationships(client, admin_headers, department, professor, db_session):
    record = create(client, COURSES, admin_headers, {
        "code": "C1", "title": "Course", "credits": 3,
        "department_id": department.id, "professor_id": professor.id,
    })
    stored = db_session.get(Course, record["id"])
    assert stored.department.id == department.id
    assert stored.professor.id == professor.id
    assert stored in department.courses
    assert stored in professor.courses
    other = Department(code="MATH", name="Mathematics")
    db_session.add(other)
    db_session.commit()
    response = client.patch(f"{COURSES}/{record['id']}", headers=admin_headers,
                            json={"department_id": other.id, "professor_id": None})
    assert response.status_code == 200
    assert response.json()["department_id"] == other.id
    assert response.json()["professor_id"] is None
    assert client.patch(f"{COURSES}/{record['id']}", headers=admin_headers,
                        json={"professor_id": professor.id}).json()["professor_id"] == professor.id


def test_course_filters(client, admin_headers, department, professor, db_session):
    other = Department(code="MATH", name="Mathematics")
    db_session.add(other)
    db_session.commit()
    base = {"title": "Course", "credits": 3}
    first = create(client, COURSES, admin_headers, base | {"code": "C1", "department_id": department.id, "professor_id": professor.id})
    second = create(client, COURSES, admin_headers, base | {"code": "C2", "department_id": other.id, "professor_id": professor.id})
    third = create(client, COURSES, admin_headers, base | {"code": "C3", "department_id": department.id})
    create(client, COURSES, admin_headers, base | {"code": "C4", "department_id": department.id, "professor_id": professor.id, "is_active": False})
    def filtered(**params):
        response = client.get(COURSES, headers=admin_headers, params=params)
        assert response.status_code == 200
        return response.json()
    assert filtered(department_id=department.id) == [first, third]
    assert filtered(professor_id=professor.id) == [first, second]
    assert filtered(department_id=department.id, professor_id=professor.id) == [first]
    assert filtered(professor_id=professor.id, skip=1, limit=1) == [second]
    assert filtered(department_id=99999) == []
    assert filtered(professor_id=99999) == []


@pytest.mark.parametrize("violation", ["code", "name", "blank_code", "blank_name"])
def test_department_database_constraints(db_session, department, violation):
    values = {"code": "OTHER", "name": "Other"}
    if violation in {"code", "name"}:
        values[violation] = getattr(department, violation)
    else:
        values[violation.removeprefix("blank_")] = " "
    db_session.add(Department(**values))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


@pytest.mark.parametrize("changes", [{"code": "C1"}, {"credits": 0}, {"department_id": 99999},
                                      {"professor_id": 99999}, {"title": " "}])
def test_course_database_constraints(db_session, department, changes):
    values = {"code": "C1", "title": "Course", "credits": 3, "department_id": department.id}
    db_session.add(Course(**values))
    db_session.commit()
    db_session.add(Course(**(values | {"code": "C2"} | changes)))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
