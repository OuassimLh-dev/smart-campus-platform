import { useCallback, useState } from 'react'
import { AdminForm } from '../components/AdminForm'
import { LoadError } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { useAuth } from '../hooks/useAuth'
import { adminOptions, adminService } from '../services/adminService'
import type { AdminKind, AdminRecord, Filters } from '../types/admin'
import { adminFields, adminTitles } from '../utils/adminFields'
import { apiError } from '../utils/apiError'

export function AdminManagementPage({ kind }: { kind: AdminKind }) {
  const { user, logout } = useAuth()
  const [skip, setSkip] = useState(0)
  const [filters, setFilters] = useState<Filters>({})
  const resource = useResource(useCallback(async (signal: AbortSignal) => {
    const [records, options] = await Promise.all([adminService.list(kind, skip, filters, signal), adminOptions(kind, signal)])
    return { records, options }
  }, [kind, skip, filters]))
  const [editing, setEditing] = useState<AdminRecord | null | undefined>(undefined)
  const [confirm, setConfirm] = useState<AdminRecord | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const canDeactivate = kind === 'users' || kind === 'departments' || kind === 'courses'
  function refresh(message: string) { setMessage(message); setError(''); setEditing(undefined); setConfirm(null); resource.reload() }
  async function deactivate() {
    if (!confirm || !canDeactivate || busy) return
    setBusy(true); setError('')
    try {
      await adminService.deactivate(kind, confirm.id)
      if (kind === 'users' && confirm.id === user?.id) { logout(); return }
      refresh('Record deactivated. The database record has been retained.')
    } catch (cause) { setError(apiError(cause)) }
    finally { setBusy(false) }
  }
  return <>
    <div className="page-heading"><p className="eyebrow">ADMIN WORKSPACE</p><h1>{adminTitles[kind]}</h1>
      <p className="muted">Manage campus {adminTitles[kind].toLowerCase()}.</p></div>
    {(kind === 'departments' || kind === 'courses') && <p className="notice">Only active records appear here. Deactivated records are retained but disappear from this list.</p>}
    {message && <p className="notice" role="status">{message}</p>}
    {error && <p className="form-error" role="alert">{error}</p>}
    {resource.loading ? <p role="status">Loading {adminTitles[kind].toLowerCase()}…</p> : resource.error ?
      <LoadError message={resource.error} retry={resource.reload} /> : resource.data && <>
      {editing !== undefined ? <AdminForm key={editing?.id ?? 'new'} kind={kind} record={editing} options={resource.data.options}
        onCancel={() => setEditing(undefined)} onSaved={saved => {
          if (kind === 'users' && saved.id === user?.id && ('role' in saved) && (saved.role !== 'admin' || !saved.is_active)) { logout(); return }
          refresh('Changes saved.');
        }} /> : <>
        {kind !== 'users' && <button className="primary-button compact-button" disabled={busy || !!confirm} onClick={() => { setMessage(''); setEditing(null) }}>Create {adminTitles[kind].toLowerCase()}</button>}
        {kind === 'course-offerings' && <div className="admin-filters">{['course_id', 'professor_id', 'term_id', 'is_open'].map(key =>
          <div key={key}><label htmlFor={`filter-${key}`}>Filter {key === 'is_open' ? 'status' : key.replace('_id', '')}</label>
            <select id={`filter-${key}`} disabled={busy || !!confirm} value={filters[key] ?? ''} onChange={event => { setSkip(0); setFilters(current => ({ ...current, [key]: event.target.value })) }}>
              <option value="">All</option>
              {(key === 'is_open' ? [{ value: 'true', label: 'Open' }, { value: 'false', label: 'Closed' }] : resource.data?.options[key] ?? []).map(option =>
                <option key={option.value} value={option.value}>{option.label}</option>)}
            </select></div>)}</div>}
        {confirm && <section className="notice" aria-label="Confirm deactivation">
          <p>Deactivate record #{confirm.id}? It will be marked inactive, not physically deleted.{kind === 'users' && confirm.id === user?.id ? ' You will be signed out.' : ''}</p>
          <button className="danger-button" disabled={busy} onClick={deactivate}>{busy ? 'Deactivating…' : 'Confirm deactivation'}</button>{' '}
          <button className="secondary-button" disabled={busy} onClick={() => setConfirm(null)}>Cancel</button>
        </section>}
        {!resource.data.records.length ? <p className="notice">No records on this page.</p> : <div className="admin-table-wrap"><table className="admin-table">
          <thead><tr><th>ID</th>{adminFields[kind].map(field => <th key={field.key}>{field.label}</th>)}<th>Created</th><th>Actions</th></tr></thead>
          <tbody>{resource.data.records.map(record => <tr key={record.id}><td>{record.id}</td>
            {adminFields[kind].map(field => {
              const value = (record as unknown as Record<string, unknown>)[field.key]
              const label = resource.data?.options[field.key]?.find(option => option.value === String(value))?.label
              return <td key={field.key}>{value == null ? '—' : typeof value === 'boolean' ? value ? 'Yes' : 'No' : label ?? String(value)}</td>
            })}<td>{new Date(record.created_at).toLocaleDateString()}</td>
            <td><div className="grade-actions"><button className="secondary-button" disabled={busy || !!confirm} onClick={() => { setMessage(''); setEditing(record) }}>Edit #{record.id}</button>
              {canDeactivate && 'is_active' in record && record.is_active && <button className="text-button" disabled={busy || !!confirm} onClick={() => { setError(''); setConfirm(record) }}>Deactivate #{record.id}</button>}
            </div></td></tr>)}</tbody>
        </table></div>}
        <div className="pagination"><button className="secondary-button" disabled={skip === 0 || busy || !!confirm} onClick={() => setSkip(s => s - 20)}>Previous</button>
          <span>Page {skip / 20 + 1}</span><button className="secondary-button" disabled={resource.data.records.length !== 20 || busy || !!confirm} onClick={() => setSkip(s => s + 20)}>Next</button></div>
      </>}
    </>}
  </>
}
