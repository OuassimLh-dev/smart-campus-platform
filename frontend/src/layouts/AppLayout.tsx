import { NavLink, Outlet } from 'react-router'
import { Brand } from '../components/Brand'
import { useAuth } from '../hooks/useAuth'
import { roleLabels } from '../utils/dashboard'

export function AppLayout() {
  const { user, logout } = useAuth()
  if (!user) return null
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside className="sidebar">
      <Brand />
      <div className="nav-caption">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <NavLink to="/dashboard" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
          <span aria-hidden="true">▦</span> Overview
        </NavLink>
      </nav>
      <div className="sidebar-note"><span className="status-dot" />Your campus, connected.<p>A simpler space for academic life.</p></div>
    </aside>
    <div className="workspace">
      <header className="topbar">
        <span className="breadcrumb">Workspace <span>/</span> <strong>Overview</strong></span>
        <div className="topbar-actions"><span className="role-badge">{roleLabels[user.role]}</span>
          <button className="text-button" onClick={logout}>Log out <span aria-hidden="true">↗</span></button>
        </div>
      </header>
      <main id="main-content" className="main-content"><Outlet /></main>
    </div>
  </div>
}
