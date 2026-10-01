import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/api';
import { saveUser } from '../services/localData';
import { useState } from 'react';
import { Eye, EyeOff, Loader2, GitBranch } from 'lucide-react';

const ROLES = [
  { value: 'student',          label: 'Student' },
  { value: 'developer',        label: 'Developer' },
  { value: 'software_engineer',label: 'Software Engineer' },
  { value: 'devops_engineer',  label: 'DevOps Engineer' },
  { value: 'team_lead',        label: 'Team Lead' },
  { value: 'project_manager',  label: 'Project Manager' },
  { value: 'researcher',       label: 'Researcher' },
  { value: 'other',            label: 'Other' },
];

const inputCls =
  'w-full bg-githubBg border border-githubBorder rounded-lg px-4 py-3 text-white placeholder-githubTextSecondary focus:border-githubPrimary focus:outline-none transition-colors text-sm';

export default function Signup() {
  const navigate = useNavigate();
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [showPwd, setShowPwd]   = useState(false);
  const [showCPwd, setShowCPwd] = useState(false);

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    const fd = new FormData(e.currentTarget);
    const name             = fd.get('name')?.trim();
    const email            = fd.get('email')?.trim();
    const password         = fd.get('password');
    const confirmPassword  = fd.get('confirmPassword');
    const profession       = fd.get('profession');
    const organization_name= fd.get('organization_name')?.trim() || null;

    // --- Frontend validation ---
    if (!name)            return setError('Full name is required.');
    if (name.length > 255) return setError('Name is too long.');
    if (!email)           return setError('Email is required.');
    if (!profession)      return setError('Please select your role.');
    if (password.length < 8) return setError('Password must be at least 8 characters.');
    if (password !== confirmPassword) return setError('Passwords do not match.');

    try {
      setLoading(true);

      // 1. Register
      await authService.signup({ name, email, password, profession, organization_name });

      // 2. Auto-login to get JWT
      const loginRes = await authService.login({ email, password });
      const token    = loginRes.data?.data?.access_token || loginRes.data?.access_token;
      if (!token) throw new Error('Login after signup failed.');
      localStorage.setItem('intelli_ci_token', token);

      // 3. Fetch profile
      const meRes = await authService.getMe();
      const user  = meRes.data?.data || meRes.data;
      if (user) saveUser(user, token);

      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map(d => d.msg).join(' · '));
      } else {
        setError(detail || err.message || 'Signup failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-githubBg flex items-center justify-center p-4 md:p-8">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-9 h-9 rounded-xl bg-githubPrimary/20 flex items-center justify-center border border-githubPrimary/30">
              <GitBranch size={18} className="text-githubPrimary" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">Intelli-CI</span>
          </div>
          <h1 className="text-2xl font-bold text-white">Create your account</h1>
          <p className="text-githubTextSecondary text-sm mt-1">Start optimizing your CI/CD pipelines</p>
        </div>

        <div className="bg-githubCard border border-githubBorder rounded-2xl p-8 shadow-xl">
          {error && (
            <div className="mb-5 rounded-lg border border-red-900/50 bg-red-900/20 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <form className="flex flex-col gap-4" onSubmit={handleSignup}>
            {/* Full Name */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">Full Name <span className="text-red-400">*</span></label>
              <input name="name" type="text" className={inputCls} placeholder="Ada Lovelace" required />
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">Email <span className="text-red-400">*</span></label>
              <input name="email" type="email" className={inputCls} placeholder="you@company.com" required />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">Password <span className="text-red-400">*</span></label>
              <div className="relative">
                <input name="password" type={showPwd ? 'text' : 'password'} className={`${inputCls} pr-11`} placeholder="Min. 8 characters" required />
                <button type="button" onClick={() => setShowPwd(!showPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-githubTextSecondary hover:text-white">
                  {showPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">Confirm Password <span className="text-red-400">*</span></label>
              <div className="relative">
                <input name="confirmPassword" type={showCPwd ? 'text' : 'password'} className={`${inputCls} pr-11`} placeholder="Repeat password" required />
                <button type="button" onClick={() => setShowCPwd(!showCPwd)} className="absolute right-3 top-1/2 -translate-y-1/2 text-githubTextSecondary hover:text-white">
                  {showCPwd ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Role */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">Role <span className="text-red-400">*</span></label>
              <select name="profession" className={`${inputCls} cursor-pointer`} required defaultValue="">
                <option value="" disabled>Select your role</option>
                {ROLES.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>

            {/* Organization */}
            <div>
              <label className="block text-xs font-semibold text-githubTextPrimary mb-1.5">
                Organization / College <span className="text-githubTextSecondary font-normal">(optional)</span>
              </label>
              <input name="organization_name" type="text" className={inputCls} placeholder="e.g. Parul University" />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-githubPrimary text-white rounded-lg px-6 py-3 font-semibold hover:bg-green-600 transition-colors mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? <><Loader2 size={16} className="animate-spin" /> Creating account…</> : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-githubTextSecondary mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-githubPrimary hover:underline font-medium">Log in</Link>
        </p>
      </div>
    </div>
  );
}
