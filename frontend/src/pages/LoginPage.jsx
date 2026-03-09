import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Cpu, Eye, EyeOff } from 'lucide-react'
import FormInput from '../components/FormInput'
import Button from '../components/Button'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/api'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const validate = () => {
    const errs = {}
    if (!form.email.trim()) errs.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Enter a valid email'
    if (!form.password) errs.password = 'Password is required'
    return errs
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setServerError('')
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    setLoading(true)
    try {
      const { data } = await authService.login(form.email, form.password)
      login(data.user, data.token)
      navigate('/dashboard')
    } catch (err) {
      if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
        setServerError(
          `Cannot connect to API. Ensure the backend is running at ${API_BASE}. ` +
          'Run: cd backend && uvicorn backend.main:app --reload --port 8000'
        )
      } else {
        setServerError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full fade-in">
      {/* Logo */}
      <div className="flex flex-col items-center mb-8">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
          style={{ background: '#0d2615', border: '1px solid #2ea04326' }}
        >
          <Cpu size={22} style={{ color: 'var(--color-success)' }} strokeWidth={1.5} />
        </div>
        <h1 className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
          Sign in
        </h1>
        <p className="text-sm mt-1.5" style={{ color: 'var(--color-text-secondary)' }}>
          to your INTELLI-CI account
        </p>
      </div>

      {/* Card */}
      <div className="panel shadow-2xl">
        {serverError && (
          <div
            className="flex items-start gap-2 border-b px-5 py-3 text-sm"
            style={{ background: '#2d1b1b', borderColor: '#6e2020', color: 'var(--color-error)' }}
          >
            {serverError}
          </div>
        )}

        <div className="p-7 sm:p-8">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <FormInput
            id="email"
            label="Email address"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={set('email')}
            error={errors.email}
            autoComplete="email"
          />

          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-sm font-medium" style={{ color: '#E6EDF3' }}>
                Password
              </label>
              <button type="button" className="text-xs hover:underline" style={{ color: '#388bfd' }}>
                Forgot password?
              </button>
            </div>
            <div className="relative min-h-[46px]">
              <input
                id="password"
                type={showPw ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={set('password')}
                autoComplete="current-password"
                className="w-full px-4 py-2.5 pr-12 rounded-lg border text-sm outline-none transition-colors focus:border-[#388bfd]"
                style={{
                  background: '#0D1117',
                  borderColor: errors.password ? '#f85149' : '#30363D',
                  color: '#E6EDF3',
                  minHeight: '46px',
                }}
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2"
                style={{ color: '#8B949E' }}
              >
                {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            {errors.password && <p className="text-xs" style={{ color: '#f85149' }}>{errors.password}</p>}
          </div>

          <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: '#8B949E' }}>
            <input type="checkbox" className="accent-[#238636]" />
            Remember me
          </label>

          <Button type="submit" variant="primary" fullWidth loading={loading}>
            Sign in
          </Button>
        </form>
        </div>
      </div>

      <p className="text-center text-sm mt-5" style={{ color: '#8B949E' }}>
        Don't have an account?{' '}
        <Link to="/signup" className="hover:underline" style={{ color: '#388bfd' }}>
          Create one
        </Link>
      </p>
    </div>
  )
}
