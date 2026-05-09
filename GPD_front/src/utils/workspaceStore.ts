import type { Workspace } from '@/types'

const storageKey = (userId: number) => `GPDetect_workspaces_${userId}`
const legacyStorageKey = (userId: number) => `GPD_workspaces_${userId}`

export function getWorkspaces(userId: number): Workspace[] {
  const key = storageKey(userId)
  const legacyKey = legacyStorageKey(userId)
  const stored = localStorage.getItem(key) ?? localStorage.getItem(legacyKey)
  if (!stored) return []

  try {
    const parsed = JSON.parse(stored)
    localStorage.setItem(key, stored)
    localStorage.removeItem(legacyKey)
    return parsed
  } catch (_) {
    return []
  }
}

export function saveWorkspaces(userId: number, workspaces: Workspace[]) {
  localStorage.setItem(storageKey(userId), JSON.stringify(workspaces))
}
