import { AdminManagementPage } from '../pages/AdminManagementPage'
import type { AdminKind } from '../types/admin'
import { ProfessorProfilePage } from '../pages/ProfessorProfilePage'
import { ProfessorCoursesPage } from '../pages/ProfessorCoursesPage'
import { ProfessorRosterPage } from '../pages/ProfessorRosterPage'
import { Navigate, Outlet, Route, Routes } from 'react-router'
import { SessionLoading } from '../components/SessionLoading'
import { useAuth } from '../hooks/useAuth'
import { AppLayout } from '../layouts/AppLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { LoginPage } from '../pages/LoginPage'
import { StudentProfilePage } from '../pages/StudentProfilePage'
import { CourseCatalogPage } from '../pages/CourseCatalogPage'
import { EnrollmentsPage } from '../pages/EnrollmentsPage'

function AdminRoute() {
  const { user } = useAuth()
  return user?.role === 'admin' ? <Outlet /> : <Navigate to="/dashboard" replace />
}

function ProfessorRoute() {
  const { user } = useAuth()
  return user?.role === 'professor' ? <Outlet /> : <Navigate to="/dashboard" replace />
}

function StudentRoute() {
  const { user } = useAuth()
  return user?.role === 'student' ? <Outlet /> : <Navigate to="/dashboard" replace />
}

function ProtectedRoute() {
  const { initializing, isAuthenticated } = useAuth()
  if (initializing) return <SessionLoading />
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

export function AppRoutes() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route element={<AdminRoute />}>
          {(['users', 'departments', 'courses', 'terms', 'course-offerings'] as AdminKind[]).map(kind =>
            <Route key={kind} path={`/admin/${kind}`} element={<AdminManagementPage key={kind} kind={kind} />} />)}
        </Route>
        <Route element={<ProfessorRoute />}>
          <Route path="/professor/profile" element={<ProfessorProfilePage />} />
          <Route path="/professor/courses" element={<ProfessorCoursesPage />} />
          <Route path="/professor/courses/:offeringId/students" element={<ProfessorRosterPage />} />
        </Route>
        <Route element={<StudentRoute />}>
          <Route path="/profile" element={<StudentProfilePage />} />
          <Route path="/courses" element={<CourseCatalogPage />} />
          <Route path="/enrollments" element={<EnrollmentsPage />} />
        </Route>
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
}
