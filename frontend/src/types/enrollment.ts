export interface Enrollment {
  id: number
  student_id: number
  course_offering_id: number
  status: 'enrolled' | 'dropped' | 'completed'
  enrolled_at: string
  created_at: string
  updated_at: string
}
