import { Link } from 'react-router'
import type { OfferingDetails } from '../types/courseOffering'

export function MissingProfile() {
  return <div className="notice">Create your student profile before enrolling.
    {' '}<Link to="/profile">Set up my profile →</Link></div>
}
export function LoadError({ message, retry }: { message: string; retry: () => void }) {
  return <div className="form-error" role="alert">{message} <button className="secondary-button" onClick={retry}>Try again</button></div>
}
export function OfferingSummary({ details }: { details: OfferingDetails }) {
  const { offering, course, term, professor } = details
  return <>
    <h2>{course ? `${course.code} · ${course.title}` : `Course #${offering.course_id}`}</h2>
    <dl className="offering-details">
      <div><dt>Section</dt><dd>{offering.section}</dd></div>
      <div><dt>Academic term</dt><dd>{term ? `${term.name} ${term.academic_year}` : `Term #${offering.term_id} · details unavailable`}</dd></div>
      <div><dt>Professor</dt><dd>{professor ? `${professor.academic_title} · profile #${professor.id}` : `Profile #${offering.professor_id} · details unavailable`}</dd></div>
      <div><dt>Credits</dt><dd>{course?.credits ?? 'Unavailable'}</dd></div>
      <div><dt>Capacity</dt><dd>{offering.capacity}</dd></div>
      <div><dt>Offering</dt><dd>{offering.is_open ? 'Open' : 'Closed'}</dd></div>
    </dl>
    {(!course || !term || !professor) && <p className="muted">Some related details could not be loaded.</p>}
  </>
}
