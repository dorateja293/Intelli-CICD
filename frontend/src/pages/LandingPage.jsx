import { Link } from 'react-router-dom'
import {
  Cpu, Bot, Zap, BarChart3, GitBranch,
  ArrowRight, CheckCircle, Activity, Shield, Clock,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Navbar from '../components/Navbar'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'

const CHART_DATA = [
  { day: 'Mon', skipped: 8,  executed: 4 },
  { day: 'Tue', skipped: 12, executed: 3 },
  { day: 'Wed', skipped: 6,  executed: 7 },
  { day: 'Thu', skipped: 15, executed: 2 },
  { day: 'Fri', skipped: 11, executed: 5 },
  { day: 'Sat', skipped: 14, executed: 3 },
  { day: 'Sun', skipped: 9,  executed: 4 },
]

const FEATURES = [
  {
    icon: Bot,
    title: 'ML Failure Prediction',
    desc: 'RandomForest model scores every commit for pipeline failure risk in under 50ms.',
    accent: '#3fb950',
  },
  {
    icon: Zap,
    title: 'Smart Test Gating',
    desc: 'Automatically skip, partially run, or fully execute test suites per commit impact.',
    accent: '#f0883e',
  },
  {
    icon: BarChart3,
    title: 'CI Analytics',
    desc: 'Track skip rates, time savings, and failure trends across all your repositories.',
    accent: '#388bfd',
  },
  {
    icon: GitBranch,
    title: 'GitHub Integration',
    desc: 'Install once via webhook. CI decisions arrive back to your pipeline in real time.',
    accent: '#a371f7',
  },
  {
    icon: Shield,
    title: 'AI Log Analysis',
    desc: 'Paste any CI log and get an instant root-cause diagnosis with fix suggestions.',
    accent: '#e3b341',
  },
  {
    icon: Clock,
    title: 'Time Tracking',
    desc: 'See exactly how many CI minutes you save per week, month, and repository.',
    accent: '#79c0ff',
  },
]

const STATS = [
  { value: '68%',    label: 'Avg. CI time reduction' },
  { value: '91%',    label: 'Prediction accuracy' },
  { value: '2.4M+',  label: 'Commits analyzed' },
  { value: '<50ms',  label: 'Decision latency' },
]

const RECENT_ACTIVITY = [
  { sha: 'a1b2c3d', decision: 'skip',    risk: '8%',  files: 2 },
  { sha: 'e4f5a6b', decision: 'run',     risk: '79%', files: 18 },
  { sha: 'c7d8e9f', decision: 'skip',    risk: '12%', files: 1 },
  { sha: '1a2b3c4', decision: 'partial', risk: '35%', files: 5 },
]

const DECISION_CHIP = {
  skip:    { bg: '#1a3a1e', color: '#3fb950', label: 'SKIP' },
  run:     { bg: '#3d1a1a', color: '#f85149', label: 'RUN' },
  partial: { bg: '#2a2a0a', color: '#e3b341', label: 'PARTIAL' },
}

function DecisionChip({ decision }) {
  const s = DECISION_CHIP[decision] ?? DECISION_CHIP.run
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold"
      style={{ background: s.bg, color: s.color }}
    >
      {s.label}
    </span>
  )
}

function FeatureCard({ icon: Icon, title, desc, accent }) {
  return (
    <div
      className="feature-card flex flex-col rounded-2xl border p-8 cursor-default"
      style={{ background: '#161B22', borderColor: '#30363D' }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = accent + '55'
        e.currentTarget.style.transform = 'translateY(-4px)'
        e.currentTarget.style.boxShadow = `0 16px 48px ${accent}12`
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = '#30363D'
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div
        className="inline-flex items-center justify-center w-11 h-11 rounded-xl mb-6 shrink-0"
        style={{ background: accent + '18' }}
      >
        <Icon size={20} style={{ color: accent }} strokeWidth={1.5} />
      </div>
      <h3 className="font-semibold text-base mb-3 leading-snug" style={{ color: '#E6EDF3' }}>{title}</h3>
      <p className="text-sm leading-relaxed flex-1" style={{ color: '#8B949E', lineHeight: '1.75' }}>{desc}</p>
    </div>
  )
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="rounded-lg border px-4 py-3 text-sm shadow-xl"
      style={{ background: '#21262D', borderColor: '#30363D', color: '#E6EDF3' }}
    >
      <p className="font-semibold mb-1" style={{ color: '#8B949E' }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>
          {p.name === 'skipped' ? 'Skipped' : 'Executed'}: <b>{p.value}</b>
        </p>
      ))}
    </div>
  )
}

export default function LandingPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen" style={{ background: '#0D1117' }}>
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 pt-28 pb-24 lg:pt-36 lg:pb-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">

          {/* Left: copy */}
          <div className="flex flex-col gap-8 max-w-xl">

            {/* Badge */}
            <div className="flex">
              <span
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-semibold tracking-wide uppercase"
                style={{ background: '#1a3a1e', borderColor: '#238636', color: '#3fb950' }}
              >
                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#3fb950' }} />
                AI-powered CI optimization
              </span>
            </div>

            {/* Headline */}
            <h1
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight"
              style={{ color: '#E6EDF3' }}
            >
              AI-Powered CI/CD Optimization
            </h1>

            {/* Subtext */}
            <p
              className="text-base sm:text-lg leading-relaxed"
              style={{ color: '#8B949E', lineHeight: '1.75' }}
            >
              Reduce CI runtime and infrastructure cost by intelligently deciding when tests should run.
            </p>

            {/* Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to={user ? '/dashboard' : '/signup'}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm transition-all duration-200 hover:opacity-90 hover:-translate-y-0.5 active:scale-[0.98]"
                style={{ background: '#3fb950', color: '#000', minHeight: '44px' }}
              >
                Get Started
                <ArrowRight size={16} />
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium text-sm border transition-all duration-200 hover:border-[#484f58] hover:bg-[#161B22]"
                style={{ borderColor: '#30363D', color: '#8B949E', minHeight: '44px' }}
              >
                View Demo
              </Link>
            </div>

            {/* Trust badges */}
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 pt-1">
              {['No credit card required', 'Free forever plan', 'GitHub native'].map((t) => (
                <span key={t} className="flex items-center gap-1.5 text-xs" style={{ color: '#8B949E' }}>
                  <CheckCircle size={13} style={{ color: '#3fb950' }} />
                  {t}
                </span>
              ))}
            </div>
          </div>

          {/* Right: live preview panel */}
          <div
            className="rounded-xl border overflow-hidden shadow-2xl"
            style={{ background: '#161B22', borderColor: '#30363D' }}
          >
            {/* Window chrome */}
            <div
              className="flex items-center gap-2 px-5 py-3.5 border-b"
              style={{ background: '#21262D', borderColor: '#30363D' }}
            >
              <span className="w-3 h-3 rounded-full" style={{ background: '#f85149' }} />
              <span className="w-3 h-3 rounded-full" style={{ background: '#f0883e' }} />
              <span className="w-3 h-3 rounded-full" style={{ background: '#3fb950' }} />
              <span className="ml-3 text-xs font-mono" style={{ color: '#8B949E' }}>
                intelli-ci · live predictions
              </span>
            </div>

            {/* Column headers */}
            <div className="px-6 pt-5 pb-0">
              <div
                className="grid grid-cols-4 gap-4 pb-3 border-b text-xs font-semibold uppercase tracking-wider"
                style={{ color: '#8B949E', borderColor: '#30363D' }}
              >
                <span>SHA</span>
                <span>Decision</span>
                <span>Risk</span>
                <span>Files</span>
              </div>
            </div>

            {/* Rows */}
            <div className="px-6 pb-5">
              {RECENT_ACTIVITY.map((r) => (
                <div
                  key={r.sha}
                  className="grid grid-cols-4 gap-4 py-3.5 text-sm items-center border-b last:border-0"
                  style={{ borderColor: '#21262D' }}
                >
                  <span className="font-mono text-xs" style={{ color: '#79c0ff' }}>{r.sha}</span>
                  <DecisionChip decision={r.decision} />
                  <span
                    className="font-mono text-xs"
                    style={{ color: r.decision === 'run' ? '#f85149' : '#3fb950' }}
                  >
                    {r.risk}
                  </span>
                  <span className="text-xs" style={{ color: '#8B949E' }}>{r.files} files</span>
                </div>
              ))}
            </div>

            {/* Status bar */}
            <div
              className="px-6 py-3.5 border-t flex items-center justify-between"
              style={{ background: '#0D1117', borderColor: '#30363D' }}
            >
              <span className="flex items-center gap-1.5 text-xs" style={{ color: '#8B949E' }}>
                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#3fb950' }} />
                Real-time predictions active
              </span>
              <span className="font-mono text-xs" style={{ color: '#3fb950' }}>3 tests skipped</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <section className="border-y" style={{ borderColor: '#21262D' }}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-24">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {STATS.map((s) => (
              <div
                key={s.label}
                className="flex flex-col items-center justify-center rounded-2xl border p-8 text-center card-hover"
                style={{ background: '#161B22', borderColor: '#30363D' }}
              >
                <span className="stat-value mb-3">{s.value}</span>
                <span className="text-xs leading-snug" style={{ color: '#8B949E' }}>{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 lg:px-8 py-28 lg:py-36">
        {/* Section header */}
        <div className="text-center mb-16">
          <span
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-semibold tracking-wide uppercase mb-6"
            style={{ background: '#1a2d4a', borderColor: '#1f3a5f', color: '#388bfd' }}
          >
            Features
          </span>
          <h2
            className="text-3xl sm:text-4xl font-bold mb-5 tracking-tight"
            style={{ color: '#E6EDF3' }}
          >
            Everything you need to cut CI waste
          </h2>
          <p
            className="text-sm sm:text-base max-w-xl mx-auto"
            style={{ color: '#8B949E', lineHeight: '1.75' }}
          >
            Intelli-CI integrates with your existing GitHub workflow with zero configuration overhead.
          </p>
        </div>

        {/* Cards grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f) => <FeatureCard key={f.title} {...f} />)}
        </div>
      </section>

      {/* ── Analytics preview ─────────────────────────────────────────────── */}
      <section className="border-t" style={{ borderColor: '#21262D' }}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-28 lg:py-36">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-20 items-center">

            {/* Text */}
            <div className="flex flex-col gap-8">
              <span
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border text-xs font-semibold tracking-wide uppercase w-fit"
                style={{ background: '#1a2d4a', borderColor: '#1f3a5f', color: '#388bfd' }}
              >
                <Activity size={12} /> Analytics
              </span>

              <h2
                className="text-3xl sm:text-4xl font-bold leading-tight tracking-tight"
                style={{ color: '#E6EDF3' }}
              >
                Visualize your CI efficiency{' '}
                <span style={{ color: '#388bfd' }}>over time</span>
              </h2>

              <p
                className="text-sm sm:text-base"
                style={{ color: '#8B949E', lineHeight: '1.75' }}
              >
                Track test skip rates, pipeline durations, and failure predictions
                across every commit in a single dashboard.
              </p>

              <div className="flex flex-col gap-4 pt-2">
                {[
                  { label: 'Commit risk scoring per push', color: '#3fb950' },
                  { label: 'Skip vs run daily breakdown',  color: '#388bfd' },
                  { label: 'CI minutes saved tracking',    color: '#a371f7' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3 text-sm" style={{ color: '#8B949E' }}>
                    <div className="w-2 h-2 rounded-full shrink-0" style={{ background: item.color }} />
                    {item.label}
                  </div>
                ))}
              </div>
            </div>

            {/* Chart card */}
            <div
              className="rounded-2xl border p-6 sm:p-8"
              style={{ background: '#161B22', borderColor: '#30363D' }}
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                <h3 className="text-base font-semibold" style={{ color: '#E6EDF3' }}>
                  Pipeline decisions — last 7 days
                </h3>
                <div className="flex items-center gap-5 text-xs" style={{ color: '#8B949E' }}>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#238636' }} />Skipped
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#f85149' }} />Executed
                  </span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={CHART_DATA} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradSkip" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#238636" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#238636" stopOpacity={0}   />
                    </linearGradient>
                    <linearGradient id="gradRun" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor="#f85149" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#f85149" stopOpacity={0}   />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#21262D" vertical={false} />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 11 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 11 }} width={28} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="skipped"  stroke="#238636" strokeWidth={2} fill="url(#gradSkip)" name="skipped" />
                  <Area type="monotone" dataKey="executed" stroke="#f85149" strokeWidth={2} fill="url(#gradRun)"  name="executed" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────── */}
      <section className="border-t" style={{ borderColor: '#21262D' }}>
        <div className="max-w-3xl mx-auto px-6 lg:px-8 py-28 lg:py-36 text-center">
          <h2
            className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-6"
            style={{ color: '#E6EDF3' }}
          >
            Start optimizing your CI
            <br />
            <span style={{ color: '#3fb950' }}>pipelines with AI</span>
          </h2>
          <p
            className="text-sm sm:text-base mb-10 mx-auto"
            style={{ color: '#8B949E', lineHeight: '1.75', maxWidth: '28rem' }}
          >
            Connect your GitHub repository in minutes. No infrastructure changes required.
          </p>
          <Link
            to={user ? '/dashboard' : '/signup'}
            className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-lg font-semibold text-sm transition-all duration-200 hover:opacity-90 hover:-translate-y-0.5"
            style={{ background: '#3fb950', color: '#000' }}
          >
            <svg viewBox="0 0 16 16" fill="currentColor" width="16" height="16">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
            </svg>
            Connect GitHub Repository
          </Link>
          <p className="text-xs mt-6" style={{ color: '#8B949E' }}>Free plan · No credit card · Cancel anytime</p>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="border-t" style={{ borderColor: '#21262D' }}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg" style={{ background: '#1a3a1e' }}>
              <Cpu size={14} style={{ color: '#3fb950' }} strokeWidth={1.5} />
            </div>
            <span className="font-bold text-sm" style={{ color: '#E6EDF3' }}>
              INTELLI<span style={{ color: '#3fb950' }}>CI</span>
            </span>
            <span className="text-xs" style={{ color: '#8B949E' }}>© 2026</span>
          </div>
          <p className="text-xs" style={{ color: '#8B949E' }}>Built for developers who ship fast</p>
        </div>
      </footer>
    </div>
  )
}
