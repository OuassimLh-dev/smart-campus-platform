import { api } from '../api/client'
import type { CourseOffering } from '../types/courseOffering'
import type { RosterEntry } from '../types/roster'
export const professorCourseService = {
  async list(professorId: number, skip: number, signal?: AbortSignal) {
    return (await api.get<CourseOffering[]>('/course-offerings', {
      params: { professor_id: professorId, skip, limit: 20 }, signal,
    })).data
  },
  async roster(offeringId: number, signal?: AbortSignal) {
    return (await api.get<RosterEntry[]>(`/course-offerings/${offeringId}/students`, { signal })).data
  },
}
