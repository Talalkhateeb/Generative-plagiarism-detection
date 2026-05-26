/**
 * AuthContext connects to Django /api/auth/ endpoints.
 * Registration uses a 2-step OTP flow:
 *   1. sendOTP() emails the verification code
 *   2. verifyOTP() verifies the code and creates the account
 */
import { createContext, useContext, useEffect, useState } from 'react'
import type { User } from '@/types'
import { authAPI } from '@/services/api'

interface AuthCtx {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; message?: string }>
  sendOTP: (name: string, email: string, password: string, planId: number) => Promise<{ success: boolean; message?: string }>
  verifyOTP: (name: string, email: string, password: string, planId: number, code: string) => Promise<{ success: boolean; message?: string }>
  resendOTP: (name: string, email: string, password: string, planId: number) => Promise<{ success: boolean; message?: string }>
  updateProfile: (updates: Partial<User>) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx)

const USER_KEY = 'GPDetect_user'
const LEGACY_USER_KEY = 'GPD_user'

const saveUser = (user: User) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  localStorage.removeItem(LEGACY_USER_KEY)
}
const clearAuth = () => {
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(LEGACY_USER_KEY)
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

const parseUser = (data: any): User => ({
  id: data.user.id,
  name: data.user.name,
  email: data.user.email,
  role: data.user.role,
  plan: data.user.plan,
  status: data.user.status,
  date_joined: data.user.date_joined,
})

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem(USER_KEY) ?? localStorage.getItem(LEGACY_USER_KEY)
    const token = localStorage.getItem('access_token')
    if (stored && token) {
      try {
        const nextUser = JSON.parse(stored)
        setUser(nextUser)
        localStorage.setItem(USER_KEY, stored)
        localStorage.removeItem(LEGACY_USER_KEY)
      } catch (_) {}
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const { data } = await authAPI.login(email, password)
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const nextUser = parseUser(data)
      saveUser(nextUser)
      setUser(nextUser)
      return { success: true }
    } catch (apiErr: any) {
      const msg =
        apiErr.response?.data?.detail ||
        apiErr.response?.data?.non_field_errors?.[0] ||
        'Invalid email or password'
      return { success: false, message: msg }
    }
  }

  const sendOTP = async (name: string, email: string, password: string, planId: number) => {
    try {
      await authAPI.sendOTP(name, email, password, password, planId)
      return { success: true }
    } catch (apiErr: any) {
      const errors = apiErr.response?.data
      const msg =
        errors?.email?.[0] ||
        errors?.password?.[0] ||
        errors?.plan_id?.[0] ||
        errors?.detail ||
        errors?.non_field_errors?.[0] ||
        'Failed to send verification code'
      return { success: false, message: msg }
    }
  }

  const verifyOTP = async (name: string, email: string, password: string, planId: number, code: string) => {
    try {
      const { data } = await authAPI.verifyOTP(name, email, password, planId, code)
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const nextUser = parseUser(data)
      saveUser(nextUser)
      setUser(nextUser)
      return { success: true }
    } catch (apiErr: any) {
      const errors = apiErr.response?.data
      const msg =
        errors?.otp_code?.[0] ||
        errors?.non_field_errors?.[0] ||
        errors?.detail ||
        'Invalid or expired code'
      return { success: false, message: msg }
    }
  }

  const resendOTP = async (name: string, email: string, password: string, planId: number) => {
    try {
      await authAPI.resendOTP(name, email, password, planId)
      return { success: true }
    } catch (_apiErr: any) {
      return { success: false, message: 'Failed to resend code' }
    }
  }

  const updateProfile = async (updates: Partial<User>) => {
    try {
      await authAPI.updateMe({ name: updates.name, email: updates.email })
    } catch (_) {}
    if (!user) return
    const updated = { ...user, ...updates }
    saveUser(updated)
    setUser(updated)
  }

  const logout = () => {
    const refresh = localStorage.getItem('refresh_token')
    if (refresh) authAPI.logout(refresh).catch(() => {})
    clearAuth()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, sendOTP, verifyOTP, resendOTP, updateProfile, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
