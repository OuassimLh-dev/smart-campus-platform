import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Grade } from '../types/grade'
import { gradingService } from '../services/gradingService'
import { apiError } from '../utils/apiError'

export function GradeEditor({ enrollmentId, existing, onSaved }: {
  enrollmentId: number; existing?: Grade; onSaved: (grade: Grade) => void
}) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState('')
  const [feedback, setFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  function edit() {
    setValue(existing ? String(existing.grade) : '')
    setFeedback(existing?.feedback ?? '')
    setError(''); setMessage(''); setEditing(true)
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    const grade = Number(value)
    if (!value.trim() || !Number.isFinite(grade) || grade < 0 || grade > 100) {
      setError('Enter a grade between 0 and 100.'); return
    }
    setSaving(true); setError('')
    try {
      const input = { grade, feedback: feedback.trim() || null }
      const saved = existing ? await gradingService.update(enrollmentId, input) : await gradingService.create(enrollmentId, input)
      onSaved(saved); setEditing(false); setMessage(existing ? 'Grade updated.' : 'Grade recorded.')
    } catch (cause) { setError(apiError(cause)) }
    finally { setSaving(false) }
  }
  return <div>
    <p><strong>{existing ? `Grade: ${existing.grade} / 100` : 'Not graded'}</strong></p>
    {existing?.feedback && <p className="grade-feedback">{existing.feedback}</p>}
    {message && <p className="notice" role="status">{message}</p>}
    {!editing ? <button className="secondary-button" onClick={edit}>{existing ? 'Edit grade' : 'Add grade'}</button> :
      <form className="profile-form" onSubmit={submit} aria-busy={saving}>
        {existing && <p className="notice">Saving will replace the current grade of {existing.grade} / 100 and its feedback.</p>}
        <div><label htmlFor={`grade-${enrollmentId}`}>Grade (0–100)</label>
          <input id={`grade-${enrollmentId}`} type="number" min="0" max="100" step="0.01" required disabled={saving}
            value={value} onChange={event => setValue(event.target.value)} /></div>
        <div><label htmlFor={`feedback-${enrollmentId}`}>Feedback (optional)</label>
          <textarea id={`feedback-${enrollmentId}`} maxLength={5000} rows={3} disabled={saving}
            value={feedback} onChange={event => setFeedback(event.target.value)} /></div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="grade-actions"><button className="primary-button compact-button" disabled={saving}>{saving ? 'Saving…' : existing ? 'Save updated grade' : 'Record grade'}</button>
          <button type="button" className="secondary-button" disabled={saving} onClick={() => setEditing(false)}>Cancel</button></div>
      </form>}
  </div>
}
