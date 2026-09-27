import { api } from '../api/client'
import type { AcademicTerm, Course, CourseOffering, OfferingDetails, ProfessorPublic } from '../types/courseOffering'

export const courseOfferingService = {
  async list(skip: number, onlyOpen: boolean, signal?: AbortSignal) {
    return (await api.get<CourseOffering[]>('/course-offerings', {
      params: { skip, limit: 20, ...(onlyOpen ? { is_open: true } : {}) }, signal,
    })).data
  },
  async get(id: number, signal?: AbortSignal) {
    return (await api.get<CourseOffering>(`/course-offerings/${id}`, { signal })).data
  },
  async enrich(offerings: CourseOffering[], signal?: AbortSignal): Promise<OfferingDetails[]> {
    // Deduplicate related lookups within this page. Missing details never hide an offering.
    async function lookup<T>(ids: number[], path: string): Promise<Map<number, T>> {
      const entries = await Promise.all([...new Set(ids)].map(async (id) => {
        try { return [id, (await api.get<T>(`${path}/${id}`, { signal })).data] as const }
        catch { return [id, undefined] as const }
      }))
      return new Map(entries.filter((entry): entry is readonly [number, T] => entry[1] !== undefined))
    }
    const [courses, terms, professors] = await Promise.all([
      lookup<Course>(offerings.map(o => o.course_id), '/courses'),
      lookup<AcademicTerm>(offerings.map(o => o.term_id), '/terms'),
      lookup<ProfessorPublic>(offerings.map(o => o.professor_id), '/professors'),
    ])
    return offerings.map(offering => ({
      offering, course: courses.get(offering.course_id),
      term: terms.get(offering.term_id), professor: professors.get(offering.professor_id),
    }))
  },
}
