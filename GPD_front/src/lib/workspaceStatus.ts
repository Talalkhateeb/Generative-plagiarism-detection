export type NormalizedWorkspaceStatus = 'draft' | 'pending' | 'analyzed'

export function normalizeWorkspaceStatus(status?: string): NormalizedWorkspaceStatus {
  if (status === 'completed') return 'analyzed'
  if (status === 'pending') return 'pending'
  if (status === 'analyzed') return 'analyzed'
  return 'draft'
}

export function workspaceStatusBadgeVariant(status?: string): 'default' | 'warning' | 'success' {
  const normalized = normalizeWorkspaceStatus(status)
  if (normalized === 'analyzed') return 'success'
  if (normalized === 'pending') return 'warning'
  return 'default'
}
