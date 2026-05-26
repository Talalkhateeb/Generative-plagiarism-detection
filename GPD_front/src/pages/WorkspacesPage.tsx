import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Pencil, Trash2, ArrowRight } from 'lucide-react'
import { Card, Badge, Button, Modal, Input, Alert } from '@/app/components/ui'
import { useWorkspaces } from '@/app/context/WorkspaceContext'
import { workspacesAPI } from '@/services/api'
import type { Workspace } from '@/types'

export default function WorkspacesPage() {
  const navigate = useNavigate()
  const { workspaces, setWorkspaces } = useWorkspaces()
  const [showCreate, setShowCreate] = useState(false)
  const [editWs, setEditWs] = useState<Workspace | null>(null)
  const [deleteWs, setDeleteWs] = useState<Workspace | null>(null)
  const [name, setName] = useState('')
  const [nameError, setNameError] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  const createWorkspace = async () => {
    if (!name.trim()) { setNameError('Name is required'); return }
    setLoading(true); setApiError('')
    try {
      const res = await workspacesAPI.create(name.trim())
      const nw: Workspace = {
        id: res.data.id,
        name: res.data.name,
        created_at: res.data.created_at?.split('T')[0] ?? new Date().toISOString().split('T')[0],
        status: res.data.status ?? 'draft',
        sources_count: res.data.sources_count ?? 0,
        documents_count: res.data.documents_count ?? 0,
        submissions: [],
      }
      setWorkspaces(p => [nw, ...p])
      setName(''); setShowCreate(false)
      // Guard: only navigate if we got a real id back from the API
      if (nw.id) {
        navigate(`/workspaces/${nw.id}`, { state: { workspace: nw } })
      }
    } catch (err: any) {
      setApiError(err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to create workspace')
    } finally {
      setLoading(false)
    }
  }

  const saveEdit = async () => {
    if (!editWs || !name.trim()) { setNameError('Name is required'); return }
    setLoading(true); setApiError('')
    try {
      await workspacesAPI.rename(editWs.id, name.trim())
      setWorkspaces(p => p.map(w => w.id === editWs.id ? { ...w, name: name.trim() } : w))
      setEditWs(null); setName('')
    } catch (err: any) {
      setApiError(err.response?.data?.detail || 'Failed to rename workspace')
    } finally {
      setLoading(false)
    }
  }

  const confirmDelete = async () => {
    if (!deleteWs) return
    setLoading(true)
    try {
      await workspacesAPI.delete(deleteWs.id)
      setWorkspaces(p => p.filter(w => w.id !== deleteWs.id))
      setDeleteWs(null)
    } catch (err: any) {
      setApiError(err.response?.data?.detail || 'Failed to delete workspace')
      setDeleteWs(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Workspaces</h2>
          <p className="text-sm text-muted-foreground mt-0.5">{workspaces.length} workspace{workspaces.length !== 1 ? 's' : ''}</p>
        </div>
        <Button onClick={() => { setName(''); setNameError(''); setApiError(''); setShowCreate(true) }}>
          <Plus size={16}/> New Workspace
        </Button>
      </div>

      {apiError && <Alert variant="error">{apiError}</Alert>}

      {workspaces.length === 0 ? (
        <Card className="p-12 text-center">
          <FolderOpen size={40} className="text-muted-foreground mx-auto mb-3 opacity-40"/>
          <p className="font-semibold">No workspaces yet</p>
          <p className="text-sm text-muted-foreground mt-1 mb-4">Create your first workspace to start checking documents</p>
          <Button onClick={() => { setName(''); setNameError(''); setApiError(''); setShowCreate(true) }}>
            <Plus size={16}/> Create Workspace
          </Button>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {workspaces.map(w => (
            <Card key={w.id} className="p-5 hover:border-primary/30 transition-colors group">
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                  <FolderOpen size={18} className="text-primary"/>
                </div>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => { setEditWs(w); setName(w.name); setNameError(''); setApiError('') }}
                    className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground">
                    <Pencil size={13}/>
                  </button>
                  <button onClick={() => { setApiError(''); setDeleteWs(w) }}
                    className="p-1.5 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive">
                    <Trash2 size={13}/>
                  </button>
                </div>
              </div>
              <h3 className="font-semibold text-sm mb-1 truncate">{w.name}</h3>
              <p className="text-xs text-muted-foreground mb-3">
                {w.created_at} · {w.sources_count} sources · {w.documents_count} docs
              </p>
              <div className="flex items-center justify-between">
                <Badge variant={w.status === 'analyzed' ? 'success' : w.status === 'pending' ? 'warning' : 'default'}>
                  {w.status}
                </Badge>
                <button onClick={() => navigate(`/workspaces/${w.id}`)}
                  className="flex items-center gap-1 text-xs text-primary hover:underline">
                  Open <ArrowRight size={12}/>
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Workspace">
        <div className="space-y-4">
          {apiError && <Alert variant="error">{apiError}</Alert>}
          <Input label="Workspace Name" value={name} onChange={e => { setName(e.target.value); setNameError('') }}
            placeholder="e.g. Research Paper Q2" error={nameError} autoFocus/>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={createWorkspace} disabled={loading}>{loading ? 'Creating...' : 'Create'}</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!editWs} onClose={() => setEditWs(null)} title="Rename Workspace">
        <div className="space-y-4">
          {apiError && <Alert variant="error">{apiError}</Alert>}
          <Input label="New Name" value={name} onChange={e => { setName(e.target.value); setNameError('') }}
            placeholder="Workspace name" error={nameError} autoFocus/>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setEditWs(null)}>Cancel</Button>
            <Button onClick={saveEdit} disabled={loading}>{loading ? 'Saving...' : 'Save'}</Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!deleteWs} onClose={() => setDeleteWs(null)} title="Delete Workspace">
        <div className="space-y-4">
          <Alert variant="error">
            This will permanently delete <strong>{deleteWs?.name}</strong> and all its submissions.
          </Alert>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteWs(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={loading}>
              <Trash2 size={14}/> {loading ? 'Deleting...' : 'Delete'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
