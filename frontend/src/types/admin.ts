import type { User } from './auth'
import type { CourseOffering } from './courseOffering'
export interface Department {
  id: number; code: string; name: string; description: string | null
  is_active: boolean; created_at: string; updated_at: string
}
export interface Course extends Omit<Department, 'name'> {
  title: string; credits: number; department_id: number; professor_id: number | null
}
export interface AcademicTerm {
  id: number; name: string; academic_year: string; start_date: string; end_date: string
  is_active: boolean; created_at: string; updated_at: string
}
export interface AdminEntities {
  users: User
  departments: Department
  courses: Course
  terms: AcademicTerm
  'course-offerings': CourseOffering
}
export type AdminKind = keyof AdminEntities
export type AdminRecord = AdminEntities[AdminKind]
export type AdminInput<K extends AdminKind> = Omit<AdminEntities[K], 'id' | 'created_at' | 'updated_at'>
export type Filters = Record<string, string>
export interface Option { value: string; label: string }
