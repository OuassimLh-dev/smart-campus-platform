import { useAuth } from '../hooks/useAuth'
import { dashboardSections, roleLabels } from '../utils/dashboard'

export function DashboardPage() {
  const { user } = useAuth()
  if (!user) return null
  const sections = dashboardSections[user.role]
  return <>
    <div className="page-heading"><p className="eyebrow">YOUR WORKSPACE</p>
      <h1>Welcome, {user.first_name}.</h1><p className="muted">A clear view of your campus life. All in one place.</p>
    </div>
    <section className="profile-card" aria-labelledby="profile-heading">
      <div className="avatar" aria-hidden="true">{user.first_name.charAt(0)}{user.last_name.charAt(0)}</div>
      <div className="profile-identity"><p className="eyebrow">SIGNED IN AS</p>
        <h2 id="profile-heading">{user.first_name} {user.last_name}</h2><p>{user.email}</p>
      </div>
      <div className="profile-role"><span>Account role</span><strong>{roleLabels[user.role]}</strong></div>
    </section>
    <section className="dashboard-section" aria-labelledby="tools-heading">
      <div className="section-heading"><h2 id="tools-heading">Your academic workspace</h2><span>{sections.length} areas</span></div>
      <div className="card-grid">{sections.map((section, index) =>
        <article className="feature-card" key={section.title}>
          <div className="card-top"><span className="card-number">0{index + 1}</span><span className="soon-badge">Coming soon</span></div>
          <h3>{section.title}</h3><p>{section.description}</p>
          <div className="card-footer">Part of your {roleLabels[user.role].toLowerCase()} workspace</div>
        </article>,
      )}</div>
    </section>
    <footer className="dashboard-footer">Smart Campus <span>·</span> A foundation for better academic experiences.</footer>
  </>
}
