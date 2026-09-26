import pytest
from sqlalchemy.exc import IntegrityError

from app.models import AcademicTerm, CourseOffering, Enrollment, EnrollmentStatus, Grade, UserRole

ENROLLMENTS = "/api/v1/enrollments"
OFFERINGS = "/api/v1/course-offerings"


def enroll(client, setup, actor="student_headers"):
    response = client.post(ENROLLMENTS, headers=setup[actor], json={"course_offering_id": setup["offering"].id})
    assert response.status_code == 201, response.text
    return response.json()


def grade_path(enrollment):
    return f"{ENROLLMENTS}/{enrollment['id']}/grade"


def test_student_enrolls_self_and_relationships(client, academic_setup, db_session):
    setup = academic_setup
    result = enroll(client, setup)
    assert result["student_id"] == setup["student"].id
    assert result["course_offering_id"] == setup["offering"].id
    assert result["status"] == "enrolled"
    assert result["enrolled_at"] and result["created_at"] and result["updated_at"]
    saved = db_session.get(Enrollment, result["id"])
    assert saved.student.id == setup["student"].id
    assert saved.offering.course.id == setup["course"].id
    assert saved.offering.term.id == setup["term"].id
    assert saved.offering.professor.id == setup["professor"].id


@pytest.mark.parametrize("actor", ["professor_headers", "admin_headers"])
def test_only_students_can_enroll(client, academic_setup, actor):
    setup = academic_setup
    assert client.post(ENROLLMENTS, headers=setup[actor], json={"course_offering_id": setup["offering"].id}).status_code == 403
    assert client.get(f"{ENROLLMENTS}/me", headers=setup[actor]).status_code == 403
    assert client.get("/api/v1/grades/me", headers=setup[actor]).status_code == 403


def test_enrollment_rejects_client_controlled_identity_and_status(client, academic_setup):
    setup = academic_setup
    for changes in ({"student_id": setup["other_student"].id}, {"status": "completed"}):
        assert client.post(ENROLLMENTS, headers=setup["student_headers"],
                           json={"course_offering_id": setup["offering"].id} | changes).status_code == 422


def test_duplicate_closed_full_and_drop_capacity(client, academic_setup, db_session):
    setup = academic_setup
    offering_path = f"{OFFERINGS}/{setup['offering'].id}"
    assert client.patch(offering_path, headers=setup["admin_headers"], json={"capacity": 1}).status_code == 200
    first = enroll(client, setup)
    payload = {"course_offering_id": setup["offering"].id}
    assert client.post(ENROLLMENTS, headers=setup["student_headers"], json=payload).status_code == 409
    response = client.post(ENROLLMENTS, headers=setup["other_student_headers"], json=payload)
    assert response.status_code == 409 and response.json()["detail"] == "Offering is full"
    drop_path = f"{ENROLLMENTS}/{first['id']}/drop"
    response = client.patch(drop_path, headers=setup["student_headers"])
    assert response.status_code == 200 and response.json()["status"] == "dropped"
    assert client.patch(drop_path, headers=setup["student_headers"]).status_code == 200
    db_session.expire_all()
    assert db_session.get(Enrollment, first["id"]).status == EnrollmentStatus.DROPPED
    # Historical duplicate enrollment remains rejected even after dropping.
    assert client.post(ENROLLMENTS, headers=setup["student_headers"], json=payload).status_code == 409
    assert client.patch(offering_path, headers=setup["admin_headers"], json={"is_open": False}).status_code == 200
    response = client.post(ENROLLMENTS, headers=setup["other_student_headers"], json=payload)
    assert response.status_code == 409 and response.json()["detail"] == "Offering is closed"
    client.patch(offering_path, headers=setup["admin_headers"], json={"is_open": True})
    enroll(client, setup, "other_student_headers")


def test_student_privacy_and_drop_permissions(client, academic_setup):
    setup = academic_setup
    first = enroll(client, setup)
    second = enroll(client, setup, "other_student_headers")
    assert client.get(f"{ENROLLMENTS}/me", headers=setup["student_headers"]).json() == [first]
    assert client.get(f"{ENROLLMENTS}/me", headers=setup["other_student_headers"]).json() == [second]
    for actor in ("other_student_headers", "professor_headers", "admin_headers"):
        assert client.patch(f"{ENROLLMENTS}/{first['id']}/drop", headers=setup[actor]).status_code == 403


@pytest.mark.parametrize("actor,expected", [("professor_headers", 200), ("other_professor_headers", 403),
                                            ("admin_headers", 200), ("student_headers", 403)])
def test_roster_permissions(client, academic_setup, actor, expected):
    setup = academic_setup
    first = enroll(client, setup)
    second = enroll(client, setup, "other_student_headers")
    client.patch(f"{ENROLLMENTS}/{second['id']}/drop", headers=setup["other_student_headers"])
    response = client.get(f"{OFFERINGS}/{setup['offering'].id}/students", headers=setup[actor])
    assert response.status_code == expected
    if expected == 200:
        roster = response.json()
        assert len(roster) == 1
        assert roster[0]["id"] == first["id"]
        assert roster[0]["student_number"] == setup["student"].student_number
        assert roster[0]["first_name"] == "Test"


@pytest.mark.parametrize("actor", ["professor_headers", "admin_headers"])
def test_create_update_grade_and_completed_state(client, academic_setup, db_session, actor):
    setup = academic_setup
    enrollment = enroll(client, setup)
    response = client.post(grade_path(enrollment), headers=setup[actor], json={"grade": 87.25, "feedback": "Good work"})
    assert response.status_code == 201
    result = response.json()
    assert result["grade"] == 87.25
    assert result["enrollment_id"] == enrollment["id"]
    assert result["graded_at"] and result["created_at"] and result["updated_at"]
    db_session.expire_all()
    record = db_session.get(Enrollment, enrollment["id"])
    assert record.status == EnrollmentStatus.COMPLETED
    assert record.grade.id == result["id"]
    assert client.post(grade_path(enrollment), headers=setup[actor], json={"grade": 95}).status_code == 409
    response = client.patch(grade_path(enrollment), headers=setup[actor], json={"grade": 92, "feedback": None})
    assert response.status_code == 200
    assert response.json()["grade"] == 92 and response.json()["feedback"] is None
    assert response.json()["created_at"] == result["created_at"]
    assert client.patch(f"{ENROLLMENTS}/{enrollment['id']}/drop", headers=setup["student_headers"]).status_code == 409


@pytest.mark.parametrize("actor", ["other_professor_headers", "student_headers", "other_student_headers"])
def test_unassigned_users_cannot_grade(client, academic_setup, actor):
    setup = academic_setup
    enrollment = enroll(client, setup)
    assert client.post(grade_path(enrollment), headers=setup[actor], json={"grade": 90}).status_code == 403
    assert client.post(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": 90}).status_code == 201
    assert client.patch(grade_path(enrollment), headers=setup[actor], json={"grade": 99}).status_code == 403


@pytest.mark.parametrize("value", [-1, 101, "NaN", 1.234, None])
def test_invalid_grades(client, academic_setup, value):
    setup = academic_setup
    enrollment = enroll(client, setup)
    assert client.post(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": value}).status_code == 422
    assert client.post(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": 100}).status_code == 201
    assert client.patch(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": value}).status_code == 422


def test_grade_privacy_and_offering_permissions(client, academic_setup):
    setup = academic_setup
    first = enroll(client, setup)
    second = enroll(client, setup, "other_student_headers")
    first_grade = client.post(grade_path(first), headers=setup["professor_headers"], json={"grade": 0}).json()
    second_grade = client.post(grade_path(second), headers=setup["professor_headers"], json={"grade": 100}).json()
    assert client.get("/api/v1/grades/me", headers=setup["student_headers"]).json() == [first_grade]
    assert client.get("/api/v1/grades/me", headers=setup["other_student_headers"]).json() == [second_grade]
    assert client.get("/api/v1/grades/me", headers=setup["student_headers"],
                      params={"student_id": setup["other_student"].id}).json() == [first_grade]
    path = f"{OFFERINGS}/{setup['offering'].id}/grades"
    for actor in ("professor_headers", "admin_headers"):
        assert client.get(path, headers=setup[actor]).json() == [first_grade, second_grade]
    for actor in ("other_professor_headers", "student_headers"):
        assert client.get(path, headers=setup[actor]).status_code == 403


def test_dropped_cannot_be_graded_and_capacity_cannot_shrink(client, academic_setup):
    setup = academic_setup
    first = enroll(client, setup)
    second = enroll(client, setup, "other_student_headers")
    path = f"{OFFERINGS}/{setup['offering'].id}"
    assert client.patch(path, headers=setup["admin_headers"], json={"capacity": 1}).status_code == 409
    client.patch(f"{ENROLLMENTS}/{second['id']}/drop", headers=setup["other_student_headers"])
    assert client.post(grade_path(second), headers=setup["professor_headers"], json={"grade": 90}).status_code == 409
    assert client.patch(path, headers=setup["admin_headers"], json={"capacity": 1}).status_code == 200
    client.post(grade_path(first), headers=setup["professor_headers"], json={"grade": 90})
    assert client.get(f"{ENROLLMENTS}/me", headers=setup["student_headers"]).json()[0]["status"] == "completed"


def test_offering_reassignment_changes_permissions(client, academic_setup):
    setup = academic_setup
    enrollment = enroll(client, setup)
    path = f"{OFFERINGS}/{setup['offering'].id}"
    assert client.patch(path, headers=setup["admin_headers"], json={"professor_id": setup["other_professor"].id}).status_code == 200
    assert client.post(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": 90}).status_code == 403
    assert client.post(grade_path(enrollment), headers=setup["other_professor_headers"], json={"grade": 90}).status_code == 201


def test_missing_records_and_student_profile(client, academic_setup, make_actor):
    setup = academic_setup
    assert client.post(ENROLLMENTS, headers=setup["student_headers"], json={"course_offering_id": 99999}).status_code == 404
    assert client.patch(f"{ENROLLMENTS}/99999/drop", headers=setup["student_headers"]).status_code == 404
    assert client.post(f"{ENROLLMENTS}/99999/grade", headers=setup["professor_headers"], json={"grade": 90}).status_code == 404
    assert client.get(f"{OFFERINGS}/99999/students", headers=setup["professor_headers"]).status_code == 404
    enrollment = enroll(client, setup)
    assert client.patch(grade_path(enrollment), headers=setup["professor_headers"], json={"grade": 90}).status_code == 404
    _, headers = make_actor(UserRole.STUDENT)
    assert client.post(ENROLLMENTS, headers=headers, json={"course_offering_id": setup["offering"].id}).status_code == 404


@pytest.mark.parametrize("method,path,body", [
    ("post", "/terms", {"name": "Fall", "academic_year": "2026", "start_date": "2026-09-01", "end_date": "2026-12-31"}),
    ("get", "/terms", None), ("get", "/terms/1", None), ("patch", "/terms/1", {}),
    ("post", "/course-offerings", {"course_id": 1, "professor_id": 1, "term_id": 1, "section": "A", "capacity": 10}),
    ("get", "/course-offerings", None), ("get", "/course-offerings/1", None), ("patch", "/course-offerings/1", {}),
    ("get", "/course-offerings/1/students", None), ("get", "/course-offerings/1/grades", None),
    ("post", "/enrollments", {"course_offering_id": 1}), ("get", "/enrollments/me", None),
    ("patch", "/enrollments/1/drop", None), ("post", "/enrollments/1/grade", {"grade": 90}),
    ("patch", "/enrollments/1/grade", {"grade": 90}), ("get", "/grades/me", None),
])
def test_all_new_endpoints_require_authentication(client, method, path, body):
    response = client.request(method, f"/api/v1{path}", json=body)
    assert response.status_code == 401


@pytest.mark.parametrize("violation", ["duplicate_term", "term_dates", "duplicate_offering", "capacity", "offering_fk",
                                      "duplicate_enrollment", "enrollment_fk", "status", "duplicate_grade", "grade_range", "grade_fk"])
def test_database_constraints(academic_setup, db_session, violation):
    setup = academic_setup
    enrollment = Enrollment(student_id=setup["student"].id, course_offering_id=setup["offering"].id)
    db_session.add(enrollment)
    db_session.flush()
    db_session.add(Grade(enrollment_id=enrollment.id, grade=90))
    db_session.commit()
    if violation.startswith("duplicate_term") or violation == "term_dates":
        record = AcademicTerm(name="Fall" if violation == "duplicate_term" else "Other",
                              academic_year="2026-2027", start_date=setup["term"].start_date,
                              end_date=setup["term"].end_date if violation == "duplicate_term" else setup["term"].start_date)
    elif violation in {"duplicate_offering", "capacity", "offering_fk"}:
        record = CourseOffering(course_id=99999 if violation == "offering_fk" else setup["course"].id,
                                professor_id=setup["professor"].id, term_id=setup["term"].id,
                                section="A" if violation == "duplicate_offering" else "B", capacity=0 if violation == "capacity" else 2)
    elif violation in {"duplicate_enrollment", "enrollment_fk", "status"}:
        if violation == "status":
            from sqlalchemy import text
            with pytest.raises(IntegrityError):
                db_session.execute(text("UPDATE enrollments SET status='invalid'"))
            db_session.rollback()
            return
        record = Enrollment(student_id=99999 if violation == "enrollment_fk" else setup["student"].id,
                            course_offering_id=setup["offering"].id)
    else:
        second = Enrollment(student_id=setup["other_student"].id, course_offering_id=setup["offering"].id)
        db_session.add(second)
        db_session.commit()
        record = Grade(enrollment_id=enrollment.id if violation == "duplicate_grade" else
                       (99999 if violation == "grade_fk" else second.id), grade=101 if violation == "grade_range" else 90)
    db_session.add(record)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
