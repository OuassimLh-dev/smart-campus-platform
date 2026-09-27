export interface ProfessorProfileInput {
  employee_number: string
  department: string
  academic_title: string
  office_location: string
  research_interests: string
}
export interface ProfessorProfile extends ProfessorProfileInput {
  id: number
  user_id: number
  created_at: string
  updated_at: string
}
