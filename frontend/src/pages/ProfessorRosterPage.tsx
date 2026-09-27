import { useCallback } from 'react'
import { Link, useParams } from 'react-router'
import { LoadError, OfferingSummary } from '../components/StudentWorkflow'
import { GradeEditor } from '../components/GradeEditor'
import { useResource } from '../hooks/useResource'
import { professorCourseService } from '../services/professorCourseService'
import { courseOfferingService } from '../services/courseOfferingService'
import { gradingService } from '../services/gradingService'

export function ProfessorRosterPage() {
  const { offeringId } = useParams()
  const resource = useResource(useCallback(async (signal: AbortSignal) => {
    const id = Number(offeringId)
    if (!Number.isSafeInteger(id) || id < 1) throw new Error('Invalid offering ID.')
    // Both restricted endpoints must succeed before any roster or grading UI is shown.
    const [roster, grades] = await Promise.all([
      professorCourseService.roster(id, signal), gradingService.list(id, signal),
    ])
    const offering = await courseOfferingService.get(id, signal)
    const [details] = await courseOfferingService.enrich([offering], signal)
    return { roster, grades, details }
  }, [offeringId]))
  return <>
    <div className="page-heading"><p className="eyebrow">PROFESSOR WORKSPACE</p><h1>Students and grades</h1>
      <Link to="/professor/courses">← My courses</Link></div>
    {resource.loading ? <p role="status">Loading roster and grades…</p> : resource.error ?
      <LoadError message={resource.error} retry={resource.reload} /> : resource.data && <>
        <section className="workflow-panel"><OfferingSummary details={resource.data.details} /></section>
        {!resource.data.roster.length && <p className="notice">There are no students in this offering.</p>}
        <div className="offering-list">{resource.data.roster.map(student => <section className="workflow-panel" key={`${offeringId}-${student.id}`}>
          <h2>{student.first_name} {student.last_name}</h2>
          <p className="muted">Student {student.student_number} · Enrollment #{student.id} · {student.status}</p>
          <GradeEditor enrollmentId={student.id} existing={resource.data?.grades.find(grade => grade.enrollment_id === student.id)}
            onSaved={saved => resource.setData(current => current && ({ ...current,
              grades: [...current.grades.filter(grade => grade.enrollment_id !== student.id), saved],
              roster: current.roster.map(entry => entry.id === student.id ? { ...entry, status: 'completed' } : entry),
            }))} />
        </section>)}</div>
      </>}
  </>
}
