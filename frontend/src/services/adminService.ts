import { api } from '../api/client'
import type { AdminEntities, AdminInput, AdminKind, Filters, Option } from '../types/admin'
import type { ProfessorProfile } from '../types/professor'

export const adminService = {
  async list<K extends AdminKind>(kind: K, skip: number, filters: Filters, signal?: AbortSignal) {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ''))
    return (await api.get<AdminEntities[K][]>(`/${kind}`, { params: { ...params, skip, limit: 20 }, signal })).data
  },
  async create<K extends Exclude<AdminKind, 'users'>>(kind: K, input: AdminInput<K>) {
    return (await api.post<AdminEntities[K]>(`/${kind}`, input)).data
  },
  async update<K extends AdminKind>(kind: K, id: number, input: AdminInput<K>) {
    return (await api.patch<AdminEntities[K]>(`/${kind}/${id}`, input)).data
  },
  async deactivate(kind: 'users' | 'departments' | 'courses', id: number) {
    return (await api.delete(`/${kind}/${id}`)).data
  },
}

// Exhaust pagination so selectors never silently omit references after page one.
async function all<T>(path: string, signal: AbortSignal): Promise<T[]> {
  const result: T[] = []
  for (let skip = 0; ; skip += 100) {
    const page = (await api.get<T[]>(path, { params: { skip, limit: 100 }, signal })).data
    result.push(...page)
    if (page.length < 100) return result
  }
}
export async function adminOptions(kind: AdminKind, signal: AbortSignal): Promise<Record<string, Option[]>> {
  if (kind !== 'courses' && kind !== 'course-offerings') return {}
  const professors = all<ProfessorProfile>('/professors', signal)
  const professorOptions = (await professors).map(p => ({ value: String(p.id), label: `${p.employee_number} · ${p.academic_title} · ${p.department}` }))
  if (kind === 'courses') {
    const departments = await all<AdminEntities['departments']>('/departments', signal)
    return { professor_id: professorOptions, department_id: departments.map(d => ({ value: String(d.id), label: `${d.code} · ${d.name}` })) }
  }
  const [courses, terms] = await Promise.all([
    all<AdminEntities['courses']>('/courses', signal), all<AdminEntities['terms']>('/terms', signal),
  ])
  return { professor_id: professorOptions,
    course_id: courses.map(c => ({ value: String(c.id), label: `${c.code} · ${c.title}` })),
    term_id: terms.map(t => ({ value: String(t.id), label: `${t.name} · ${t.academic_year}` })),
  }
}
