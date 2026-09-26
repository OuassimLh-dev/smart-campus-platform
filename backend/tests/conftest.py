from uuid import uuid4
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.main import app
from app.models import User  # noqa: F401 -- register model metadata
from app.models.user import UserRole


@pytest.fixture
def db_session():
    # A fresh, isolated database for each test; never read DATABASE_URL.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

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


@pytest.fixture
def make_actor(db_session, auth_settings):
    def create(role=UserRole.STUDENT):
        user = User(first_name="Test", last_name="Actor", role=role,
                    email=f"actor-{uuid4().hex}@example.com")
        db_session.add(user)
        db_session.commit()
        token = create_access_token(user.id, auth_settings)
        return user, {"Authorization": f"Bearer {token}"}
    return create


@pytest.fixture
def admin_headers(make_actor):
    _, headers = make_actor(UserRole.ADMIN)
    return headers


@pytest.fixture
def academic_setup(db_session, make_actor):
    from app.models import AcademicTerm, Course, CourseOffering, Department, ProfessorProfile, StudentProfile

    def academic_actor(role):
        user, headers = make_actor(role)
        if role == UserRole.STUDENT:
            profile = StudentProfile(user_id=user.id, student_number=f"S-{user.id}", department="Computing",
                                     program="Software Engineering", year_level=1, enrollment_year=2026,
                                     expected_graduation_year=2030)
        else:
            profile = ProfessorProfile(user_id=user.id, employee_number=f"P-{user.id}", department="Computing",
                                       academic_title="Professor", office_location="A-101", research_interests="Systems")
        db_session.add(profile)
        db_session.commit()
        return profile, headers

    student, student_headers = academic_actor(UserRole.STUDENT)
    other_student, other_student_headers = academic_actor(UserRole.STUDENT)
    professor, professor_headers = academic_actor(UserRole.PROFESSOR)
    other_professor, other_professor_headers = academic_actor(UserRole.PROFESSOR)
    _, admin_headers = make_actor(UserRole.ADMIN)
    department = Department(code="SE", name="Software Engineering")
    db_session.add(department)
    db_session.flush()
    # Deliberately assign a different course-level professor to detect authorization mistakes.
    course = Course(code="SE101", title="Introduction", credits=3,
                    department_id=department.id, professor_id=other_professor.id)
    term = AcademicTerm(name="Fall", academic_year="2026-2027", start_date=date(2026, 9, 1), end_date=date(2026, 12, 31))
    db_session.add_all([course, term])
    db_session.flush()
    offering = CourseOffering(course_id=course.id, professor_id=professor.id, term_id=term.id, section="A", capacity=2)
    db_session.add(offering)
    db_session.commit()
    return dict(student=student, student_headers=student_headers, other_student=other_student,
                other_student_headers=other_student_headers, professor=professor, professor_headers=professor_headers,
                other_professor=other_professor, other_professor_headers=other_professor_headers,
                admin_headers=admin_headers, department=department, course=course, term=term, offering=offering)
