import { useEffect, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { Card, Button, Modal, Input, Alert } from '@/app/components/ui'
import type { Plan } from '@/types'
import { plansAPI } from '@/services/api'

export default function PlansPage() {
  const [plans,    setPlans]    = useState<Plan[]>([])
  const [editing,  setEditing]  = useState<Partial<Plan> | null>(null)
  const [isNew,    setIsNew]    = useState(false)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [errors,   setErrors]   = useState<Record<string,string>>({})
  const [saved,    setSaved]    = useState(false)
  const [loading,  setLoading]  = useState(false)

  // جيب الخطط من API عند فتح الصفحة
  useEffect(() => {
    plansAPI.list().then(res => setPlans(res.data.results ?? res.data)).catch(() => {})
  }, [])

  const empty: Partial<Plan> = {
    name: '', price: 0, checks: 10, max_sources: 5, max_docs: 3,
    allowed_formats: ['pdf','docx','txt']
  }

  const validate = () => {
    const e: Record<string,string> = {}
    if (!editing?.name?.trim()) e.name = 'Name required'
    if ((editing?.price ?? 0) < 0) e.price = 'Price must be positive'
    setErrors(e)
    return Object.keys(e).length === 0
  }

  const save = async () => {
    if (!validate()) return
    setLoading(true)
    try {
      const payload = {
        name:             editing!.name,
        price:            editing!.price,
        checks_per_month: editing!.checks,   // API يستخدم checks_per_month
        max_sources:      editing!.max_sources,
        max_documents:    editing!.max_docs,  // API يستخدم max_documents
        allowed_formats:  editing!.allowed_formats ?? ['pdf','docx','txt'],
        is_active:        true,
      }
      if (isNew) {
        // POST /api/plans/
        const res = await plansAPI.create(payload)
        setPlans(p => [...p, res.data])
      } else {
        // PATCH /api/plans/{id}/
        const res = await plansAPI.update(editing!.id!, payload)
        setPlans(p => p.map(pl => pl.id === editing!.id ? res.data : pl))
      }
      setEditing(null)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err: any) {
      const msg = err.response?.data?.name?.[0] || err.response?.data?.detail || 'Failed to save'
      setErrors({ api: msg })
    } finally {
      setLoading(false)
    }
  }

  const confirmDelete = async () => {
    if (deleteId === null) return
    try {
      // DELETE /api/plans/{id}/
      await plansAPI.delete(deleteId)
      setPlans(p => p.filter(pl => pl.id !== deleteId))
    } catch {
      // إذا فشل — ما يحذف محلياً
    }
    setDeleteId(null)
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Plans Management</h2>
          <p className="text-sm text-muted-foreground mt-0.5">{plans.length} active plans</p>
        </div>
        <div className="flex items-center gap-3">
          {saved && <Alert variant="success">Saved successfully</Alert>}
          <Button onClick={() => { setEditing(empty); setIsNew(true); setErrors({}) }}>
            <Plus size={16}/> Add Plan
          </Button>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {plans.map(p => (
          <Card key={p.id} className="p-5 hover:border-primary/30 transition-colors group relative">
            <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {/* زر Edit — يفتح الـ modal بالبيانات الحالية */}
              <button
                onClick={() => {
                  setEditing({
                    id:              p.id,
                    name:            p.name,
                    price:           p.price,
                    checks:          p.checks_per_month ?? p.checks,
                    max_sources:     p.max_sources,
                    max_docs:        p.max_documents ?? p.max_docs,
                    allowed_formats: p.allowed_formats,
                  })
                  setIsNew(false)
                  setErrors({})
                }}
                className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground">
                <Pencil size={13}/>
              </button>
              {/* زر Delete */}
              <button
                onClick={() => setDeleteId(p.id)}
                className="p-1.5 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive">
                <Trash2 size={13}/>
              </button>
            </div>
            <p className="font-bold text-lg">{p.name}</p>
            <p className="text-3xl font-bold font-mono text-primary mt-1">${p.price}<span className="text-sm font-normal text-muted-foreground">/mo</span></p>
            <div className="mt-4 space-y-1.5 text-sm text-muted-foreground">
              <p>• {(p.checks_per_month ?? p.checks) === -1 ? 'Unlimited checks' : `${p.checks_per_month ?? p.checks} checks/month`}</p>
              <p>• {p.max_sources === -1 ? 'Unlimited sources' : `Up to ${p.max_sources} sources`}</p>
              <p>• {(p.max_documents ?? p.max_docs) === -1 ? 'Unlimited documents' : `Up to ${p.max_documents ?? p.max_docs} documents`}</p>
              <p>• Formats: {(p.allowed_formats ?? []).join(', ').toUpperCase()}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Add / Edit Modal */}
      <Modal isOpen={!!editing} onClose={() => setEditing(null)} title={isNew ? 'Add Plan' : 'Edit Plan'}>
        {editing && (
          <div className="space-y-4">
            {errors.api && <Alert variant="error">{errors.api}</Alert>}
            <Input label="Plan Name" value={editing.name || ''} onChange={e => setEditing(p => ({ ...p!, name: e.target.value }))} error={errors.name}/>
            <Input label="Price ($/mo)" type="number" value={editing.price ?? ''} onChange={e => setEditing(p => ({ ...p!, price: Number(e.target.value) }))} error={errors.price}/>
            <Input label="Checks/month (-1 = unlimited)" type="number" value={editing.checks ?? ''} onChange={e => setEditing(p => ({ ...p!, checks: Number(e.target.value) }))}/>
            <Input label="Max Sources (-1 = unlimited)" type="number" value={editing.max_sources ?? ''} onChange={e => setEditing(p => ({ ...p!, max_sources: Number(e.target.value) }))}/>
            <Input label="Max Documents (-1 = unlimited)" type="number" value={editing.max_docs ?? ''} onChange={e => setEditing(p => ({ ...p!, max_docs: Number(e.target.value) }))}/>
            <div className="flex gap-2 justify-end pt-2">
              <Button variant="outline" onClick={() => setEditing(null)}>Cancel</Button>
              <Button onClick={save} disabled={loading}>{loading ? 'Saving...' : 'Save'}</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm Modal */}
      <Modal isOpen={deleteId !== null} onClose={() => setDeleteId(null)} title="Delete Plan">
        <div className="space-y-4">
          <Alert variant="error">Are you sure you want to delete this plan? Users on this plan will need to be reassigned.</Alert>
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={confirmDelete}>Delete</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
