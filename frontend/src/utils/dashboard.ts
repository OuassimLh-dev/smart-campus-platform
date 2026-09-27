import type { Role } from '../types/auth'

export const dashboardSections: Record<Role, { title: string; description: string; path?: string }[]> = {
  student: [
    { title: 'My Profile', description: 'Manage your academic information.', path: '/profile' },
    { title: 'My Courses', description: 'Browse available course offerings.', path: '/courses' },
    { title: 'Enrollments', description: 'Keep track of your academic journey.', path: '/enrollments' },
    { title: 'Grades', description: 'Follow your progress through each term.' },
  ],
  professor: [
    { title: 'My Profile', description: 'Manage your teaching profile.', path: '/professor/profile' },
    { title: 'My Courses', description: 'View your assigned course offerings.', path: '/professor/courses' },
    { title: 'Students / Grading', description: 'Select an offering to view students and record grades.', path: '/professor/courses' },
  ],
  admin: [
    { title: 'Users', description: 'Support your campus community.' },
    { title: 'Departments', description: 'Organize your academic departments.' },
    { title: 'Courses', description: 'Maintain your institution’s course catalog.' },
    { title: 'Academic Management', description: 'Coordinate terms, offerings, and enrollment.' },
  ],
}

export const roleLabels: Record<Role, string> = {
  student: 'Student', professor: 'Professor', admin: 'Administrator',
}
