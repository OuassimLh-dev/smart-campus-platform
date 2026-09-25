from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.professor_profile import ProfessorProfile
from app.schemas.course import CourseCreate, CourseUpdate
from app.services.academic import AcademicNotFoundError, ensure_unique, save_record
from app.services.department import get_department


def validate_professor(db: Session, professor_id: int | None) -> None:
    if professor_id is not None and db.get(ProfessorProfile, professor_id) is None:
        raise AcademicNotFoundError("Professor not found")


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise AcademicNotFoundError("Course not found")
    return course


def list_courses(db: Session, skip: int = 0, limit: int = 20,
                 department_id: int | None = None, professor_id: int | None = None) -> list[Course]:
    query = select(Course).where(Course.is_active.is_(True))
    if department_id is not None:
        query = query.where(Course.department_id == department_id)
    if professor_id is not None:
        query = query.where(Course.professor_id == professor_id)
    return list(db.scalars(query.order_by(Course.id).offset(skip).limit(limit)))


def create_course(db: Session, payload: CourseCreate) -> Course:
    get_department(db, payload.department_id)
    validate_professor(db, payload.professor_id)
    ensure_unique(db, Course, {"code": payload.code})
    course = Course(**payload.model_dump())
    db.add(course)
    return save_record(db, course, ("code",))


def update_course(db: Session, course_id: int, payload: CourseUpdate) -> Course:
    course = get_course(db, course_id)
    changes = payload.model_dump(exclude_unset=True)
    if "department_id" in changes:
        get_department(db, changes["department_id"])
    if "professor_id" in changes:
        validate_professor(db, changes["professor_id"])
    if "code" in changes:
        ensure_unique(db, Course, {"code": changes["code"]}, course.id)
    for field, value in changes.items():
        setattr(course, field, value)
    return save_record(db, course, ("code",))


def delete_course(db: Session, course_id: int) -> Course:
    course = get_course(db, course_id)
    course.is_active = False
    return save_record(db, course, ("code",))
