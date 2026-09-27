import { api } from '../api/client'
import type { StudentProfile, StudentProfileInput } from '../types/student'
import { isNotFound } from '../utils/apiError'

export const studentService = {
  async me(signal?: AbortSignal): Promise<StudentProfile | null> {
    try { return (await api.get<StudentProfile>('/students/me', { signal })).data }
    catch (error) { if (isNotFound(error)) return null; throw error }
  },
  async create(payload: StudentProfileInput) {
    return (await api.post<StudentProfile>('/students/profile', payload)).data
  },
  async update(payload: Partial<StudentProfileInput>) {
    return (await api.patch<StudentProfile>('/students/me', payload)).data
  },
}
