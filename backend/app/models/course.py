from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course_offering import CourseOffering
    from app.models.department import Department
    from app.models.professor_profile import ProfessorProfile


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("credits > 0", name="course_credits_positive"),
        CheckConstraint("length(trim(code)) > 0", name="course_code_not_blank"),
        CheckConstraint("length(trim(title)) > 0", name="course_title_not_blank"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text)
    credits: Mapped[int]
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), index=True)
    professor_id: Mapped[int | None] = mapped_column(ForeignKey("professor_profiles.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    department: Mapped["Department"] = relationship(back_populates="courses")
    professor: Mapped["ProfessorProfile | None"] = relationship(back_populates="courses")
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="course")
