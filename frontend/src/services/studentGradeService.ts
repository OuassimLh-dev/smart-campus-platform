import { api } from '../api/client'
import { courseOfferingService } from './courseOfferingService'
import { enrollmentService } from './enrollmentService'
import { studentService } from './studentService'
import type { Grade } from '../types/grade'
import type { Enrollment } from '../types/enrollment'
import type { AcademicTerm, Course, CourseOffering } from '../types/courseOffering'

export interface StudentGradeDetails {
  grade: Grade
  enrollment?: Enrollment
  offering?: CourseOffering
  course?: Course
  term?: AcademicTerm
}

export const studentGradeService = {
  async me(signal: AbortSignal): Promise<{ missingProfile: boolean; records: StudentGradeDetails[] }> {
    const profile = await studentService.me(signal)
    if (!profile) return { missingProfile: true, records: [] }
    const grades = (await api.get<Grade[]>('/grades/me', { signal })).data
    if (!grades.length) return { missingProfile: false, records: [] }
    const enrollments = await enrollmentService.me(signal)
    const byEnrollment = new Map(enrollments.map(enrollment => [enrollment.id, enrollment]))
    // Cache related lookups within this load; one unavailable detail must not hide a grade.
    const offerings = new Map<number, Promise<CourseOffering | undefined>>()
    const courses = new Map<number, Promise<Course | undefined>>()
    const terms = new Map<number, Promise<AcademicTerm | undefined>>()
    function lookup<T>(cache: Map<number, Promise<T | undefined>>, id: number, load: () => Promise<T>) {
      if (!cache.has(id)) cache.set(id, load().catch(() => undefined))
      return cache.get(id)!
    }
    const records = await Promise.all(grades.map(async grade => {
      const enrollment = byEnrollment.get(grade.enrollment_id)
      const offering = enrollment && await lookup(offerings, enrollment.course_offering_id,
        () => courseOfferingService.get(enrollment.course_offering_id, signal))
      const [course, term] = offering ? await Promise.all([
        lookup(courses, offering.course_id, async () => (await api.get<Course>(`/courses/${offering.course_id}`, { signal })).data),
        lookup(terms, offering.term_id, async () => (await api.get<AcademicTerm>(`/terms/${offering.term_id}`, { signal })).data),
      ]) : [undefined, undefined]
      return { grade, enrollment, offering, course, term }
    }))
    return { missingProfile: false, records }
  },
}
