import type { AdminKind, Option } from '../types/admin'
export interface AdminField {
  key: string; label: string; type?: 'text' | 'email' | 'number' | 'date' | 'checkbox' | 'textarea' | 'select'
  maxLength?: number; nullable?: boolean; options?: Option[]
}
export const adminTitles: Record<AdminKind, string> = {
  users: 'Users', departments: 'Departments', courses: 'Courses', terms: 'Academic Terms', 'course-offerings': 'Course Offerings',
}
const active: AdminField = { key: 'is_active', label: 'Active', type: 'checkbox' }
const code: AdminField = { key: 'code', label: 'Code', maxLength: 50 }
const description: AdminField = { key: 'description', label: 'Description', type: 'textarea', maxLength: 5000, nullable: true }
const professor: AdminField = { key: 'professor_id', label: 'Professor', type: 'select' }
export const adminFields: Record<AdminKind, AdminField[]> = {
  users: [
    { key: 'first_name', label: 'First name', maxLength: 100 }, { key: 'last_name', label: 'Last name', maxLength: 100 },
    { key: 'email', label: 'Email', type: 'email', maxLength: 254 },
    { key: 'role', label: 'Role', type: 'select', options: ['student', 'professor', 'admin'].map(value => ({ value, label: value })) }, active,
  ],
  departments: [code, { key: 'name', label: 'Name', maxLength: 150 }, description, active],
  courses: [code, { key: 'title', label: 'Title', maxLength: 150 }, description,
    { key: 'credits', label: 'Credits', type: 'number' }, { key: 'department_id', label: 'Department', type: 'select' },
    { ...professor, nullable: true }, active],
  terms: [{ key: 'name', label: 'Name', maxLength: 100 }, { key: 'academic_year', label: 'Academic year', maxLength: 50 },
    { key: 'start_date', label: 'Start date', type: 'date' }, { key: 'end_date', label: 'End date', type: 'date' }, active],
  'course-offerings': [{ key: 'course_id', label: 'Course', type: 'select' }, professor,
    { key: 'term_id', label: 'Academic term', type: 'select' }, { key: 'section', label: 'Section', maxLength: 50 },
    { key: 'capacity', label: 'Capacity', type: 'number' }, { key: 'is_open', label: 'Open for enrollment', type: 'checkbox' }],
}
