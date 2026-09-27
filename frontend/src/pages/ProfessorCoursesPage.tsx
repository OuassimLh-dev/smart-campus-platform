import { useCallback, useState } from 'react'
import { Link } from 'react-router'
import { LoadError, OfferingSummary } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { professorService } from '../services/professorService'
import { professorCourseService } from '../services/professorCourseService'
import { courseOfferingService } from '../services/courseOfferingService'

export function ProfessorCoursesPage() {
  const [skip, setSkip] = useState(0)
  const resource = useResource(useCallback(async (signal: AbortSignal) => {
    const profile = await professorService.me(signal)
    if (!profile) return null
    const offerings = await professorCourseService.list(profile.id, skip, signal)
    return courseOfferingService.enrich(offerings, signal)
  }, [skip]))
  return <>
    <div className="page-heading"><p className="eyebrow">PROFESSOR WORKSPACE</p><h1>My courses</h1>
      <p className="muted">Assigned offerings, student rosters, and grading.</p></div>
    {resource.loading ? <p role="status">Loading assigned offerings…</p> : resource.error ?
      <LoadError message={resource.error} retry={resource.reload} /> : resource.data === null ?
      <div className="notice">Create your professor profile first. <Link to="/professor/profile">Set up my profile →</Link></div> : <>
        {!resource.data?.length && <p className="notice">No assigned offerings on this page.</p>}
        <div className="offering-list">{resource.data?.map(details => <section className="workflow-panel" key={details.offering.id}>
          <OfferingSummary details={details} />
          <Link to={`/professor/courses/${details.offering.id}/students`}>View students →</Link>
        </section>)}</div>
        <div className="pagination"><button className="secondary-button" disabled={skip === 0} onClick={() => setSkip(s => s - 20)}>Previous</button>
          <span>Page {skip / 20 + 1}</span>
          <button className="secondary-button" disabled={resource.data?.length !== 20} onClick={() => setSkip(s => s + 20)}>Next</button></div>
      </>}
  </>
}
