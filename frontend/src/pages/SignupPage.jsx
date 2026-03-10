import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Cpu, Eye, EyeOff } from 'lucide-react'
import FormInput from '../components/FormInput'
import Button from '../components/Button'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/api'

const DEMO_USER = { name: 'Demo Developer', email: 'demo@intelli-ci.dev', role: 'Developer', createdAt: '2026-01-01' }
const DEMO_TOKEN = 'demo-token'

export default function SignupPage() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState('')

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Full name is required'
    if (!form.email.trim()) errs.email = 'Email is required'
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Enter a valid email'
    if (!form.password) errs.password = 'Password is required'
    else if (form.password.length < 8) errs.password = 'Password must be at least 8 characters'
    if (form.password !== form.confirm) errs.confirm = 'Passwords do not match'
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
      const { data } = await authService.signup(form.name, form.email, form.password)
      login(data.user, data.token)
      navigate('/dashboard')
    } catch (err) {
      if (err.code === 'ERR_NETWORK' || err.response?.status === 404) {
        const newUser = { name: form.name, email: form.email, role: 'Developer', createdAt: new Date().toISOString() }
        login(newUser, DEMO_TOKEN)
        navigate('/dashboard')
      } else {
        setServerError(err.response?.data?.detail || 'Signup failed. Please try again.')
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
        <h1 className="text-2xl font-bold tracking-tight text-center" style={{ color: 'var(--color-text-primary)' }}>
          Create account
        </h1>
        <p className="text-sm mt-1.5 text-center" style={{ color: 'var(--color-text-secondary)' }}>
          Join INTELLI-CI today
        </p>
      </div>

      {/* Card */}
      <div className="panel shadow-xl">
        {serverError && (
          <div
            className="flex items-start gap-2 border-b px-5 py-3 text-sm"
            style={{ background: '#2d1b1b', borderColor: '#6e2020', color: 'var(--color-error)' }}
          >
            {serverError}
          </div>
        )}

        <div className="p-8 sm:p-10">
        <form onSubmit={handleSubmit} className="flex flex-col gap-6">
          <FormInput
            id="name"
            label="Full Name"
            placeholder="Jane Doe"
            value={form.name}
            onChange={set('name')}
            error={errors.name}
            autoComplete="name"
          />
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

          {/* Password */}
          <div className="flex flex-col gap-2">
            <label htmlFor="password" className="text-sm font-medium" style={{ color: '#E6EDF3' }}>Password</label>
            <div className="relative">
              <input
                id="password"
                type={showPw ? 'text' : 'password'}
                placeholder="Min. 8 characters"
                value={form.password}
                onChange={set('password')}
                autoComplete="new-password"
                className="w-full px-4 py-3 pr-12 rounded-lg border text-sm outline-none transition-colors focus:border-[#388bfd]"
                style={{ background: '#0D1117', borderColor: errors.password ? '#f85149' : '#30363D', color: '#E6EDF3', minHeight: '48px' }}
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

          <FormInput
            id="confirm"
            label="Confirm Password"
            type="password"
            placeholder="Repeat password"
            value={form.confirm}
            onChange={set('confirm')}
            error={errors.confirm}
            autoComplete="new-password"
          />

          <Button type="submit" variant="primary" fullWidth loading={loading}>
            Create Account
          </Button>
        </form>
        </div>
      </div>

      <p className="text-center text-sm mt-5" style={{ color: '#8B949E' }}>
        Already have an account?{' '}
        <Link to="/login" className="hover:underline" style={{ color: '#388bfd' }}>
          Sign in
        </Link>
      </p>
    </div>
  )
}
