import axios from 'axios'

// FastAPI backend — override with VITE_API_URL in .env.local for production
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ici_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redirect to /login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ici_token')
      localStorage.removeItem('ici_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

/** Extract user-friendly error message from API error response */
export function getErrorMessage(err, fallback = 'An error occurred. Please try again.') {
  const detail = err.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    const msg = first?.msg || first?.message
    const loc = first?.loc?.filter(Boolean)?.join('.')
    return loc ? `${loc}: ${msg}` : msg || fallback
  }
  return fallback
}

// ── Auth ── POST /login  POST /signup ─────────────────────────────────────────
export const authService = {
  login:  (email, password)        => api.post('/login',  { email, password }),
  signup: (name, email, password)  => api.post('/signup', { name, email, password }),
}

// ── Predictions ── POST /predict ──────────────────────────────────────────────
export const predictService = {
  predict: (payload) => api.post('/predict', payload),
}

// ── Commit history ── GET /commits ────────────────────────────────────────────
export const commitService = {
  getCommits: (params) => api.get('/commits', { params }),
}

// ── Analytics ── GET /analytics/summary  GET /analytics/timeline ────────────
export const analyticsService = {
  getSummary: ()           => api.get('/analytics/summary'),
  getTimeline: (days = 30) => api.get('/analytics/timeline', { params: { days } }),
}

// ── Repositories ── GET /repositories  POST /connect-repository  DELETE /repositories/:id ──
export const repositoryService = {
  list:    ()        => api.get('/repositories'),
  connect: (payload) => api.post('/connect-repository', payload),
  delete:  (id)      => api.delete(`/repositories/${id}`),
}

// ── Profile ── GET /profile  PUT /profile  PUT /profile/password ──────────────
export const profileService = {
  get:            ()                               => api.get('/profile'),
  update:         (name)                           => api.put('/profile', { name }),
  changePassword: (current_password, new_password) =>
    api.put('/profile/password', { current_password, new_password }),
}

// ── Log analyzer ── POST /analyze-logs  POST /fix-error ───────────────────────
export const logService = {
  analyzeLogs: (log_text) => api.post('/analyze-logs', { log_text }),
  fixError:    (log_text) => api.post('/fix-error',    { log_text }),
}

// ── System health ── GET /system-health ───────────────────────────────────────
export const systemService = {
  health: () => api.get('/system-health'),
}

export default api
