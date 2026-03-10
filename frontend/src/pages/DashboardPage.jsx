import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { GitCommitHorizontal, SkipForward, PlayCircle, Clock, TrendingUp, ArrowUpRight } from 'lucide-react'
import Card from '../components/Card'
import { DecisionBarChart } from '../components/Charts'
import { analyticsService, commitService } from '../services/api'

const DECISION_STYLES = {
  SKIP_TESTS:    { bg: '#1a3a1e', color: '#3fb950', label: 'SKIP' },
  RUN_TESTS:     { bg: '#3d1a1a', color: '#f85149', label: 'RUN' },
  PARTIAL_TESTS: { bg: '#2a2a0a', color: '#e3b341', label: 'PARTIAL' },
}

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [recentCommits, setRecentCommits] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analyticsService.getSummary(),
      commitService.getCommits({ limit: 5 }),
    ])
      .then(([{ data: summary }, { data: commitsData }]) => {
        setStats(summary)
        setRecentCommits(Array.isArray(commitsData) ? commitsData : commitsData.commits ?? [])
      })
      .catch(() => {
        setStats({ total: 0, skipped: 0, executed: 0, time_saved: 0 })
        setRecentCommits([])
      })
      .finally(() => setLoading(false))
  }, [])

  const total     = stats?.total    ?? 0
  const skipped   = stats?.skipped  ?? 0
  const executed  = stats?.executed ?? 0
  const timeSaved = `${stats?.time_saved ?? 0} min`
  const skipRate  = total > 0 ? `${((skipped / total) * 100).toFixed(0)}% skip rate` : '—'

  return (
    <div className="max-w-7xl mx-auto space-y-8 sm:space-y-10 fade-in">

      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-sub">CI prediction overview &amp; recent activity</p>
        </div>
        <div
          className="shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs"
          style={{ background: '#161B22', borderColor: '#30363D', color: '#8B949E' }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#3fb950]" />
          Live data
        </div>
      </div>

      {/* KPI Cards — 1 col mobile, 2 cols tablet, 4 cols desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card title="Total Analyzed"  value={loading ? null : total}     subtitle="All time"                  icon={GitCommitHorizontal} accent="#388bfd" loading={loading} />
        <Card title="Tests Skipped"   value={loading ? null : skipped}   subtitle={loading ? null : skipRate} icon={SkipForward}         accent="#3fb950" loading={loading} />
        <Card title="Tests Executed"  value={loading ? null : executed}  subtitle="Full & partial runs"       icon={PlayCircle}          accent="#f85149" loading={loading} />
        <Card title="CI Time Saved"   value={loading ? null : timeSaved} subtitle="Est. 10 min/run"           icon={Clock}               accent="#a371f7" loading={loading} />
      </div>

      {/* Chart + Recent commits — stack on mobile/tablet */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 min-w-0">

        {/* Chart */}
        <div className="panel lg:col-span-2 min-w-0">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              <TrendingUp size={14} style={{ color: '#8B949E' }} />
              <h2 className="section-title">Decision breakdown</h2>
            </div>
            <span className="text-xs" style={{ color: '#8B949E' }}>Skip vs run</span>
          </div>
          <div className="p-5 sm:p-6">
            <DecisionBarChart data={{ skipped, executed }} loading={loading} />
          </div>
        </div>

        {/* Recent commits table */}
        <div className="panel lg:col-span-3 min-w-0">
          <div className="panel-header">
            <h2 className="section-title">Recent commits</h2>
            <Link
              to="/commits"
              className="nav-item text-xs"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              View all <ArrowUpRight size={11} />
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr style={{ borderBottom: '1px solid #21262D' }}>
                  {['SHA', 'Decision', 'Risk', 'When'].map((h) => (
                    <th
                      key={h}
                      className="px-5 py-5 text-left font-semibold uppercase tracking-wider text-xs"
                      style={{ color: '#8B949E' }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading
                  ? Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #21262D' }}>
                        {[1, 2, 3, 4].map((j) => (
                          <td key={j} className="px-5 py-5">
                            <div className="skeleton h-4 w-full" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : recentCommits.length === 0
                  ? (
                      <tr>
                        <td colSpan={4} className="px-4 py-8 text-center text-xs" style={{ color: '#8B949E' }}>
                          No commits yet — connect a repository or run a prediction.
                        </td>
                      </tr>
                    )
                  : recentCommits.map((c) => {
                      const ds = DECISION_STYLES[c.decision] || DECISION_STYLES.RUN_TESTS
                      return (
                        <tr
                          key={c.commit_sha}
                          className="transition-colors hover:bg-[#21262D]"
                          style={{ borderBottom: '1px solid #21262D' }}
                        >
                          <td className="px-5 py-5 font-mono text-sm" style={{ color: '#79c0ff' }}>
                            {c.commit_sha?.slice(0, 8)}
                          </td>
                          <td className="px-5 py-5">
                            <span
                              className="inline-flex px-2.5 py-1 rounded-full font-semibold text-xs"
                              style={{ background: ds.bg, color: ds.color }}
                            >
                              {ds.label}
                            </span>
                          </td>
                          <td
                            className="px-5 py-5 font-mono text-sm"
                            style={{ color: c.failure_probability > 0.5 ? '#f85149' : '#3fb950' }}
                          >
                            {c.failure_probability != null ? `${(c.failure_probability * 100).toFixed(1)}%` : '—'}
                          </td>
                          <td className="px-5 py-5 text-sm" style={{ color: '#8B949E' }}>
                            {c.created_at
                              ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                              : '—'}
                          </td>
                        </tr>
                      )
                    })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
