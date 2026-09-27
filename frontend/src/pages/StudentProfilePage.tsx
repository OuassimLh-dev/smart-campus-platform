import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { LoadError } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { studentService } from '../services/studentService'
import type { StudentProfileInput } from '../types/student'
import { apiError } from '../utils/apiError'

const fields = [
  ['student_number', 'Student number', 'text', 50],
  ['department', 'Department', 'text', 100],
  ['program', 'Program', 'text', 150],
  ['year_level', 'Year level', 'number'],
  ['enrollment_year', 'Enrollment year', 'number'],
  ['expected_graduation_year', 'Expected graduation year', 'number'],
] as const
type Draft = Record<keyof StudentProfileInput, string>
const blank: Draft = { student_number: '', department: '', program: '', year_level: '', enrollment_year: '', expected_graduation_year: '' }

export function StudentProfilePage() {
  const resource = useResource(useCallback((signal: AbortSignal) => studentService.me(signal), []))
  const [draft, setDraft] = useState<Draft>(blank)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    if (resource.data) {
      const profile = resource.data
      setDraft(Object.fromEntries(fields.map(([key]) => [key, String(profile[key])])) as Draft)
    }
  }, [resource.data])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setError(''); setMessage('')
    const payload: StudentProfileInput = {
      student_number: draft.student_number.trim(), department: draft.department.trim(), program: draft.program.trim(),
      year_level: Number(draft.year_level), enrollment_year: Number(draft.enrollment_year),
      expected_graduation_year: Number(draft.expected_graduation_year),
    }
    if (!payload.student_number || !payload.department || !payload.program) {
      setError('Student number, department, and program must not be blank.'); return
    }
    if (payload.expected_graduation_year < payload.enrollment_year) {
      setError('Expected graduation year must not precede enrollment year.'); return
    }
    setSaving(true)
    try {
      const saved = resource.data ? await studentService.update(payload) : await studentService.create(payload)
      setMessage(resource.data ? 'Your profile has been updated.' : 'Your profile is ready. You can now enroll in courses.')
      resource.setData(saved)
    } catch (cause) { setError(apiError(cause)) }
    finally { setSaving(false) }
  }

  return <>
    <div className="page-heading"><p className="eyebrow">STUDENT WORKSPACE</p><h1>My profile</h1>
      <p className="muted">Keep your academic information up to date.</p></div>
    {resource.loading ? <p role="status">Loading your profile…</p> :
      resource.error ? <LoadError message={resource.error} retry={resource.reload} /> :
      <section className="workflow-panel">
        <h2>{resource.data ? 'Academic profile' : 'Welcome. Let’s create your student profile.'}</h2>
        {!resource.data && <p className="muted">Complete these details before enrolling in a course offering.</p>}
        <form onSubmit={submit} className="profile-form" aria-busy={saving}>
          <div className="form-grid">{fields.map(([key, label, type, maxLength]) =>
            <div key={key}><label htmlFor={key}>{label}</label>
              <input id={key} type={type} required maxLength={maxLength} disabled={saving}
                min={type === 'number' ? key === 'year_level' ? 1 : 1900 : undefined}
                max={type === 'number' && key !== 'year_level' ? 2200 : undefined}
                step={type === 'number' ? 1 : undefined}
                value={draft[key]} onChange={event => setDraft(current => ({ ...current, [key]: event.target.value }))} />
            </div>,
          )}</div>
          {error && <div className="form-error" role="alert">{error}</div>}
          {message && <div className="notice" role="status">{message} <Link to="/courses">Browse offerings →</Link></div>}
          <button className="primary-button compact-button" disabled={saving}>
            {saving ? 'Saving…' : resource.data ? 'Save changes' : 'Create profile'}
          </button>
        </form>
      </section>}
  </>
}
