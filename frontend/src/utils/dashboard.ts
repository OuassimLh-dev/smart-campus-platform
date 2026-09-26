import type { Role } from '../types/auth'

export const dashboardSections: Record<Role, { title: string; description: string }[]> = {
  student: [
    { title: 'My Courses', description: 'Your learning, organized in one place.' },
    { title: 'Enrollments', description: 'Keep track of your academic journey.' },
    { title: 'Grades', description: 'Follow your progress through each term.' },
  ],
  professor: [
    { title: 'My Courses', description: 'A home for your teaching activity.' },
    { title: 'Students', description: 'Stay connected to the students you teach.' },
    { title: 'Grading', description: 'Review progress and record achievement.' },
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
