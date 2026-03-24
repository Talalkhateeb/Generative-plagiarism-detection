import { useEffect, useState } from 'react'
import { Pencil } from 'lucide-react'
import { Card, Badge, Button, Modal, Alert } from '@/app/components/ui'
import type { User } from '@/types'
import { adminAPI } from '@/services/api'

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<any[]>([])
  const [editing, setEditing] = useState<any | null>(null)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)
  const [saveError, setSaveError] = useState('')

  useEffect(() => {
    adminAPI.listAccounts().then(res => setAccounts(res.data.results ?? res.data)).catch(() => {})
  }, [])

  const save = async () => {
    if (!editing) return
    setLoading(true); setSaveError('')
    try {
      await adminAPI.updateStatus(editing.id, editing.status)
      setAccounts(p => p.map(a => a.id === editing.id ? { ...a, status: editing.status } : a))
      setEditing(null); setSaved(true); setTimeout(() => setSaved(false), 2000)
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || 'Failed to update status')
    } finally {
      setLoading(false)
    }
  }

  // Backend returns plan_name — normalise to plan for display
  const getPlan = (a: any) => a.plan_name ?? a.plan ?? '—'

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold">Accounts Management</h2>
          <p className="text-sm text-muted-foreground mt-0.5">{accounts.length} registered users</p>
        </div>
        {saved && <Alert variant="success">Account updated successfully</Alert>}
      </div>

      <Card>
        <div className="px-5 py-3 border-b border-border grid grid-cols-12 gap-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <span className="col-span-4">User</span>
          <span className="col-span-2">Role</span>
          <span className="col-span-2">Plan</span>
          <span className="col-span-2">Status</span>
          <span className="col-span-2">Joined</span>
        </div>

        {accounts.map(a => (
          <div key={a.id} className="px-5 py-4 border-b border-border last:border-0 grid grid-cols-12 gap-3 items-center hover:bg-accent/40 transition-colors group">
            <div className="col-span-4 flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center text-xs font-bold text-primary flex-shrink-0">
                {a.name.charAt(0)}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{a.name}</p>
                <p className="text-xs text-muted-foreground truncate">{a.email}</p>
              </div>
            </div>
            <div className="col-span-2"><Badge variant={a.role === 'admin' ? 'admin' : 'default'}>{a.role}</Badge></div>
            <span className="col-span-2 text-sm text-muted-foreground">{getPlan(a)}</span>
            <div className="col-span-2"><Badge variant={a.status === 'active' ? 'success' : 'danger'}>{a.status}</Badge></div>
            <div className="col-span-2 flex items-center justify-between">
              <span className="text-xs font-mono text-muted-foreground">
                {a.date_joined ? new Date(a.date_joined).toISOString().split('T')[0] : '—'}
              </span>
              <button onClick={() => { setEditing({ ...a }); setSaveError('') }}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-accent">
                <Pencil size={13} className="text-muted-foreground"/>
              </button>
            </div>
          </div>
        ))}
      </Card>

      {/* Edit Modal — Admin can ONLY change status */}
      <Modal isOpen={!!editing} onClose={() => setEditing(null)} title="Edit Account Status">
        {editing && (
          <div className="space-y-5">
            {saveError && <Alert variant="error">{saveError}</Alert>}
            <div className="flex items-center gap-3 p-3 rounded-lg bg-secondary">
              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary">
                {editing.name.charAt(0)}
              </div>
              <div>
                <p className="font-semibold text-sm">{editing.name}</p>
                <p className="text-xs text-muted-foreground">{editing.email} · {getPlan(editing)}</p>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block mb-2">Account Status</label>
              <div className="flex gap-2">
                {[{ v: 'active', label: '✅ Active' }, { v: 'inactive', label: '❌ Inactive' }].map(s => (
                  <button key={s.v} onClick={() => setEditing((e: any) => ({ ...e, status: s.v }))}
                    className={`flex-1 py-2.5 text-sm rounded-lg border font-medium transition-all
                      ${editing.status === s.v
                        ? s.v === 'active' ? 'bg-emerald-500 border-emerald-500 text-white' : 'bg-destructive border-destructive text-white'
                        : 'border-border text-muted-foreground hover:border-primary/30'}`}>
                    {s.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                {editing.status === 'active'
                  ? 'User can log in and use the platform normally.'
                  : 'User will be blocked from accessing the platform.'}
              </p>
            </div>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setEditing(null)}>Cancel</Button>
              <Button onClick={save} disabled={loading}>{loading ? 'Saving...' : 'Save Changes'}</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
