export interface CourseOffering {
  id: number
  course_id: number
  professor_id: number
  term_id: number
  section: string
  capacity: number
  is_open: boolean
  created_at: string
  updated_at: string
}
export interface Course {
  id: number
  code: string
  title: string
  credits: number
}
export interface AcademicTerm {
  id: number
  name: string
  academic_year: string
}
export interface ProfessorPublic {
  id: number
  academic_title: string
}
export interface OfferingDetails {
  offering: CourseOffering
  course?: Course
  term?: AcademicTerm
  professor?: ProfessorPublic
}
