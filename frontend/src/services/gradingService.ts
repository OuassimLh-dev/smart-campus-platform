import { api } from '../api/client'
import type { Grade, GradeInput } from '../types/grade'
export const gradingService = {
  async list(offeringId: number, signal?: AbortSignal) {
    return (await api.get<Grade[]>(`/course-offerings/${offeringId}/grades`, { signal })).data
  },
  async create(enrollmentId: number, input: GradeInput) {
    return (await api.post<Grade>(`/enrollments/${enrollmentId}/grade`, input)).data
  },
  async update(enrollmentId: number, input: GradeInput) {
    return (await api.patch<Grade>(`/enrollments/${enrollmentId}/grade`, input)).data
  },
}
