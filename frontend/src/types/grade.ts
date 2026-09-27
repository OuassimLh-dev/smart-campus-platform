export interface GradeInput { grade: number; feedback: string | null }
export interface Grade extends GradeInput {
  id: number
  enrollment_id: number
  graded_at: string
  created_at: string
  updated_at: string
}
