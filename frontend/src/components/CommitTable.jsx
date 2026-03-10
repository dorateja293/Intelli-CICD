import { useState, useMemo } from 'react'
import { Search, ChevronUp, ChevronDown } from 'lucide-react'

const DECISIONS = {
  SKIP_TESTS:    { label: 'SKIP TESTS',    bg: '#1a3a1e', color: '#3fb950', border: '#255130' },
  RUN_TESTS:     { label: 'RUN TESTS',     bg: '#3d1a1a', color: '#f85149', border: '#6e2020' },
  PARTIAL_TESTS: { label: 'PARTIAL TESTS', bg: '#2a2a0a', color: '#e3b341', border: '#5c4a00' },
}

function DecisionBadge({ decision }) {
  const style = DECISIONS[decision] ?? { label: decision, bg: '#21262D', color: '#8B949E', border: '#30363D' }
  return (
    <span
      className="px-2 py-0.5 rounded-full text-xs font-semibold border"
      style={{ background: style.bg, color: style.color, borderColor: style.border }}
    >
      {style.label}
    </span>
  )
}

function SkeletonRow() {
  return (
    <tr>
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <td key={i} className="px-5 py-5">
          <div className="skeleton h-4 w-full" />
        </td>
      ))}
    </tr>
  )
}

function SortIcon({ col, sortKey, sortDir }) {
  if (sortKey !== col) return <ChevronUp size={12} style={{ opacity: 0.3 }} />
  return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
}

function Col({ col, label, sortKey, sortDir, onSort }) {
  return (
    <th
      className="px-5 py-5 text-left text-sm font-semibold uppercase tracking-wide cursor-pointer select-none hover:text-[#E6EDF3] transition-colors"
      style={{ color: '#8B949E' }}
      onClick={() => onSort(col)}
    >
      <span className="flex items-center gap-1">{label} <SortIcon col={col} sortKey={sortKey} sortDir={sortDir} /></span>
    </th>
  )
}

export default function CommitTable({ commits = [], loading = false }) {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('ALL')
  const [sortKey, setSortKey] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 10

  const filtered = useMemo(() => {
    let data = commits
    if (filter !== 'ALL') data = data.filter((c) => c.decision === filter)
    if (search.trim()) {
      const q = search.toLowerCase()
      data = data.filter(
        (c) =>
          c.commit_sha?.toLowerCase().includes(q) ||
          c.decision?.toLowerCase().includes(q)
      )
    }
    data = [...data].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })
    return data
  }, [commits, search, filter, sortKey, sortDir])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(key); setSortDir('asc') }
  }

  return (
    <div className="panel">
      {/* Toolbar */}
      <div className="panel-header flex-wrap gap-3">
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm flex-1 min-w-48"
          style={{ background: '#0D1117', borderColor: '#30363D' }}
        >
          <Search size={14} style={{ color: '#8B949E' }} />
          <input
            className="bg-transparent outline-none text-sm w-full"
            style={{ color: '#E6EDF3' }}
            placeholder="Search by SHA or decision…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {['ALL', 'SKIP_TESTS', 'RUN_TESTS', 'PARTIAL_TESTS'].map((f) => (
            <button
              key={f}
              onClick={() => { setFilter(f); setPage(1) }}
              className="px-4 py-2 rounded-md text-sm font-medium border transition-colors"
              style={{
                background: filter === f ? '#21262D' : 'transparent',
                borderColor: filter === f ? '#444c56' : '#30363D',
                color: filter === f ? '#E6EDF3' : '#8B949E',
              }}
            >
              {f === 'ALL' ? 'All' : f === 'SKIP_TESTS' ? 'Skip' : f === 'RUN_TESTS' ? 'Run' : 'Partial'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" style={{ background: 'var(--color-bg-primary)' }}>
          <thead style={{ background: 'var(--color-bg-secondary)' }}>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <Col col="commit_sha" label="Commit SHA" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
              <Col col="files_changed" label="Files" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
              <Col col="code_churn" label="Churn" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
              <Col col="failure_probability" label="Failure %" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
              <th className="px-5 py-5 text-left text-sm font-semibold uppercase tracking-wide" style={{ color: '#8B949E' }}>Decision</th>
              <Col col="created_at" label="Timestamp" sortKey={sortKey} sortDir={sortDir} onSort={handleSort} />
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 6 }).map((_, i) => <SkeletonRow key={i} />)
              : paginated.length === 0
              ? (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-sm" style={{ color: '#8B949E' }}>
                    No commits found.
                  </td>
                </tr>
              )
              : paginated.map((row) => (
                <tr
                  key={row.commit_sha}
                  className="border-t transition-colors hover:bg-[#161B22]"
                  style={{ borderColor: '#21262D' }}
                >
                  <td className="px-5 py-5 font-mono text-sm" style={{ color: '#79c0ff' }}>
                    {row.commit_sha?.slice(0, 8)}…
                  </td>
                  <td className="px-5 py-5 text-sm" style={{ color: '#E6EDF3' }}>{row.files_changed ?? '—'}</td>
                  <td className="px-5 py-5 text-sm" style={{ color: '#E6EDF3' }}>{row.code_churn ?? '—'}</td>
                  <td className="px-5 py-5">
                    <span
                      className="font-mono text-sm"
                      style={{
                        color: row.failure_probability > 0.5 ? '#f85149' : '#3fb950',
                      }}
                    >
                      {row.failure_probability != null
                        ? `${(row.failure_probability * 100).toFixed(1)}%`
                        : '—'}
                    </span>
                  </td>
                  <td className="px-5 py-5">
                    <DecisionBadge decision={row.decision} />
                  </td>
                  <td className="px-5 py-5 text-sm" style={{ color: '#8B949E' }}>
                    {row.created_at
                      ? new Date(row.created_at).toLocaleString()
                      : '—'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="divider flex items-center justify-between px-5 py-4 text-sm" style={{ color: '#8B949E', background: 'var(--color-bg-secondary)' }}>
        <span>{filtered.length} result{filtered.length !== 1 ? 's' : ''}</span>
        <div className="flex items-center gap-2">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-[#21262D] transition-colors"
            style={{ borderColor: '#30363D', color: '#E6EDF3' }}
          >
            ← Prev
          </button>
          <span>Page {page} / {totalPages}</span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="px-2 py-1 rounded border disabled:opacity-40 hover:bg-[#21262D] transition-colors"
            style={{ borderColor: '#30363D', color: '#E6EDF3' }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  )
}
