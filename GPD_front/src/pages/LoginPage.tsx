import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Mail, ArrowLeft, RefreshCw } from 'lucide-react'
import { useAuth } from '@/app/context/AuthContext'
import { useTheme } from '@/app/context/ThemeContext'
import { Button, Input, ThemeToggle, Alert } from '@/app/components/ui'
import { plansAPI } from '@/services/api'

// Register flow: step 1 = form, step 2 = plan select, step 3 = OTP verify
type RegStep = 1 | 2 | 3

export default function LoginPage() {
  const { login, sendOTP, verifyOTP, resendOTP } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()

  const [mode,    setMode]    = useState<'login' | 'register'>('login')
  const [regStep, setRegStep] = useState<RegStep>(1)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')
  const [success, setSuccess] = useState('')
  const [plans,   setPlans]   = useState<any[]>([])

  // Form fields
  const [form, setForm] = useState({
    name: '', email: '', password: '', confirmPassword: '', planId: 0,
  })
  const f = (k: string, v: any) => { setForm(p => ({ ...p, [k]: v })); setError('') }

  // OTP input — 6 individual boxes
  const [otp,     setOtp]     = useState(['', '', '', '', '', ''])
  const [resendIn, setResendIn] = useState(0)   // countdown seconds
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    plansAPI.list()
      .then(res => setPlans(res.data.results ?? res.data))
      .catch(() => setPlans([]))
  }, [])

  // Resend countdown
  useEffect(() => {
    if (resendIn <= 0) return
    timerRef.current = setInterval(() => {
      setResendIn(n => { if (n <= 1) { clearInterval(timerRef.current!); return 0 } return n - 1 })
    }, 1000)
    return () => clearInterval(timerRef.current!)
  }, [resendIn])

  const resetRegister = () => {
    setRegStep(1); setOtp(['', '', '', '', '', ''])
    setError(''); setSuccess('')
  }

  // ── Login ──────────────────────────────────────────────────────────────────
  const handleLogin = async () => {
    if (!form.email || !form.password) { setError('Please fill in all fields'); return }
    setLoading(true)
    const res = await login(form.email, form.password)
    setLoading(false)
    if (res.success) navigate('/', { replace: true })
    else setError(res.message || 'Login failed')
  }

  // ── Register step 1 → 2 (validate form) ───────────────────────────────────
  const handleRegStep1 = () => {
    if (!form.name.trim())                          { setError('Name is required'); return }
    if (!form.email || !/\S+@\S+\.\S+/.test(form.email)) { setError('Valid email required'); return }
    if (form.password.length < 6)                   { setError('Password must be at least 6 characters'); return }
    if (form.password !== form.confirmPassword)     { setError('Passwords do not match'); return }
    setError(''); setRegStep(2)
  }

  // ── Register step 2 → 3 (select plan, send OTP) ───────────────────────────
  const handleSendOTP = async () => {
    if (!form.planId) { setError('Please select a subscription plan'); return }
    setLoading(true); setError('')
    const res = await sendOTP(form.name, form.email, form.password, form.planId)
    setLoading(false)
    if (res.success) {
      setRegStep(3)
      setOtp(['', '', '', '', '', ''])
      setResendIn(60)
      setSuccess(`Verification code sent to ${form.email}`)
      setTimeout(() => otpRefs.current[0]?.focus(), 100)
    } else {
      setError(res.message || 'Failed to send code')
    }
  }

  // ── OTP input handlers ─────────────────────────────────────────────────────
  const handleOtpChange = (i: number, val: string) => {
    if (!/^\d?$/.test(val)) return
    const next = [...otp]; next[i] = val; setOtp(next)
    setError('')
    if (val && i < 5) otpRefs.current[i + 1]?.focus()
  }

  const handleOtpKeyDown = (i: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) otpRefs.current[i - 1]?.focus()
  }

  const handleOtpPaste = (e: React.ClipboardEvent) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length === 6) {
      setOtp(pasted.split(''))
      otpRefs.current[5]?.focus()
    }
  }

  // ── Register step 3: verify OTP ───────────────────────────────────────────
  const handleVerifyOTP = async () => {
    const code = otp.join('')
    if (code.length < 6) { setError('Please enter the full 6-digit code'); return }
    setLoading(true); setError('')
    const res = await verifyOTP(form.name, form.email, form.password, form.planId, code)
    setLoading(false)
    if (res.success) navigate('/', { replace: true })
    else setError(res.message || 'Invalid verification code')
  }

  // ── Resend OTP ─────────────────────────────────────────────────────────────
  const handleResend = async () => {
    if (resendIn > 0) return
    setLoading(true); setError('')
    const res = await resendOTP(form.name, form.email, form.password, form.planId)
    setLoading(false)
    if (res.success) {
      setOtp(['', '', '', '', '', ''])
      setResendIn(60)
      setSuccess('New verification code sent!')
      setTimeout(() => otpRefs.current[0]?.focus(), 100)
    } else {
      setError(res.message || 'Failed to resend code')
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background relative overflow-hidden">
      {/* Background blobs */}
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute top-1/3 left-1/4 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl"/>
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-500/5 rounded-full blur-3xl"/>
      </div>

      <button onClick={toggleTheme} className="fixed top-4 right-4 rounded-lg p-2 hover:bg-accent text-muted-foreground">
        <ThemeToggle theme={theme} toggle={toggleTheme}/>
      </button>

      <div className="relative w-full max-w-sm animate-slide-up">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 mb-4">
            <Shield size={26} className="text-primary"/>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">VERITAS<span className="text-primary">.AI</span></h1>
          <p className="text-sm text-muted-foreground mt-1">Academic Integrity Platform</p>
        </div>

        {/* Tab switcher — hide during OTP step */}
        {!(mode === 'register' && regStep === 3) && (
          <div className="flex rounded-xl p-1 mb-5 bg-secondary">
            {[{ id: 'login', label: 'Log In' }, { id: 'register', label: 'Sign Up' }].map(t => (
              <button key={t.id}
                onClick={() => { setMode(t.id as any); resetRegister(); setError('') }}
                className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                  mode === t.id ? 'bg-primary text-primary-foreground shadow' : 'text-muted-foreground hover:text-foreground'
                }`}>
                {t.label}
              </button>
            ))}
          </div>
        )}

        <div className="space-y-4">
          {error   && <Alert variant="error">{error}</Alert>}
          {success && <Alert variant="success">{success}</Alert>}

          {/* ── LOGIN ─────────────────────────────────────────────────── */}
          {mode === 'login' && (
            <>
              <Input label="Email" type="email" value={form.email}
                onChange={e => f('email', e.target.value)} placeholder="you@example.com" autoFocus/>
              <Input label="Password" type="password" value={form.password}
                onChange={e => f('password', e.target.value)} placeholder="••••••••"
                onKeyDown={e => e.key === 'Enter' && handleLogin()}/>
              <Button className="w-full" onClick={handleLogin} disabled={loading}>
                {loading ? 'Logging in…' : 'Log In'}
              </Button>
            </>
          )}

          {/* ── REGISTER STEP 1 — personal info ────────────────────────── */}
          {mode === 'register' && regStep === 1 && (
            <>
              <Input label="Full Name" value={form.name}
                onChange={e => f('name', e.target.value)} placeholder="Your name" autoFocus/>
              <Input label="Email" type="email" value={form.email}
                onChange={e => f('email', e.target.value)} placeholder="you@example.com"/>
              <Input label="Password" type="password" value={form.password}
                onChange={e => f('password', e.target.value)} placeholder="Min 6 characters"/>
              <Input label="Confirm Password" type="password" value={form.confirmPassword}
                onChange={e => f('confirmPassword', e.target.value)} placeholder="Repeat password"
                onKeyDown={e => e.key === 'Enter' && handleRegStep1()}/>
              <Button className="w-full" onClick={handleRegStep1}>Continue →</Button>
            </>
          )}

          {/* ── REGISTER STEP 2 — plan selection ───────────────────────── */}
          {mode === 'register' && regStep === 2 && (
            <>
              <p className="text-sm text-muted-foreground -mt-1">Choose a plan for your account</p>
              <div className="space-y-2">
                {plans.length === 0
                  ? <p className="text-xs text-muted-foreground text-center py-4">Loading plans…</p>
                  : plans.map((p: any) => (
                    <button key={p.id}
                      onClick={() => f('planId', p.id)}
                      className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                        form.planId === p.id
                          ? 'border-primary bg-primary/10 shadow-sm'
                          : 'border-border hover:border-primary/40 bg-secondary/50'
                      }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-sm">{p.name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {p.checks_per_month === -1 ? 'Unlimited' : `${p.checks_per_month} checks`} / month
                          </p>
                        </div>
                        {form.planId === p.id && (
                          <div className="w-4 h-4 rounded-full bg-primary flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-white"/>
                          </div>
                        )}
                      </div>
                    </button>
                  ))
                }
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1"
                  onClick={() => { setRegStep(1); setError('') }}>
                  <ArrowLeft size={14}/> Back
                </Button>
                <Button className="flex-1" onClick={handleSendOTP} disabled={loading}>
                  {loading ? 'Sending code…' : 'Send Verification Code'}
                </Button>
              </div>
            </>
          )}

          {/* ── REGISTER STEP 3 — OTP verification ─────────────────────── */}
          {mode === 'register' && regStep === 3 && (
            <>
              {/* Header */}
              <div className="text-center space-y-2 mb-2">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-primary/10 border border-primary/20">
                  <Mail size={22} className="text-primary"/>
                </div>
                <h2 className="font-bold text-lg">Check your email</h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  We sent a 6-digit code to<br/>
                  <span className="font-semibold text-foreground">{form.email}</span>
                </p>
              </div>

              {/* OTP boxes */}
              <div className="flex gap-2 justify-center my-4" onPaste={handleOtpPaste}>
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    ref={el => { otpRefs.current[i] = el }}
                    type="text" inputMode="numeric" maxLength={1}
                    value={digit}
                    onChange={e => handleOtpChange(i, e.target.value)}
                    onKeyDown={e => handleOtpKeyDown(i, e)}
                    className={`w-11 h-13 text-center text-xl font-bold rounded-xl border-2 bg-secondary transition-all outline-none
                      ${digit ? 'border-primary text-primary' : 'border-border'}
                      focus:border-primary focus:ring-2 focus:ring-primary/20`}
                    style={{ height: '3.2rem' }}
                  />
                ))}
              </div>

              <Button className="w-full" onClick={handleVerifyOTP} disabled={loading}>
                {loading ? 'Verifying…' : 'Verify & Create Account'}
              </Button>

              {/* Resend + back */}
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                <button onClick={() => { resetRegister(); setError('') }}
                  className="flex items-center gap-1 hover:text-foreground transition-colors">
                  <ArrowLeft size={12}/> Change email
                </button>
                <button
                  onClick={handleResend}
                  disabled={resendIn > 0 || loading}
                  className={`flex items-center gap-1 transition-colors ${
                    resendIn > 0 ? 'opacity-50 cursor-not-allowed' : 'hover:text-foreground cursor-pointer'
                  }`}>
                  <RefreshCw size={12}/>
                  {resendIn > 0 ? `Resend in ${resendIn}s` : 'Resend code'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
