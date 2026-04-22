/**
 * AuthContext — connects to Django /api/auth/ endpoints.
 * Registration is now a 2-step OTP flow:
 *   step 1: sendOTP()   → backend validates & emails OTP
 *   step 2: verifyOTP() → backend checks code, creates account, returns tokens
 */
import { createContext, useContext, useState, useEffect } from 'react'
import type { User } from '@/types'
import { authAPI } from '@/services/api'

interface AuthCtx {
  user: User | null
  loading: boolean
  login:      (email: string, password: string) => Promise<{ success: boolean; message?: string }>
  sendOTP:    (name: string, email: string, password: string, planId: number) => Promise<{ success: boolean; message?: string }>
  verifyOTP:  (name: string, email: string, password: string, planId: number, code: string) => Promise<{ success: boolean; message?: string }>
  resendOTP:  (name: string, email: string, password: string, planId: number) => Promise<{ success: boolean; message?: string }>
  updateProfile: (updates: Partial<User>) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx)

const saveUser  = (user: User) => localStorage.setItem('GPD_user', JSON.stringify(user))
const clearAuth = () => {
  localStorage.removeItem('GPD_user')
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

const parseUser = (data: any): User => ({
  id:          data.user.id,
  name:        data.user.name,
  email:       data.user.email,
  role:        data.user.role,
  plan:        data.user.plan,
  status:      data.user.status,
  date_joined: data.user.date_joined,
})

export const AuthProvider = ({ children }: { children: React.ReactNode }) =>  {
  const [user, setUser]       = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('GPD_user')
    const token  = localStorage.getItem('access_token')
    if (stored && token) {
      try { setUser(JSON.parse(stored)) } catch (_) {}
    }
    setLoading(false)
  }, [])

  // ── Login ──────────────────────────────────────────────────────────────────
  const login = async (email: string, password: string) => {
    try {
      const { data } = await authAPI.login(email, password)
      localStorage.setItem('access_token',  data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const u = parseUser(data)
      saveUser(u); setUser(u)
      return { success: true }
    } catch (apiErr: any) {
     const msg = apiErr.response?.data?.detail
        || apiErr.response?.data?.non_field_errors?.[0]
        || 'Invalid email or password'
      return { success: false, message: msg } 
      }
    }
  

  // ── OTP Step 1: send code ──────────────────────────────────────────────────
  const sendOTP = async (name: string, email: string, password: string, planId: number) => {
    try {
      await authAPI.sendOTP(name, email, password, password, planId)
      return { success: true }
    } catch (apiErr: any) {
      const errors = apiErr.response?.data
      const msg = errors?.email?.[0]
        || errors?.password?.[0]
        || errors?.plan_id?.[0]
        || errors?.detail
        || errors?.non_field_errors?.[0]
        || 'Failed to send verification code'
      return { success: false, message: msg }
    }
  }

  // ── OTP Step 2: verify code + create account ───────────────────────────────
  const verifyOTP = async (name: string, email: string, password: string, planId: number, code: string) => {
    try {
      const { data } = await authAPI.verifyOTP(name, email, password, planId, code)
      localStorage.setItem('access_token',  data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const u = parseUser(data)
      saveUser(u); setUser(u)
      return { success: true }
    } catch (apiErr: any) {
      const errors = apiErr.response?.data
      const msg = errors?.otp_code?.[0]
        || errors?.non_field_errors?.[0]
        || errors?.detail
        || 'Invalid or expired code'
      return { success: false, message: msg }
    }
  }

  // ── OTP Resend ─────────────────────────────────────────────────────────────
  const resendOTP = async (name: string, email: string, password: string, planId: number) => {
    try {
      await authAPI.resendOTP(name, email, password, planId)
      return { success: true }
    } catch (apiErr: any) {
      return { success: false, message: 'Failed to resend code' }
    }
  }

  // ── Profile update ─────────────────────────────────────────────────────────
  const updateProfile = async (updates: Partial<User>) => {
    try {
      await authAPI.updateMe({ name: updates.name, email: updates.email })
    } catch (_) {}
    if (!user) return
    const updated = { ...user, ...updates }
    saveUser(updated); setUser(updated)
  }

  // ── Logout ─────────────────────────────────────────────────────────────────
  const logout = () => {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) authAPI.logout(refresh).catch(() => {})
    clearAuth(); setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, sendOTP, verifyOTP, resendOTP, updateProfile, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
