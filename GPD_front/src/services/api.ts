/**
 * Veritas.AI — API Service
 */
import axios, { type AxiosError } from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
})

// ── Attach JWT token ──────────────────────────────────────────────────────────
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('access_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}` 
  return cfg
})

// ── Auto-refresh on 401 ───────────────────────────────────────────────────────
api.interceptors.response.use(
  r => r,
  async (err: AxiosError) => {
    const original = err.config as any
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post(
            `${api.defaults.baseURL}/auth/token/refresh/`,
            { refresh }
          )
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch (_) {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/auth/login/', { email, password }),

  // Step 1: validate form + send OTP email
  sendOTP: (name: string, email: string, password: string, confirm_password: string, plan_id: number) =>
    api.post('/auth/register/send-otp/', { name, email, password, confirm_password, plan_id }),

  // Step 2: verify OTP and create account (returns tokens)
  verifyOTP: (name: string, email: string, password: string, plan_id: number, otp_code: string) =>
    api.post('/auth/register/verify-otp/', { name, email, password, plan_id, otp_code }),

  // Resend a fresh OTP
  resendOTP: (name: string, email: string, password: string, plan_id: number) =>
    api.post('/auth/register/resend-otp/', { name, email, password, confirm_password: password, plan_id }),

  logout:         (refresh: string) => api.post('/auth/logout/', { refresh }),
  me:             () => api.get('/auth/me/'),
  updateMe:       (data: { name?: string; email?: string }) => api.patch('/auth/me/', data),
  changePassword: (data: { current_password: string; new_password: string; confirm_password: string }) =>
    api.post('/auth/change-password/', data),
}

// ── Plans ─────────────────────────────────────────────────────────────────────
export const plansAPI = {
  list:   () => api.get('/plans/'),
  create: (data: object) => api.post('/plans/', data),
  update: (id: number, data: object) => api.patch(`/plans/${id}/`, data),
  delete: (id: number) => api.delete(`/plans/${id}/`),
}

// ── Workspaces ────────────────────────────────────────────────────────────────
export const workspacesAPI = {
  list:   () => api.get('/workspaces/'),
  create: (name: string) => api.post('/workspaces/', { name }),
  get:    (id: number) => api.get(`/workspaces/${id}/`),
  rename: (id: number, name: string) => api.patch(`/workspaces/${id}/`, { name }),
  delete: (id: number) => api.delete(`/workspaces/${id}/`),

  listSources:   (id: number) => api.get(`/workspaces/${id}/sources/`),
  uploadSource:  (id: number, file: File) => {
    const form = new FormData(); form.append('file', file)
    return api.post(`/workspaces/${id}/sources/`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  deleteSource:  (wsId: number, srcId: string | number) =>
    api.delete(`/workspaces/${wsId}/sources/${srcId}/`),

  listDocuments:  (id: number) => api.get(`/workspaces/${id}/documents/`),
  uploadDocument: (id: number, file: File) => {
    const form = new FormData(); form.append('file', file)
    return api.post(`/workspaces/${id}/documents/`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  deleteDocument: (wsId: number, docId: string | number) =>
    api.delete(`/workspaces/${wsId}/documents/${docId}/`),

  submit:  (id: number, sourceIds: number[], documentIds: number[]) =>
    api.post(`/workspaces/${id}/submit/`, { source_ids: sourceIds, document_ids: documentIds }),
  results: (id: number) => api.get(`/workspaces/${id}/results/`),
  report:  (id: number) => api.get(`/workspaces/${id}/report/`),
}

// ── Submissions ───────────────────────────────────────────────────────────────
export const submissionsAPI = {
  history: () => api.get('/submissions/history/'),
}

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminAPI = {
  listAccounts:  () => api.get('/admin/accounts/'),
  getAccount:    (id: number) => api.get(`/admin/accounts/${id}/`),
  updateStatus:  (id: number, status: 'active' | 'inactive') =>
    api.patch(`/admin/accounts/${id}/`, { status }),
}

export default api
