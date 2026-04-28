import { createContext, useContext, useState, useEffect } from 'react'
import type { Workspace } from '@/types'
import {workspacesAPI} from '@/services/api'
import { useAuth } from './AuthContext'

interface WorkspaceCtx {
  workspaces: Workspace[]
  setWorkspaces: React.Dispatch<React.SetStateAction<Workspace[]>>
  updateWorkspaceStatus: (wsId: number, status: string) => void
}

const WorkspaceContext = createContext<WorkspaceCtx>({
  workspaces: [],
  setWorkspaces: () => {},
  updateWorkspaceStatus: () => {}
})

export const WorkspaceProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])

  useEffect(() => {
    if (!user) { setWorkspaces([]); return }
    
    workspacesAPI.list()
      .then(res =>setWorkspaces(res.data.results ?? res.data))
      .catch(()=>setWorkspaces([]))
  }, [user?.id])

  // Update workspace status (called from WorkspaceDetailPage when analysis completes)
  const updateWorkspaceStatus = (wsId: number, status: string) => {
    setWorkspaces(prev => prev.map(w =>
      w.id === wsId ? { ...w, status } : w
    ))
  }

  return (
    <WorkspaceContext.Provider value={{ workspaces, setWorkspaces, updateWorkspaceStatus }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export const useWorkspaces = () => useContext(WorkspaceContext)
