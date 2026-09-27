export interface StudentProfileInput {
  student_number: string
  department: string
  program: string
  year_level: number
  enrollment_year: number
  expected_graduation_year: number
}
export interface StudentProfile extends StudentProfileInput {
  id: number
  user_id: number
  created_at: string
  updated_at: string
}
