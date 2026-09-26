from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.enrollment import Enrollment


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (CheckConstraint("grade >= 0 AND grade <= 100", name="grade_valid_range"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("enrollments.id"), unique=True)
    grade: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    feedback: Mapped[str | None] = mapped_column(Text)
    graded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    enrollment: Mapped["Enrollment"] = relationship(back_populates="grade")
