import { api } from '../api/client'
import type { ProfessorProfile, ProfessorProfileInput } from '../types/professor'
import { isNotFound } from '../utils/apiError'
export const professorService = {
  async me(signal?: AbortSignal) {
    try { return (await api.get<ProfessorProfile>('/professors/me', { signal })).data }
    catch (error) { if (isNotFound(error)) return null; throw error }
  },
  async create(input: ProfessorProfileInput) {
    return (await api.post<ProfessorProfile>('/professors/profile', input)).data
  },
  async update(input: ProfessorProfileInput) {
    return (await api.patch<ProfessorProfile>('/professors/me', input)).data
  },
}
