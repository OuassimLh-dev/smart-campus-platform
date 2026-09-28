import { useState } from 'react'
import type { FormEvent } from 'react'
import type { AdminInput, AdminKind, AdminRecord, Option } from '../types/admin'
import { adminFields } from '../utils/adminFields'
import { adminService } from '../services/adminService'
import { apiError } from '../utils/apiError'

export function AdminForm({ kind, record, options, onSaved, onCancel }: {
  kind: AdminKind; record: AdminRecord | null; options: Record<string, Option[]>;
  onSaved: (record: AdminRecord) => void; onCancel: () => void
}) {
  const fields = adminFields[kind]
  const source = record as unknown as Record<string, unknown> | null
  const [draft, setDraft] = useState<Record<string, string | boolean>>(() => Object.fromEntries(fields.map(field =>
    [field.key, field.type === 'checkbox' ? source ? Boolean(source[field.key]) : true : String(source?.[field.key] ?? '')])))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving) return
    setError('')
    const payload: Record<string, string | number | boolean | null> = {}
    for (const field of fields) {
      const value = draft[field.key]
      if (field.type === 'checkbox') { payload[field.key] = Boolean(value); continue }
      const text = String(value).trim()
      if (!text && !field.nullable) { setError(`${field.label} is required.`); return }
      if (!text && field.nullable) { payload[field.key] = null; continue }
      if (field.type === 'number' || field.key.endsWith('_id')) {
        const number = Number(text)
        if (!Number.isSafeInteger(number) || number < 1) { setError(`${field.label} must be a positive integer.`); return }
        payload[field.key] = number
      } else payload[field.key] = text
    }
    if (kind === 'terms' && String(payload.start_date) >= String(payload.end_date)) {
      setError('Start date must be before end date.'); return
    }
    setSaving(true)
    try {
      const input = payload as unknown as AdminInput<typeof kind>
      const saved = record ? await adminService.update(kind, record.id, input) :
        kind !== 'users' ? await adminService.create(kind, input as AdminInput<Exclude<AdminKind, 'users'>>) : null
      if (saved) onSaved(saved)
    } catch (cause) { setError(apiError(cause)) }
    finally { setSaving(false) }
  }
  return <section className="workflow-panel">
    <h2>{record ? `Edit record #${record.id}` : 'Create record'}</h2>
    <form className="profile-form" onSubmit={submit} aria-busy={saving}>
      <div className="form-grid">{fields.map(field => {
        const id = `admin-${field.key}`
        const choices = field.options ?? options[field.key] ?? []
        const value = String(draft[field.key])
        return <div key={field.key}><label htmlFor={id}>{field.label}{field.nullable ? ' (optional)' : ''}</label>
          {field.type === 'checkbox' ? <input id={id} type="checkbox" checked={Boolean(draft[field.key])} disabled={saving}
            onChange={event => setDraft(current => ({ ...current, [field.key]: event.target.checked }))} /> :
          field.type === 'select' ? <select id={id} required={!field.nullable} disabled={saving} value={value}
            onChange={event => setDraft(current => ({ ...current, [field.key]: event.target.value }))}>
            <option value="">{field.nullable ? 'None' : 'Select…'}</option>
            {value && !choices.some(option => option.value === value) && <option value={value}>Existing reference #{value} (not in active list)</option>}
            {choices.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select> : field.type === 'textarea' ? <textarea id={id} rows={3} maxLength={field.maxLength} disabled={saving} value={value}
            onChange={event => setDraft(current => ({ ...current, [field.key]: event.target.value }))} /> :
          <input id={id} type={field.type ?? 'text'} required maxLength={field.maxLength} disabled={saving} value={value}
            min={field.type === 'number' ? 1 : undefined} step={field.type === 'number' ? 1 : undefined}
            onChange={event => setDraft(current => ({ ...current, [field.key]: event.target.value }))} />}
        </div>
      })}</div>
      {source?.is_active === true && draft.is_active === false && <label className="notice">
        <input type="checkbox" required disabled={saving} /> Confirm deactivation: this record will become inactive and be retained in the database.
      </label>}
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="grade-actions"><button className="primary-button compact-button" disabled={saving}>{saving ? 'Saving…' : record ? 'Save changes' : 'Create'}</button>
        <button type="button" className="secondary-button" disabled={saving} onClick={onCancel}>Cancel</button></div>
    </form>
  </section>
}
