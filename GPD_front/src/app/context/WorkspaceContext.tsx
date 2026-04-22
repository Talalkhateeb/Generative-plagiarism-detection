import { createContext, useContext, useState, useEffect } from 'react'
import type { Workspace } from '@/types'
import {workspacesAPI} from '@/services/api'
import { useAuth } from './AuthContext'

interface WorkspaceCtx {
  workspaces: Workspace[]
  setWorkspaces: React.Dispatch<React.SetStateAction<Workspace[]>>
}
const WorkspaceContext = createContext<WorkspaceCtx>({ workspaces: [], setWorkspaces: () => {} })

export const WorkspaceProvider = ({ children }: { children: React.ReactNode }) => {
  const { user } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])

  useEffect(() => {
    if (!user) { setWorkspaces([]); return }
    
    workspacesAPI.list()
      .then(res =>setWorkspaces(res.data.results ?? res.data))
      .catch(()=>setWorkspaces([]))},
      [user?.id])
      
  return (
    <WorkspaceContext.Provider value={{ workspaces, setWorkspaces }}>
      {children}
    </WorkspaceContext.Provider>
  )
}

export const useWorkspaces = () => useContext(WorkspaceContext)
