import { createBrowserRouter, Navigate } from 'react-router-dom'
import { useAuth } from '@/app/context/AuthContext'
import Layout from '@/app/components/Layout'
import { Spinner } from '@/app/components/ui'

import LoginPage         from '@/pages/LoginPage'
import DashboardPage     from '@/pages/DashboardPage'
import WorkspacesPage    from '@/pages/WorkspacesPage'
import WorkspaceDetail   from '@/pages/WorkspaceDetailPage'
import HistoryPage       from '@/pages/HistoryPage'
import ProfilePage       from '@/pages/user/ProfilePage'
import PlansPage         from '@/pages/admin/PlansPage'
import AccountsPage      from '@/pages/admin/AccountsPage'

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center"><Spinner size={32}/></div>
  return user ? <>{children}</> : <Navigate to="/login" replace/>
}
function AdminOnly({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  return user?.role === 'admin' ? <>{children}</> : <Navigate to="/" replace/>
}

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage/> },
  {
    element: <Protected><Layout/></Protected>,
    children: [
      { index: true, element: <DashboardPage/> },
      { path: 'workspaces', element: <WorkspacesPage/> },
      { path: 'workspaces/:id', element: <WorkspaceDetail/> },
      { path: 'history', element: <HistoryPage/> },
      { path: 'profile', element: <ProfilePage/> },
      { path: 'admin/plans',    element: <AdminOnly><PlansPage/></AdminOnly> },
      { path: 'admin/accounts', element: <AdminOnly><AccountsPage/></AdminOnly> },
    ]
  },
  { path: '*', element: <Navigate to="/" replace/> }
])
