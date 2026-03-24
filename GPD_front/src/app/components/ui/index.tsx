import { cn } from '@/lib/utils'
import { type ReactNode, type InputHTMLAttributes, type ButtonHTMLAttributes } from 'react'
import { Sun, Moon, X, Check, AlertTriangle, Upload, Trash2, FileText, ChevronDown } from 'lucide-react'

// ── Button ──────────────────────────────────────────────────────────────────
type BtnVariant = 'default' | 'outline' | 'ghost' | 'destructive' | 'secondary'
type BtnSize = 'default' | 'sm' | 'lg' | 'icon'
interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: BtnVariant; size?: BtnSize; children?: ReactNode
}
export function Button({ variant = 'default', size = 'default', className, children, ...p }: BtnProps) {
  return (
    <button {...p} className={cn(
      'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:pointer-events-none',
      {
        'bg-primary text-primary-foreground hover:bg-primary/90 shadow': variant === 'default',
        'border border-border bg-background hover:bg-accent hover:text-accent-foreground': variant === 'outline',
        'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
        'bg-destructive text-destructive-foreground hover:bg-destructive/90': variant === 'destructive',
        'bg-secondary text-secondary-foreground hover:bg-secondary/80': variant === 'secondary',
        'h-9 px-4 py-2 text-sm': size === 'default',
        'h-8 px-3 text-xs': size === 'sm',
        'h-10 px-6 text-sm': size === 'lg',
        'h-9 w-9 p-0': size === 'icon',
      }, className
    )}>{children}</button>
  )
}

// ── Input ───────────────────────────────────────────────────────────────────
interface InputProps extends InputHTMLAttributes<HTMLInputElement> { label?: string; error?: string }
export function Input({ label, error, className, ...p }: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{label}</label>}
      <input {...p} className={cn(
        'flex h-9 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        error && 'border-destructive focus-visible:ring-destructive',
        className
      )} />
      {error && <p className="text-xs text-destructive flex items-center gap-1"><AlertTriangle size={11}/>{error}</p>}
    </div>
  )
}

// ── Card ────────────────────────────────────────────────────────────────────
export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn('rounded-xl border border-border bg-card shadow-sm', className)}>{children}</div>
}

// ── Badge ───────────────────────────────────────────────────────────────────
type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'admin'
export function Badge({ variant = 'default', children }: { variant?: BadgeVariant; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold', {
      'bg-secondary text-secondary-foreground': variant === 'default',
      'bg-emerald-500/15 text-emerald-500': variant === 'success',
      'bg-amber-500/15 text-amber-500': variant === 'warning',
      'bg-destructive/15 text-destructive': variant === 'danger',
      'bg-violet-500/15 text-violet-400': variant === 'admin',
    })}>{children}</span>
  )
}

// ── Modal ───────────────────────────────────────────────────────────────────
export function Modal({ isOpen, onClose, title, children }: { isOpen: boolean; onClose: () => void; title?: string; children: ReactNode }) {
  if (!isOpen) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card shadow-2xl animate-fade-in max-h-[85vh] overflow-y-auto">
        {title && (
          <div className="flex items-center justify-between p-5 border-b border-border sticky top-0 bg-card z-10">
            <h3 className="font-semibold text-foreground">{title}</h3>
            <button onClick={onClose} className="rounded-lg p-1.5 hover:bg-accent text-muted-foreground"><X size={16}/></button>
          </div>
        )}
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}

// ── ThemeToggle ─────────────────────────────────────────────────────────────
export function ThemeToggle({ theme, toggle }: { theme: string; toggle: () => void }) {
  return (
    <button onClick={toggle} className="rounded-lg p-2 hover:bg-accent text-muted-foreground transition-colors">
      {theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}
    </button>
  )
}

// ── ScoreRing ────────────────────────────────────────────────────────────────
export function ScoreRing({ score }: { score: number }) {
  const r = 52, c = 2 * Math.PI * r
  const filled = ((100 - score) / 100) * c
  const color = score < 15 ? '#22c55e' : score < 30 ? '#eab308' : '#ef4444'
  return (
    <div className="relative flex items-center justify-center">
      <svg width="130" height="130" className="-rotate-90">
        <circle cx="65" cy="65" r={r} fill="none" stroke="hsl(var(--secondary))" strokeWidth="10"/>
        <circle cx="65" cy="65" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={c} strokeDashoffset={c - filled} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 1s ease' }}/>
      </svg>
      <div className="absolute text-center">
        <p className="text-3xl font-bold font-mono" style={{ color }}>{score}%</p>
        <p className="text-xs text-muted-foreground">Plagiarism</p>
      </div>
    </div>
  )
}

// ── FileRow ──────────────────────────────────────────────────────────────────
export function FileRow({ name, size, ext, onDelete }: { name: string; size: string; ext: string; onDelete: () => void }) {
  return (
    <div className="flex items-center gap-3 p-2.5 rounded-lg border border-border bg-background group hover:border-primary/30 transition-colors">
      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
        <FileText size={14} className="text-primary"/>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{name}</p>
        <p className="text-xs text-muted-foreground">{ext} · {size}</p>
      </div>
      <button onClick={onDelete} className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-destructive/10 text-destructive">
        <Trash2 size={13}/>
      </button>
    </div>
  )
}

// ── DropZone ─────────────────────────────────────────────────────────────────
export function DropZone({ onFiles, label }: { onFiles: (files: File[]) => void; label?: string }) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) onFiles(Array.from(e.target.files))
  }
  return (
    <label className="flex flex-col items-center gap-2 p-4 rounded-xl border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-colors">
      <Upload size={20} className="text-muted-foreground"/>
      <span className="text-xs text-muted-foreground text-center">{label || 'Click or drag files here'}</span>
      <input type="file" multiple accept=".pdf,.docx,.doc,.txt" className="hidden" onChange={handleChange}/>
    </label>
  )
}

// ── Spinner ──────────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return <div className="rounded-full border-2 border-primary/20 border-t-primary animate-spin" style={{ width: size, height: size }}/>
}

// ── Alert ────────────────────────────────────────────────────────────────────
export function Alert({ variant = 'info', children }: { variant?: 'info' | 'success' | 'warning' | 'error'; children: ReactNode }) {
  const styles = {
    info:    'bg-primary/10 border-primary/30 text-primary',
    success: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-500',
    warning: 'bg-amber-500/10 border-amber-500/30 text-amber-500',
    error:   'bg-destructive/10 border-destructive/30 text-destructive',
  }
  const icons = { info: AlertTriangle, success: Check, warning: AlertTriangle, error: AlertTriangle }
  const Icon = icons[variant]
  return (
    <div className={cn('flex items-start gap-2.5 p-3 rounded-lg border text-sm', styles[variant])}>
      <Icon size={15} className="flex-shrink-0 mt-0.5"/>{children}
    </div>
  )
}
