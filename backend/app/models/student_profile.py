from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        CheckConstraint("year_level >= 1", name="student_year_level_positive"),
        CheckConstraint("enrollment_year BETWEEN 1900 AND 2200", name="student_enrollment_year_range"),
        CheckConstraint("expected_graduation_year BETWEEN enrollment_year AND 2200",
                        name="student_graduation_year_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    student_number: Mapped[str] = mapped_column(String(50), unique=True)
    department: Mapped[str] = mapped_column(String(100))
    program: Mapped[str] = mapped_column(String(150))
    year_level: Mapped[int]
    enrollment_year: Mapped[int]
    expected_graduation_year: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="student_profile")
