import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/app/context/AuthContext'
import { Card, Button, Input, Alert, Modal } from '@/app/components/ui'
import type { Plan } from '@/types'
import { authAPI, plansAPI } from '@/services/api'

export default function ProfilePage() {
  const { user, updateProfile, logout } = useAuth()
  const navigate = useNavigate()

  const [form,       setForm]       = useState({ name: user?.name || '', email: user?.email || '' })
  const [pass,       setPass]       = useState({ current: '', newPass: '', confirm: '' })
  const [errors,     setErrors]     = useState<Record<string,string>>({})
  const [passErrors, setPassErrors] = useState<Record<string,string>>({})
  const [saved,      setSaved]      = useState(false)
  const [passSaved,  setPassSaved]  = useState(false)

  // Delete account state
  const [showDelete,   setShowDelete]   = useState(false)
  const [deletePass,   setDeletePass]   = useState('')
  const [deleteError,  setDeleteError]  = useState('')
  const [deleting,     setDeleting]     = useState(false)

  // Upgrade plan state
  const [plans,           setPlans]           = useState<Plan[]>([])
  const [showUpgrade,     setShowUpgrade]     = useState(false)
  const [selectedPlan,    setSelectedPlan]    = useState<number | null>(null)
  const [upgradeError,    setUpgradeError]    = useState('')
  const [upgrading,       setUpgrading]       = useState(false)
  const [upgradeSuccess,  setUpgradeSuccess]  = useState(false)

  // Load available plans
  useEffect(() => {
    plansAPI.list().then(res => setPlans(res.data.results ?? res.data)).catch(() => {})
  }, [])

  const saveInfo = () => {
    const e: Record<string,string> = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email || !/\S+@\S+\.\S+/.test(form.email)) e.email = 'Valid email required'
    if (Object.keys(e).length) { setErrors(e); return }
    updateProfile({ name: form.name, email: form.email })
    setSaved(true); setTimeout(() => setSaved(false), 2500)
  }

  const savePassword = async () => {
    const e: Record<string,string> = {}
    if (!pass.current) e.current = 'Current password required'
    if (pass.newPass.length < 6) e.newPass = 'Min 6 characters'
    if (pass.newPass !== pass.confirm) e.confirm = 'Passwords do not match'
    if (Object.keys(e).length) { setPassErrors(e); return }
    try {
      await authAPI.changePassword({
        current_password: pass.current,
        new_password:     pass.newPass,
        confirm_password: pass.confirm,
      })
      setPass({ current: '', newPass: '', confirm: '' })
      setPassSaved(true); setTimeout(() => setPassSaved(false), 2500)
    } catch (err: any) {
      setPassErrors({ current: err.response?.data?.current_password?.[0] || 'Incorrect password' })
    }
  }

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  const handleDeleteAccount = async () => {
    if (!deletePass) { setDeleteError('Password is required'); return }
    setDeleting(true); setDeleteError('')
    try {
      await authAPI.deleteAccount(deletePass)
      logout()
      navigate('/login', { replace: true })
    } catch (err: any) {
      setDeleteError(err.response?.data?.error || 'Incorrect password. Please try again.')
      setDeleting(false)
    }
  }

  const handleUpgradePlan = async () => {
    if (!selectedPlan) { setUpgradeError('Please select a plan'); return }
    if (selectedPlan === plans.find(p => p.name === user?.plan)?.id) {
      setUpgradeError('You are already on this plan'); return
    }
    
    setUpgrading(true); setUpgradeError('')
    try {
      await authAPI.upgradePlan(selectedPlan)
      const { data } = await authAPI.me()
      updateProfile(data)
      setUpgradeSuccess(true)
      setShowUpgrade(false)
      setSelectedPlan(null)
    } catch (err: any) {
      setUpgradeError(err.response?.data?.error || 'Failed to upgrade plan')
    } finally {
      setUpgrading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-2xl">
      <div>
        <h2 className="text-xl font-bold">My Account</h2>
        <p className="text-sm text-muted-foreground">Manage your personal information</p>
      </div>

      {/* Avatar */}
      <Card className="p-5 flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center text-2xl font-bold text-primary flex-shrink-0">
          {user?.name?.charAt(0)}
        </div>
        <div className="flex-1">
          <p className="font-bold">{user?.name}</p>
          <p className="text-sm text-muted-foreground">{user?.email}</p>
          <div className="flex gap-2 mt-1.5">
            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/15 text-primary font-medium">{user?.plan} Plan</span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${user?.role === 'admin' ? 'bg-violet-500/15 text-violet-400' : 'bg-secondary text-muted-foreground'}`}>{user?.role}</span>
          </div>
        </div>
        {plans.length > 0 && <Button onClick={() => {
          const currentPlan = plans.find(p => p.name === user?.plan)
          setShowUpgrade(true)
          setSelectedPlan(currentPlan?.id ?? null)
          setUpgradeError('')
        }}>Upgrade Plan</Button>}
      </Card>
      {upgradeSuccess && <Alert variant="success">Plan upgraded successfully!</Alert>}

      {/* Edit Info */}
      <Card className="p-5 space-y-4">
        <h3 className="font-semibold text-sm">Personal Information</h3>
        <Input label="Full Name" value={form.name}
          onChange={e => { setForm(p => ({ ...p, name: e.target.value })); setErrors(p => ({ ...p, name: '' })) }}
          error={errors.name}/>
        <Input label="Email" type="email" value={form.email}
          onChange={e => { setForm(p => ({ ...p, email: e.target.value })); setErrors(p => ({ ...p, email: '' })) }}
          error={errors.email}/>
        {saved && <Alert variant="success">Changes saved successfully</Alert>}
        <div className="flex justify-end"><Button onClick={saveInfo}>Save Changes</Button></div>
      </Card>

      {/* Change Password */}
      <Card className="p-5 space-y-4">
        <h3 className="font-semibold text-sm">Change Password</h3>
        <Input label="Current Password" type="password" value={pass.current}
          onChange={e => { setPass(p => ({ ...p, current: e.target.value })); setPassErrors(p => ({ ...p, current: '' })) }}
          error={passErrors.current}/>
        <Input label="New Password" type="password" value={pass.newPass}
          onChange={e => { setPass(p => ({ ...p, newPass: e.target.value })); setPassErrors(p => ({ ...p, newPass: '' })) }}
          error={passErrors.newPass}/>
        <Input label="Confirm New Password" type="password" value={pass.confirm}
          onChange={e => { setPass(p => ({ ...p, confirm: e.target.value })); setPassErrors(p => ({ ...p, confirm: '' })) }}
          error={passErrors.confirm}/>
        {passSaved && <Alert variant="success">Password changed successfully</Alert>}
        <div className="flex justify-end">
          <Button variant="outline" onClick={savePassword}>Change Password</Button>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card className="p-5 border-destructive/30">
        <h3 className="font-semibold text-sm text-destructive mb-4">Danger Zone</h3>

        {/* Sign Out */}
        <div className="flex items-center justify-between py-3 border-b border-border">
          <div>
            <p className="text-sm font-medium">Sign Out</p>
            <p className="text-xs text-muted-foreground">End your current session</p>
          </div>
          <Button variant="outline" onClick={handleLogout}>Sign Out</Button>
        </div>

        {/* Delete Account */}
        <div className="flex items-center justify-between pt-3">
          <div>
            <p className="text-sm font-medium text-destructive">Delete Account</p>
            <p className="text-xs text-muted-foreground">
              Permanently delete your account and all data. This cannot be undone.
            </p>
          </div>
          <Button variant="destructive" onClick={() => { setShowDelete(true); setDeletePass(''); setDeleteError('') }}>
            Delete Account
          </Button>
        </div>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={showDelete} onClose={() => setShowDelete(false)} title="Delete Account">
        <div className="space-y-4">
          <Alert variant="error">
            This will permanently delete your account, all workspaces, and all results. This action cannot be undone.
          </Alert>
          <Input
            label="Enter your password to confirm"
            type="password"
            value={deletePass}
            onChange={e => { setDeletePass(e.target.value); setDeleteError('') }}
            placeholder="Your current password"
            error={deleteError}
            autoFocus
          />
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={() => setShowDelete(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteAccount} disabled={deleting}>
              {deleting ? 'Deleting…' : 'Yes, Delete My Account'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Upgrade Plan Modal */}
      <Modal isOpen={showUpgrade} onClose={() => setShowUpgrade(false)} title="Upgrade Plan">
        <div className="space-y-4">
          {upgradeError && <Alert variant="error">{upgradeError}</Alert>}
          
          <div className="text-sm text-muted-foreground mb-4">
            Current plan: <span className="font-semibold text-foreground">{user?.plan}</span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {plans.map(plan => (
              <div
                key={plan.id}
                onClick={() => setSelectedPlan(plan.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedPlan === plan.id
                    ? 'border-primary bg-primary/10'
                    : plan.name === user?.plan
                    ? 'border-muted opacity-50 cursor-not-allowed'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{plan.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {plan.checks_per_month === -1 ? 'Unlimited checks' : `${plan.checks_per_month} checks/month`}
                    </p>
                  </div>
                  <p className="text-lg font-bold text-primary">${plan.price}<span className="text-xs font-normal">/mo</span></p>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2 justify-end pt-2">
            <Button variant="outline" onClick={() => setShowUpgrade(false)}>Cancel</Button>
            <Button onClick={handleUpgradePlan} disabled={upgrading || !selectedPlan}>
              {upgrading ? 'Upgrading…' : 'Confirm Upgrade'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
