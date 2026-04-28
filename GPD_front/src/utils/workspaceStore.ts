import type { Workspace } from '@/types'

const storageKey = (userId: number) => `GPD_workspaces_${userId}`

export function getWorkspaces(userId: number): Workspace[] {
  const stored = localStorage.getItem(storageKey(userId))
  if (!stored) return []

  try {
    return JSON.parse(stored)
  } catch (_) {
    return []
  }
}

export function saveWorkspaces(userId: number, workspaces: Workspace[]) {
  localStorage.setItem(storageKey(userId), JSON.stringify(workspaces))
}
