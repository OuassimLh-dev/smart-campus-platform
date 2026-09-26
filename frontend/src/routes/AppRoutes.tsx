import { Navigate, Outlet, Route, Routes } from 'react-router'
import { SessionLoading } from '../components/SessionLoading'
import { useAuth } from '../hooks/useAuth'
import { AppLayout } from '../layouts/AppLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { LoginPage } from '../pages/LoginPage'

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
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>
}
