import { useCallback, useState } from 'react'
import { Link } from 'react-router'
import { LoadError, MissingProfile, OfferingSummary } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { courseOfferingService } from '../services/courseOfferingService'
import { enrollmentService } from '../services/enrollmentService'
import { studentService } from '../services/studentService'
import { apiError, isNotFound } from '../utils/apiError'

export function CourseCatalogPage() {
  const [skip, setSkip] = useState(0)
  const [onlyOpen, setOnlyOpen] = useState(true)
  const [pending, setPending] = useState<number | null>(null)
  const [joined, setJoined] = useState<number[]>([])
  const [missing, setMissing] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  // Profile/enrollment state is independent of catalog pagination and filtering.
  const student = useResource(useCallback(async (signal: AbortSignal) => {
    const profile = await studentService.me(signal)
    const records = profile ? await enrollmentService.me(signal) : []
    return { profile, records }
  }, []))
  const resource = useResource(useCallback(async (signal: AbortSignal) => {
    const offerings = await courseOfferingService.list(skip, onlyOpen, signal)
    return { details: await courseOfferingService.enrich(offerings, signal) }
  }, [skip, onlyOpen]))

  async function enroll(id: number) {
    if (pending !== null || enrollmentStatus(id) !== undefined) return
    setPending(id); setError(''); setMessage('')
    try {
      await enrollmentService.enroll(id)
      setJoined(current => [...current, id])
      setMessage('Enrollment successful.')
    } catch (cause) {
      setError(apiError(cause))
      if (isNotFound(cause)) {
        try { setMissing((await studentService.me()) === null) } catch { /* retain original error */ }
      }
    } finally { setPending(null) }
  }
  const needsProfile = missing || student.data?.profile === null
  const loading = resource.loading || student.loading
  const loadError = resource.error || student.error
  // Every enrollment record blocks re-enrollment, including dropped/completed.
  function enrollmentStatus(id: number) {
    return joined.includes(id) ? 'enrolled' :
      student.data?.records.find(record => record.course_offering_id === id)?.status
  }
  function retry() {
    if (resource.error) resource.reload()
    if (student.error) student.reload()
  }
  return <>
    <div className="page-heading"><p className="eyebrow">STUDENT WORKSPACE</p><h1>Course offerings</h1>
      <p className="muted">Explore courses by section and term. Capacity is the total class size, not remaining seats.</p></div>
    <label className="checkbox-label"><input type="checkbox" checked={onlyOpen}
      onChange={event => { setOnlyOpen(event.target.checked); setSkip(0) }} /> Show open offerings only</label>
    {needsProfile && <MissingProfile />}
    {error && <div className="form-error" role="alert">{error}</div>}
    {message && <div className="notice" role="status">{message} <Link to="/enrollments">View my enrollments →</Link></div>}
    {loading ? <p role="status">Loading course offerings…</p> :
      loadError ? <LoadError message={loadError} retry={retry} /> : <>
        {!resource.data?.details.length && <div className="workflow-panel">No offerings found on this page.</div>}
        <div className="offering-list">{resource.data?.details.map(details =>
          <article className="workflow-panel" key={details.offering.id}>
            <OfferingSummary details={details} />
            <button className="primary-button compact-button"
              disabled={pending !== null || needsProfile || !details.offering.is_open || enrollmentStatus(details.offering.id) !== undefined}
              onClick={() => void enroll(details.offering.id)}>
              {pending === details.offering.id ? 'Enrolling…' : enrollmentStatus(details.offering.id) === 'enrolled' ? 'Enrolled' :
                enrollmentStatus(details.offering.id) !== undefined ? 'Previously enrolled' :
                !details.offering.is_open ? 'Closed' : 'Enroll'}
            </button>
          </article>,
        )}</div>
      </>}
    <nav className="pagination" aria-label="Offering pages">
      <button className="secondary-button" disabled={skip === 0 || loading} onClick={() => setSkip(value => Math.max(0, value - 20))}>Previous</button>
      <span>Page {skip / 20 + 1}</span>
      <button className="secondary-button" disabled={loading || !!loadError || resource.data?.details.length !== 20} onClick={() => setSkip(value => value + 20)}>Next</button>
    </nav>
  </>
}
