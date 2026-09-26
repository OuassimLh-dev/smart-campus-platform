from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.academic_term import AcademicTerm
    from app.models.course import Course
    from app.models.enrollment import Enrollment
    from app.models.professor_profile import ProfessorProfile


class CourseOffering(Base):
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint("course_id", "term_id", "section", name="uq_offering_course_term_section"),
        CheckConstraint("capacity > 0", name="offering_capacity_positive"),
        CheckConstraint("length(trim(section)) > 0", name="offering_section_not_blank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professor_profiles.id"), index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("academic_terms.id"), index=True)
    section: Mapped[str] = mapped_column(String(50))
    capacity: Mapped[int]
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    course: Mapped["Course"] = relationship(back_populates="offerings")
    professor: Mapped["ProfessorProfile"] = relationship(back_populates="offerings")
    term: Mapped["AcademicTerm"] = relationship(back_populates="offerings")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="offering")
