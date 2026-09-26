from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course_offering import CourseOffering
    from app.models.grade import Grade
    from app.models.student_profile import StudentProfile


class EnrollmentStatus(str, Enum):
    ENROLLED = "enrolled"
    DROPPED = "dropped"
    COMPLETED = "completed"


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "course_offering_id", name="uq_enrollment_student_offering"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.id"), index=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id"), index=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        SQLAlchemyEnum(EnrollmentStatus, name="enrollment_status",
                       values_callable=lambda statuses: [status.value for status in statuses],
                       validate_strings=True, create_constraint=True),
        default=EnrollmentStatus.ENROLLED, server_default="enrolled",
    )
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    student: Mapped["StudentProfile"] = relationship(back_populates="enrollments")
    offering: Mapped["CourseOffering"] = relationship(back_populates="enrollments")
    grade: Mapped["Grade | None"] = relationship(back_populates="enrollment")
