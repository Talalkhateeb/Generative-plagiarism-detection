import type { Workspace } from '@/types'
//import { MOCK_WORKSPACES } from './mockData'

// IDs of demo accounts that have pre-seeded data
const DEMO_USER_IDS = [1, 2] // admin@GPD.ai (id:1), user@GPD.ai (id:2)

const STORAGE_KEY = (userId: number) => `GPD_workspaces_${userId}`

export function getWorkspaces(userId: number): Workspace[] {
  // Demo users: check localStorage first, fallback to mock data
  if (DEMO_USER_IDS.includes(userId)) {
    const stored = localStorage.getItem(STORAGE_KEY(userId))
    if (stored) {
      try { return JSON.parse(stored) } catch (_) {}
    }
    // First time: seed with mock data
   /* const seeded = userId === 2 ? MOCK_WORKSPACES : [] // only user@GPD.ai gets mock workspaces
    saveWorkspaces(userId, seeded)
    return seeded*/
  }
  // New / real users: start empty
  const stored = localStorage.getItem(STORAGE_KEY(userId))
  if (stored) {
    try { return JSON.parse(stored) } catch (_) {}
  }
  return []
}

export function saveWorkspaces(userId: number, workspaces: Workspace[]) {
  localStorage.setItem(STORAGE_KEY(userId), JSON.stringify(workspaces))
}
