import { useCallback } from 'react'
import { Link } from 'react-router'
import { LoadError } from '../components/StudentWorkflow'
import { useResource } from '../hooks/useResource'
import { studentGradeService } from '../services/studentGradeService'

export function StudentGradesPage() {
  const resource = useResource(useCallback((signal: AbortSignal) => studentGradeService.me(signal), []))
  return <>
    <div className="page-heading"><p className="eyebrow">STUDENT WORKSPACE</p><h1>My grades</h1>
      <p className="muted">Your recorded course grades and professor feedback.</p></div>
    {resource.loading ? <p role="status">Loading your grades…</p> : resource.error ?
      <LoadError message={resource.error} retry={resource.reload} /> : resource.data && <>
        {!resource.data.records.length && <section className="workflow-panel">
          <h2>No grades have been recorded yet.</h2>
          {resource.data.missingProfile ? <p>Create your academic profile to get started. <Link to="/profile">Set up my profile →</Link></p> :
            <p className="muted">Grades will appear here once your professor records them. <Link to="/enrollments">View enrollments →</Link></p>}
        </section>}
        <div className="offering-list">{resource.data.records.map(({ grade, enrollment, offering, course, term }) =>
          <article className="workflow-panel" key={grade.id}>
            <h2>{course ? `${course.code} · ${course.title}` : offering ? `Course #${offering.course_id}` : `Enrollment #${grade.enrollment_id}`}</h2>
            <dl className="offering-details">
              <div><dt>Section</dt><dd>{offering?.section ?? 'Unavailable'}</dd></div>
              <div><dt>Academic term</dt><dd>{term ? `${term.name} ${term.academic_year}` : 'Unavailable'}</dd></div>
              <div><dt>Enrollment status</dt><dd>{enrollment ? enrollment.status.charAt(0).toUpperCase() + enrollment.status.slice(1) : 'Unavailable'}</dd></div>
              <div><dt>Graded date</dt><dd><time dateTime={grade.graded_at}>{new Date(grade.graded_at).toLocaleDateString()}</time></dd></div>
            </dl>
            <p><strong>Grade: {grade.grade} / 100</strong></p>
            <h3>Feedback</h3><p className="grade-feedback">{grade.feedback?.trim() ? grade.feedback : 'No feedback provided.'}</p>
            {(!enrollment || !offering || !course || !term) && <div className="notice">Some course details could not be loaded. Your recorded grade is shown above.
              {' '}<button className="secondary-button" onClick={resource.reload}>Try again</button></div>}
          </article>,
        )}</div>
      </>}
  </>
}
