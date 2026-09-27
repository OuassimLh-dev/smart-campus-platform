import { api } from '../api/client'
import type { Enrollment } from '../types/enrollment'

export const enrollmentService = {
  async me(signal?: AbortSignal) {
    return (await api.get<Enrollment[]>('/enrollments/me', { signal })).data
  },
  async enroll(courseOfferingId: number) {
    return (await api.post<Enrollment>('/enrollments', { course_offering_id: courseOfferingId })).data
  },
  async drop(enrollmentId: number) {
    return (await api.patch<Enrollment>(`/enrollments/${enrollmentId}/drop`)).data
  },
}
