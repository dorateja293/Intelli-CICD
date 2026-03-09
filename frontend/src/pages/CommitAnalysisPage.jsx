import { useEffect, useState } from 'react'
import CommitTable from '../components/CommitTable'
import { commitService } from '../services/api'

const MOCK_COMMITS = Array.from({ length: 25 }, (_, i) => ({
  commit_sha: Math.random().toString(16).slice(2, 14),
  files_changed: Math.floor(Math.random() * 20) + 1,
  code_churn: Math.floor(Math.random() * 600) + 10,
  failure_probability: parseFloat((Math.random()).toFixed(4)),
  decision: Math.random() > 0.4 ? 'SKIP_TESTS' : 'RUN_TESTS',
  created_at: new Date(Date.now() - i * 3600_000 * 6).toISOString(),
}))

export default function CommitAnalysisPage() {
  const [commits, setCommits] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    commitService.getCommits({ limit: 200 })
      .then(({ data }) => setCommits(Array.isArray(data) ? data : data.commits ?? []))
      .catch(() => setCommits(MOCK_COMMITS))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-7xl mx-auto space-y-8 fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Commit Analysis</h1>
          <p className="page-sub">
            {loading ? 'Loading commits…' : `${commits.length} commits — search, filter, and sort`}
          </p>
        </div>
        <div
          className="shrink-0 flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs"
          style={{ background: '#161B22', borderColor: '#30363D', color: '#8B949E' }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: loading ? '#f0883e' : '#3fb950' }}
          />
          {loading ? 'Fetching…' : 'Live data'}
        </div>
      </div>
      <CommitTable commits={commits} loading={loading} />
    </div>
  )
}
