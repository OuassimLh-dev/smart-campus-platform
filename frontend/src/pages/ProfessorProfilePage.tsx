import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { LoadError } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { professorService } from '../services/professorService'
import type { ProfessorProfileInput } from '../types/professor'
import { apiError } from '../utils/apiError'

const fields = [
  ['employee_number', 'Employee number', 'text', 50],
  ['department', 'Department', 'text', 100],
  ['academic_title', 'Academic title', 'text', 100],
  ['office_location', 'Office location', 'text', 150],
  ['research_interests', 'Research interests', 'text', 5000],
] as const
type Draft = ProfessorProfileInput
const blank: Draft = { employee_number: '', department: '', academic_title: '', office_location: '', research_interests: '' }

export function ProfessorProfilePage() {
  const resource = useResource(useCallback((signal: AbortSignal) => professorService.me(signal), []))
  const [draft, setDraft] = useState<Draft>(blank)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  useEffect(() => {
    if (resource.data) {
      const profile = resource.data
      setDraft(profile)
    }
  }, [resource.data])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setError(''); setMessage('')
    const payload = Object.fromEntries(fields.map(([key]) => [key, draft[key].trim()])) as unknown as ProfessorProfileInput
    if (Object.values(payload).some(value => !value)) {
      setError('All profile fields must not be blank.'); return
    }
    setSaving(true)
    try {
      const saved = resource.data ? await professorService.update(payload) : await professorService.create(payload)
      setMessage(resource.data ? 'Your profile has been updated.' : 'Your profile is ready. You can now view your assigned offerings.')
      resource.setData(saved)
    } catch (cause) { setError(apiError(cause)) }
    finally { setSaving(false) }
  }

  return <>
    <div className="page-heading"><p className="eyebrow">PROFESSOR WORKSPACE</p><h1>My profile</h1>
      <p className="muted">Keep your academic information up to date.</p></div>
    {resource.loading ? <p role="status">Loading your profile…</p> :
      resource.error ? <LoadError message={resource.error} retry={resource.reload} /> :
      <section className="workflow-panel">
        <h2>{resource.data ? 'Academic profile' : 'Welcome. Let’s create your professor profile.'}</h2>
        {!resource.data && <p className="muted">Complete these details to set up your teaching profile.</p>}
        <form onSubmit={submit} className="profile-form" aria-busy={saving}>
          <div className="form-grid">{fields.map(([key, label, type, maxLength]) =>
            <div key={key}><label htmlFor={key}>{label}</label>
              <input id={key} type={type} required maxLength={maxLength} disabled={saving}
                value={draft[key]} onChange={event => setDraft(current => ({ ...current, [key]: event.target.value }))} />
            </div>,
          )}</div>
          {error && <div className="form-error" role="alert">{error}</div>}
          {message && <div className="notice" role="status">{message} <Link to="/professor/courses">View assigned offerings →</Link></div>}
          <button className="primary-button compact-button" disabled={saving}>
            {saving ? 'Saving…' : resource.data ? 'Save changes' : 'Create profile'}
          </button>
        </form>
      </section>}
  </>
}
