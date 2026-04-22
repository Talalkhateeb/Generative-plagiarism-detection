import { useNavigate } from 'react-router-dom'
import { FolderOpen, Shield, BarChart3, FileText, ArrowRight, Activity, Users, Settings, Sparkles } from 'lucide-react'
import { useAuth } from '@/app/context/AuthContext'
import { useWorkspaces } from '@/app/context/WorkspaceContext'
import { Card, Badge } from '@/app/components/ui'
import { useState, useEffect } from 'react'
import { adminAPI, plansAPI, submissionsAPI } from '@/services/api'

export default function DashboardPage() {
  const { user } = useAuth()
  const { workspaces } = useWorkspaces()
  const navigate = useNavigate()
  const isAdmin  = user?.role === 'admin'
  const isNewUser = workspaces.length === 0

  // ── Admin stats ────────────────────────────────────────────
  const [recentAccounts, setRecentAccounts] = useState<any[]>([])
  const [recentPlans,    setRecentPlans]    = useState<any[]>([])
  const [statsData,      setStatsData]      = useState({ users: 0, active: 0, plans: 0 })

  // ── User stats ─────────────────────────────────────────────
  const [checksUsed,  setChecksUsed]  = useState(0)
  const [planLimit,   setPlanLimit]   = useState<number | null>(null)
  const [planName,    setPlanName]    = useState(user?.plan ?? '—')

  // Collect all plagiarism scores from document_results (new structure)
  const allScores = workspaces.flatMap(w =>
    (w.submissions ?? []).flatMap((s: any) =>
      (s.document_results ?? []).map((r: any) => r.plagiarism_score)
    ).filter((v: any) => v !== undefined && v !== null)
  )
  const avgScore = allScores.length
    ? (allScores.reduce((a: number, b: number) => a + b, 0) / allScores.length).toFixed(1)
    : '—'
  const totalSubs = workspaces.reduce((s, w) => s + (w.submissions?.length ?? 0), 0)

  useEffect(() => {
    if (isAdmin) {
      // Admin: جيب accounts و plans من API
      Promise.all([adminAPI.listAccounts(), plansAPI.list()])
        .then(([accRes, plRes]) => {
          const accounts = accRes.data.results ?? accRes.data
          const plans    = plRes.data.results   ?? plRes.data
          setRecentAccounts(accounts.slice(0, 4))
          setRecentPlans(plans)
          setStatsData({
            users:  accounts.length,
            active: accounts.filter((a: any) => a.status === 'active').length,
            plans:  plans.length,
          })
        })
        .catch(() => {}) // سيرفر مو شغّال — تبقى أصفار
    } else {
      // User: جيب plan info و checks used
      Promise.all([submissionsAPI.history(), plansAPI.list()])
        .then(([histRes, plRes]) => {
          const history = histRes.data.results ?? histRes.data
          setChecksUsed(history.length)
          const plans   = plRes.data.results ?? plRes.data
          const myPlan  = plans.find((p: any) => p.name === user?.plan)
          if (myPlan) {
            setPlanLimit(myPlan.checks_per_month)
            setPlanName(myPlan.name)
          }
        })
        .catch(() => {}) // fallback — تبقى 0
    }
  }, [isAdmin, user?.plan])

  const checksRemaining = planLimit === null
    ? '...'
    : planLimit === -1
      ? '∞'
      : Math.max(0, planLimit - checksUsed)

  // ── ADMIN DASHBOARD ─────────────────────────────────────────
  if (isAdmin) return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold">System Overview</h2>
        <p className="text-sm text-muted-foreground mt-0.5">Admin dashboard — platform status</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Users',  value: statsData.users,  icon: Users,    color: 'text-primary bg-primary/10' },
          { label: 'Active Users', value: statsData.active, icon: Activity, color: 'text-emerald-400 bg-emerald-400/10' },
          { label: 'Active Plans', value: statsData.plans,  icon: Shield,   color: 'text-violet-400 bg-violet-400/10' },
          { label: 'Total Checks', value: '—',              icon: FileText, color: 'text-amber-400 bg-amber-400/10' },
        ].map(s => (
          <Card key={s.label} className="p-4">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${s.color}`}><s.icon size={18}/></div>
            <p className="text-2xl font-bold font-mono">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>
      <div className="grid lg:grid-cols-2 gap-5">
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm">Recent Accounts</h3>
            <button onClick={() => navigate('/admin/accounts')} className="text-xs text-primary hover:underline flex items-center gap-1">View all <ArrowRight size={12}/></button>
          </div>
          {recentAccounts.length === 0
            ? <p className="text-xs text-muted-foreground">No accounts yet</p>
            : recentAccounts.map(a => (
              <div key={a.id} className="flex items-center gap-3 py-2.5 border-b border-border last:border-0">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">{a.name.charAt(0)}</div>
                <div className="flex-1 min-w-0"><p className="text-sm font-medium truncate">{a.name}</p><p className="text-xs text-muted-foreground truncate">{a.email}</p></div>
                <Badge variant={a.status === 'active' ? 'success' : 'danger'}>{a.status}</Badge>
              </div>
            ))}
        </Card>
        <Card className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm">Plans Overview</h3>
            <button onClick={() => navigate('/admin/plans')} className="text-xs text-primary hover:underline flex items-center gap-1">Manage <ArrowRight size={12}/></button>
          </div>
          {recentPlans.length === 0
            ? <p className="text-xs text-muted-foreground">No plans yet</p>
            : recentPlans.map(p => (
              <div key={p.id} className="flex items-center justify-between py-2.5 border-b border-border last:border-0">
                <div><p className="text-sm font-semibold">{p.name}</p><p className="text-xs text-muted-foreground">{p.checks_per_month === -1 ? 'Unlimited' : `${p.checks_per_month} checks/mo`}</p></div>
                <span className="text-primary font-bold font-mono">${p.price}/mo</span>
              </div>
            ))}
        </Card>
      </div>
    </div>
  )

  // ── NEW USER — Welcome screen ────────────────────────────────
  if (isNewUser) return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold">Welcome, {user?.name?.split(' ')[0]}! 👋</h2>
        <p className="text-sm text-muted-foreground mt-0.5">You're all set — let's get started</p>
      </div>
      <Card className="p-8 text-center border-primary/20 bg-primary/5 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent pointer-events-none"/>
        <div className="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center mx-auto mb-4">
          <Sparkles size={28} className="text-primary"/>
        </div>
        <h3 className="text-lg font-bold mb-2">Welcome to GPD.AI</h3>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          GPD.AI helps you detect plagiarism in academic documents using AI.
          Create a workspace, upload your sources and documents, and get a detailed plagiarism report in seconds.
        </p>
        <button onClick={() => navigate('/workspaces')}
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-primary/90 transition-colors">
          <FolderOpen size={16}/> Create Your First Workspace
        </button>
      </Card>
      <div>
        <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide mb-4">How it works</h3>
        <div className="grid sm:grid-cols-3 gap-4">
          {[
            { step: '1', title: 'Create Workspace', desc: 'Organize your documents in a dedicated workspace', icon: FolderOpen, color: 'text-primary bg-primary/10' },
            { step: '2', title: 'Upload Files',     desc: 'Add source references and documents to check (min 2 sources)', icon: FileText, color: 'text-violet-400 bg-violet-400/10' },
            { step: '3', title: 'Get Results',      desc: 'Submit for AI analysis and download a PDF plagiarism report', icon: Shield, color: 'text-emerald-400 bg-emerald-400/10' },
          ].map(s => (
            <Card key={s.step} className="p-5">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${s.color}`}><s.icon size={17}/></div>
              <p className="text-xs font-bold text-muted-foreground mb-1">Step {s.step}</p>
              <p className="font-semibold text-sm mb-1">{s.title}</p>
              <p className="text-xs text-muted-foreground">{s.desc}</p>
            </Card>
          ))}
        </div>
      </div>
      {/* Plan info — يوزر جديد يشوف 0 استهلاك */}
      <Card className="p-5 flex items-center gap-4">
        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
          <Shield size={18} className="text-primary"/>
        </div>
        <div className="flex-1">
          <p className="font-semibold text-sm">Your Plan: <span className="text-primary">{planName}</span></p>
          <p className="text-xs text-muted-foreground mt-0.5">
            {planLimit === null
              ? 'Loading plan info... '
              :planLimit === -1
                 ?'Unlimited checks per month'
                 : `${checksUsed} used · ${checksRemaining} remaining this month`}
          </p>
        </div>
        <button onClick={() => navigate('/profile')} className="text-xs text-primary hover:underline">View account</button>
      </Card>
    </div>
  )

  // ── RETURNING USER DASHBOARD ────────────────────────────────
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-bold">Welcome back, {user?.name?.split(' ')[0]} 👋</h2>
        <p className="text-sm text-muted-foreground mt-0.5">Here's your GPD.AI overview</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Workspaces',  value: workspaces.length, icon: FolderOpen, color: 'text-primary bg-primary/10' },
          { label: 'Checks Remaining',  value: checksRemaining,   icon: Shield,     color: 'text-violet-400 bg-violet-400/10' },
          { label: 'Avg. Score',        value: `${avgScore}%`,    icon: BarChart3,  color: 'text-emerald-400 bg-emerald-400/10' },
          { label: 'Reports Generated', value: totalSubs,         icon: FileText,   color: 'text-amber-400 bg-amber-400/10' },
        ].map(s => (
          <Card key={s.label} className="p-4">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${s.color}`}><s.icon size={18}/></div>
            <p className="text-2xl font-bold font-mono">{s.value}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
          </Card>
        ))}
      </div>
      <div className="grid lg:grid-cols-3 gap-5">
        <Card className="lg:col-span-2 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-sm">Recent Workspaces</h3>
            <button onClick={() => navigate('/workspaces')} className="text-xs text-primary hover:underline flex items-center gap-1">View all <ArrowRight size={12}/></button>
          </div>
          {workspaces.slice(0,4).map(w => (
            <div key={w.id} onClick={() => navigate(`/workspaces/${w.id}`)}
              className="flex items-center gap-3 p-3 rounded-lg cursor-pointer hover:bg-accent transition-colors">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <FolderOpen size={15} className="text-primary"/>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{w.name}</p>
                <p className="text-xs text-muted-foreground">{w.created_at} · {w.sources_count} sources</p>
              </div>
              <Badge variant={w.status === 'analyzed' ? 'success' : w.status === 'pending' ? 'warning' : 'default'}>{w.status}</Badge>
            </div>
          ))}
        </Card>
        <div className="space-y-4">
          <Card className="p-5">
            <h3 className="font-semibold text-sm mb-3">Quick Actions</h3>
            {[
              { label: 'New Workspace', icon: FolderOpen, to: '/workspaces' },
              { label: 'View History',  icon: BarChart3,  to: '/history' },
              { label: 'My Account',    icon: Settings,   to: '/profile' },
            ].map(a => (
              <button key={a.label} onClick={() => navigate(a.to)}
                className="flex items-center gap-3 w-full p-3 rounded-lg border border-border hover:border-primary/30 hover:bg-accent text-left transition-all mb-2 last:mb-0">
                <a.icon size={15} className="text-primary"/>
                <span className="text-sm font-medium">{a.label}</span>
              </button>
            ))}
          </Card>
          <Card className="p-5">
            <h3 className="font-semibold text-sm mb-3">Score Guide</h3>
            {[{label:'Low',range:'0–15%',c:'bg-emerald-500'},{label:'Medium',range:'15–30%',c:'bg-amber-500'},{label:'High',range:'30%+',c:'bg-destructive'}].map(l => (
              <div key={l.label} className="flex items-center gap-2 mb-2 last:mb-0">
                <div className={`w-2 h-2 rounded-full ${l.c}`}/><span className="text-xs">{l.label}</span>
                <span className="text-xs text-muted-foreground ml-auto font-mono">{l.range}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  )
}
