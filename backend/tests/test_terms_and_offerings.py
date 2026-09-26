import pytest

from app.models import AcademicTerm, CourseOffering

TERMS = "/api/v1/terms"
OFFERINGS = "/api/v1/course-offerings"
TERM = {"name": "Spring", "academic_year": "2026-2027", "start_date": "2027-01-01", "end_date": "2027-05-31"}


def offering_payload(setup, **changes):
    return dict(course_id=setup["course"].id, professor_id=setup["professor"].id,
                term_id=setup["term"].id, section="B", capacity=30, **changes)


def test_admin_create_and_update_term(client, academic_setup):
    headers = academic_setup["admin_headers"]
    response = client.post(TERMS, headers=headers, json=TERM)
    assert response.status_code == 201
    record = response.json()
    assert record.items() >= TERM.items()
    assert record["is_active"] is True
    assert record["created_at"] and record["updated_at"]
    path = f"{TERMS}/{record['id']}"
    response = client.patch(path, headers=headers, json={"name": "Spring revised", "is_active": False})
    assert response.status_code == 200
    assert response.json()["name"] == "Spring revised"
    assert response.json()["is_active"] is False


def test_term_duplicate_and_date_validation(client, academic_setup):
    headers = academic_setup["admin_headers"]
    first = client.post(TERMS, headers=headers, json=TERM).json()
    assert client.post(TERMS, headers=headers, json=TERM).status_code == 409
    second = client.post(TERMS, headers=headers, json=TERM | {"name": "Summer"}).json()
    assert client.patch(f"{TERMS}/{second['id']}", headers=headers, json={"name": "Spring"}).status_code == 409
    for end in ("2027-01-01", "2026-01-01"):
        assert client.post(TERMS, headers=headers, json=TERM | {"end_date": end}).status_code == 422
    assert client.patch(f"{TERMS}/{first['id']}", headers=headers, json={"start_date": "2028-01-01"}).status_code == 422
    assert client.get(f"{TERMS}/{first['id']}", headers=headers).json() == first
    assert client.post(TERMS, headers=headers, json=TERM | {"academic_year": "2027-2028"}).status_code == 201


@pytest.mark.parametrize("actor", ["student_headers", "professor_headers", "admin_headers"])
def test_authenticated_term_and_offering_reads(client, academic_setup, actor):
    for url, key in [(TERMS, "term"), (OFFERINGS, "offering")]:
        headers = academic_setup[actor]
        response = client.get(url, headers=headers)
        assert response.status_code == 200
        assert response.json()[0]["id"] == academic_setup[key].id
        assert client.get(f"{url}/{academic_setup[key].id}", headers=headers).status_code == 200


@pytest.mark.parametrize("actor", ["student_headers", "professor_headers"])
def test_nonadmin_cannot_manage_terms_or_offerings(client, academic_setup, actor):
    setup = academic_setup
    for url, key, body in [(TERMS, "term", TERM), (OFFERINGS, "offering", offering_payload(setup))]:
        assert client.post(url, headers=setup[actor], json=body).status_code == 403
        assert client.patch(f"{url}/{setup[key].id}", headers=setup[actor], json=body).status_code == 403


def test_admin_create_and_update_offering(client, academic_setup):
    setup = academic_setup
    headers = setup["admin_headers"]
    payload = offering_payload(setup)
    response = client.post(OFFERINGS, headers=headers, json=payload)
    assert response.status_code == 201
    record = response.json()
    assert record.items() >= payload.items()
    assert record["is_open"] is True
    assert client.post(OFFERINGS, headers=headers, json=payload).status_code == 409
    path = f"{OFFERINGS}/{record['id']}"
    assert client.patch(path, headers=headers, json={"section": "A"}).status_code == 409
    changes = {"professor_id": setup["other_professor"].id, "capacity": 40, "is_open": False}
    response = client.patch(path, headers=headers, json=changes)
    assert response.status_code == 200
    assert response.json().items() >= changes.items()


@pytest.mark.parametrize("field", ["course_id", "professor_id", "term_id"])
def test_offering_reference_validation(client, academic_setup, field):
    setup = academic_setup
    headers = setup["admin_headers"]
    assert client.post(OFFERINGS, headers=headers, json=offering_payload(setup) | {field: 99999}).status_code == 404
    assert client.patch(f"{OFFERINGS}/{setup['offering'].id}", headers=headers, json={field: 99999}).status_code == 404


@pytest.mark.parametrize("changes", [{"capacity": 0}, {"capacity": -1}, {"capacity": 1.5},
                                      {"professor_id": None}, {"section": " "}])
def test_offering_invalid_values(client, academic_setup, changes):
    setup = academic_setup
    assert client.post(OFFERINGS, headers=setup["admin_headers"], json=offering_payload(setup) | changes).status_code == 422
    assert client.patch(f"{OFFERINGS}/{setup['offering'].id}", headers=setup["admin_headers"], json=changes).status_code == 422


def test_offering_filters_and_pagination(client, academic_setup, db_session):
    setup = academic_setup
    first = setup["offering"]
    second = CourseOffering(course_id=first.course_id, professor_id=setup["other_professor"].id,
                            term_id=first.term_id, section="B", capacity=2, is_open=False)
    db_session.add(second)
    db_session.commit()
    def ids(**params):
        response = client.get(OFFERINGS, headers=setup["student_headers"], params=params)
        assert response.status_code == 200
        return [item["id"] for item in response.json()]
    assert ids(course_id=first.course_id) == [first.id, second.id]
    assert ids(term_id=first.term_id) == [first.id, second.id]
    assert ids(professor_id=first.professor_id) == [first.id]
    assert ids(is_open=False) == [second.id]
    assert ids(is_open=True, professor_id=first.professor_id, course_id=first.course_id, term_id=first.term_id) == [first.id]
    assert ids(skip=1, limit=1) == [second.id]
    assert ids(course_id=99999) == []


@pytest.mark.parametrize("url", [TERMS, OFFERINGS])
def test_missing_and_pagination(client, academic_setup, url):
    headers = academic_setup["admin_headers"]
    assert client.get(f"{url}/99999", headers=headers).status_code == 404
    assert client.patch(f"{url}/99999", headers=headers, json={}).status_code == 404
    for params in ({"skip": -1}, {"limit": 0}, {"limit": 101}):
        assert client.get(url, headers=headers, params=params).status_code == 422


def test_default_and_maximum_page_size(client, academic_setup, db_session):
    setup = academic_setup
    for i in range(22):
        db_session.add(AcademicTerm(name=f"Term {i}", academic_year="2028-2029",
                                   start_date=setup["term"].start_date, end_date=setup["term"].end_date))
        db_session.add(CourseOffering(course_id=setup["course"].id, professor_id=setup["professor"].id,
                                     term_id=setup["term"].id, section=f"Section {i}", capacity=10))
    db_session.commit()
    for url in (TERMS, OFFERINGS):
        assert len(client.get(url, headers=setup["admin_headers"]).json()) == 20
        assert len(client.get(url, headers=setup["admin_headers"], params={"limit": 100}).json()) == 23
