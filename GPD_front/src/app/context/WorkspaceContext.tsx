import { createContext, useContext, useState, useEffect } from 'react'
import type { Workspace } from '@/types'
import {workspacesAPI} from '@/services/api'
import { useAuth } from './AuthContext'
import { normalizeWorkspaceStatus } from '@/lib/workspaceStatus'

interface WorkspaceCtx {
  workspaces: Workspace[]
  setWorkspaces: React.Dispatch<React.SetStateAction<Workspace[]>>
  loading: boolean
}
const WorkspaceContext = createContext<WorkspaceCtx>({ workspaces: [], setWorkspaces: () => {}, loading: false })

export const WorkspaceProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) { setWorkspaces([]); setLoading(false); return }

    setLoading(true)
    workspacesAPI.list()
      .then(res => {
        const raw = res.data.results ?? res.data
        setWorkspaces((raw ?? []).map((w: Workspace) => ({
          ...w,
          status: normalizeWorkspaceStatus(w.status),
        })))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user?.id])
      
  return (
    <WorkspaceContext.Provider value={{ workspaces, setWorkspaces, loading }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export const useWorkspaces = () => useContext(WorkspaceContext)
