from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.professor_profile import ProfessorProfile
from app.models.department import Department
from app.models.course import Course
from app.models.academic_term import AcademicTerm
from app.models.course_offering import CourseOffering
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.grade import Grade

__all__ = ["User", "UserRole", "StudentProfile", "ProfessorProfile", "Department", "Course",
           "AcademicTerm", "CourseOffering", "Enrollment", "EnrollmentStatus", "Grade"]
