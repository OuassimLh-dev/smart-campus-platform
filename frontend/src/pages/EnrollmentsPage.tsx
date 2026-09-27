import { useCallback, useState } from 'react'
import { Link } from 'react-router'
import { LoadError, MissingProfile, OfferingSummary } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { courseOfferingService } from '../services/courseOfferingService'
import { enrollmentService } from '../services/enrollmentService'
import { studentService } from '../services/studentService'
import type { Enrollment } from '../types/enrollment'
import type { OfferingDetails } from '../types/courseOffering'
import { apiError } from '../utils/apiError'

export function EnrollmentsPage() {
  const [confirm, setConfirm] = useState<number | null>(null)
  const [pending, setPending] = useState<number | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const resource = useResource(useCallback(async (signal: AbortSignal) => {
    const profile = await studentService.me(signal)
    if (!profile) return { missing: true, records: [] as Enrollment[], details: [] as OfferingDetails[] }
    const records = await enrollmentService.me(signal)
    const offerings = await Promise.all([...new Set(records.map(record => record.course_offering_id))]
      .map(async id => { try { return await courseOfferingService.get(id, signal) } catch { return null } }))
    const valid = offerings.filter(offering => offering !== null)
    return { missing: false, records, details: await courseOfferingService.enrich(valid, signal) }
  }, []))

  async function drop(id: number) {
    if (pending !== null) return
    setPending(id); setError(''); setMessage('')
    try {
      const updated = await enrollmentService.drop(id)
      resource.setData(current => current ? {
        ...current, records: current.records.map(record => record.id === id ? updated : record),
      } : current)
      setConfirm(null); setMessage('Enrollment dropped. The record remains in your history.')
    } catch (cause) { setError(apiError(cause)) }
    finally { setPending(null) }
  }

  return <>
    <div className="page-heading"><p className="eyebrow">STUDENT WORKSPACE</p><h1>My enrollments</h1>
      <p className="muted">Your current courses and enrollment history.</p></div>
    {error && <div className="form-error" role="alert">{error}</div>}
    {message && <div className="notice" role="status">{message}</div>}
    {resource.loading ? <p role="status">Loading your enrollments…</p> :
      resource.error ? <LoadError message={resource.error} retry={resource.reload} /> :
        resource.data?.missing ? <MissingProfile /> : <>
          {!resource.data?.records.length && <div className="workflow-panel">You have no enrollments yet. <Link to="/courses">Browse course offerings →</Link></div>}
          <div className="offering-list">{resource.data?.records.map(record => {
            const details = resource.data?.details.find(item => item.offering.id === record.course_offering_id)
            return <article className="workflow-panel" key={record.id}>
              <div className="enrollment-meta"><span className={`enrollment-status status-${record.status}`}>{record.status}</span>
                <span>Enrolled {new Date(record.enrolled_at).toLocaleDateString()}</span></div>
              {details ? <OfferingSummary details={details} /> :
                <><h2>Offering #{record.course_offering_id}</h2><p className="muted">Related course details could not be loaded.</p></>}
              {record.status === 'enrolled' && (confirm === record.id ?
                <div className="drop-confirm" role="group" aria-label="Confirm dropping enrollment">
                  <p>Drop this enrollment? Your seat will be released. You cannot re-enroll in this same offering.</p>
                  <button className="secondary-button danger-button" disabled={pending !== null} onClick={() => void drop(record.id)}>
                    {pending === record.id ? 'Dropping…' : 'Confirm drop'}
                  </button>
                  <button className="secondary-button" disabled={pending !== null} onClick={() => setConfirm(null)}>Keep enrollment</button>
                </div> :
                <button className="secondary-button" disabled={pending !== null} onClick={() => setConfirm(record.id)}>Drop enrollment</button>)}
            </article>
          })}</div>
        </>}
  </>
}
