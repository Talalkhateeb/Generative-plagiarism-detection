import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { LayoutDashboard, FolderOpen, History, User, Shield, Users, Menu, X, LogOut } from 'lucide-react'
import { useAuth } from '@/app/context/AuthContext'
import { useTheme } from '@/app/context/ThemeContext'
import { ThemeToggle } from '@/app/components/ui'
import { cn } from '@/lib/utils'

const USER_NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/workspaces', label: 'Workspaces', icon: FolderOpen },
  { to: '/history', label: 'History', icon: History },
  { to: '/profile', label: 'My Account', icon: User },
]
const ADMIN_NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/plans', label: 'Plans', icon: Shield },
  { to: '/admin/accounts', label: 'Accounts', icon: Users },
  { to: '/profile', label: 'My Account', icon: User },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const nav = user?.role === 'admin' ? ADMIN_NAV : USER_NAV

  const handleLogout = () => { logout(); navigate('/login', { replace: true }) }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Topbar */}
      <header className="fixed top-0 left-0 right-0 z-40 h-14 border-b border-border bg-card/80 backdrop-blur-md flex items-center px-4 gap-4">
        <button className="lg:hidden rounded-lg p-1.5 hover:bg-accent" onClick={() => setOpen(o => !o)}>
          {open ? <X size={18}/> : <Menu size={18}/>}
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
            <Shield size={14} className="text-primary"/>
          </div>
          <span className="font-bold tracking-tight text-sm">VERITAS<span className="text-primary">.AI</span></span>
        </div>
        <div className="flex-1"/>
        <ThemeToggle theme={theme} toggle={toggleTheme}/>
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
            {user?.name?.charAt(0)}
          </div>
          <div className="hidden sm:block">
            <p className="text-xs font-medium leading-none">{user?.name?.split(' ')[0]}</p>
            <p className="text-xs text-muted-foreground">{user?.role}</p>
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-14">
        {/* Sidebar */}
        {open && <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setOpen(false)}/>}
        <aside className={cn(
          'fixed top-14 left-0 bottom-0 z-30 w-56 border-r border-border bg-sidebar flex flex-col transition-transform duration-300',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}>
          <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
            {nav.map(item => (
              <NavLink key={item.to} to={item.to} end={item.end}
                onClick={() => setOpen(false)}
                className={({ isActive }) => cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary/10 text-primary border border-primary/20'
                    : 'text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent'
                )}>
                <item.icon size={16}/>
                {item.label}
              </NavLink>
            ))}
          </nav>

          {/* User plan */}
          {user?.role !== 'admin' && user?.plan && (
            <div className="p-3 border-t border-sidebar-border">
              <div className="p-3 rounded-xl bg-sidebar-accent">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-semibold text-foreground">{user.plan} Plan</span>
                  <span className="text-xs text-primary font-mono capitalize">{user.status}</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Active subscription</p>
              </div>
            </div>
          )}
          <div className="p-3 border-t border-sidebar-border">
            <button onClick={handleLogout} className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors">
              <LogOut size={15}/> Sign Out
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 lg:ml-56 p-6 overflow-x-hidden">
          <Outlet/>
        </main>
      </div>
    </div>
  )
}
