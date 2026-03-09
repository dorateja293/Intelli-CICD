import { useState } from 'react'
import { Search, AlertTriangle, CheckCircle, Info, AlertOctagon, Clipboard } from 'lucide-react'
import { logService, getErrorMessage } from '../services/api'

const SAMPLE_LOGS = {
  dependency: `Running pip install -r requirements.txt
Collecting requests>=2.28
  Downloading requests-2.31.0-py3-none-any.whl
ModuleNotFoundError: No module named 'httpx'
ERROR: Could not find a version that satisfies the requirement httpx==0.28.1
build: exited with code 1`,

  test: `============================= test session starts ==============================
collected 24 items
FAILED tests/test_auth.py::test_login_invalid_password - AssertionError: 401 != 200
FAILED tests/test_api.py::test_predict_endpoint - AssertionError: expected RUN_TESTS got SKIP_TESTS
2 failed, 22 passed in 3.42s`,

  timeout: `Running integration tests...
jest FAIL src/__tests__/integration.test.js
  ● Integration › API › should respond within 5000ms
    Error: Timeout of 5000ms exceeded.
    connect ETIMEDOUT 192.168.1.100:5432
Test Suites: 1 failed, 3 passed, 4 total`,

  infrastructure: `Starting services...
docker: Error response from daemon: driver failed programming external connectivity
Connection refused: ECONNREFUSED 127.0.0.1:5432
FATAL: database "intellici" does not exist
Error: Could not connect to PostgreSQL`,
}

const SEVERITY_META = {
  critical: { color: '#f85149', bg: '#3d1a1a', border: '#6e2020', icon: AlertOctagon,  label: 'Critical' },
  high:     { color: '#f0883e', bg: '#3d2a1a', border: '#6e4a20', icon: AlertTriangle, label: 'High' },
  medium:   { color: '#e3b341', bg: '#2a2a0a', border: '#5c4a00', icon: Info,          label: 'Medium' },
  low:      { color: '#3fb950', bg: '#1a3a1e', border: '#255130', icon: CheckCircle,   label: 'Low' },
}

export default function LogAnalyzerPage() {
  const [logText, setLogText] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const handleAnalyze = async () => {
    if (!logText.trim()) return
    setError('')
    setLoading(true)
    setResult(null)
    try {
      const { data } = await logService.analyzeLogs(logText)
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Analysis failed. Is the backend running?'))
    } finally {
      setLoading(false)
    }
  }

  const loadSample = (key) => {
    setLogText(SAMPLE_LOGS[key])
    setResult(null)
    setError('')
  }

  const copyFix = () => {
    if (!result) return
    navigator.clipboard.writeText(result.suggested_fix)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const sm = result ? (SEVERITY_META[result.severity] ?? SEVERITY_META.medium) : null

  return (
    <div className="max-w-6xl mx-auto space-y-8 fade-in">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="page-title">CI Log Analyzer</h1>
          <p className="page-sub">Paste CI log output to classify the error and get actionable fix suggestions</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span className="text-xs" style={{ color: '#8B949E' }}>Try sample:</span>
          {Object.keys(SAMPLE_LOGS).map((k) => (
            <button
              key={k}
              onClick={() => loadSample(k)}
              className="text-xs px-2.5 py-1 rounded-md border transition-colors hover:border-[#388bfd]"
              style={{ background: '#21262D', borderColor: '#30363D', color: '#8B949E' }}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* ── Input ── */}
        <div className="panel">
          <div className="panel-header">
            <h2 className="section-title">CI Log Input</h2>
            <span className="text-xs" style={{ color: '#8B949E' }}>{logText.split('\n').filter(Boolean).length} lines</span>
          </div>
          <div className="p-5 flex flex-col gap-4">
            <textarea
              rows={20}
              value={logText}
              onChange={(e) => { setLogText(e.target.value); setResult(null) }}
              placeholder="Paste your CI log output here..."
              className="w-full font-mono text-xs rounded-lg border px-4 py-3 outline-none resize-none focus:border-[#388bfd] transition-colors"
              style={{ background: '#0D1117', borderColor: '#30363D', color: '#E6EDF3', lineHeight: 1.65 }}
            />

            {error && (
              <p className="text-xs rounded-md border px-3 py-2" style={{ color: '#f85149', background: '#3d1a1a', borderColor: '#6e2020' }}>
                {error}
              </p>
            )}

            <button
              onClick={handleAnalyze}
              disabled={loading || !logText.trim()}
              className="flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-sm transition-all duration-200 hover:opacity-90 disabled:opacity-40"
              style={{ background: '#238636', color: '#fff', minHeight: '50px' }}
            >
              <Search size={14} />
              {loading ? 'Analyzing...' : 'Analyze Log'}
            </button>
          </div>
        </div>

        {/* ── Result ── */}
        <div className="panel">
          <div className="panel-header">
            <h2 className="section-title">Analysis Result</h2>
          </div>
          <div className="p-5">

            {!result && !loading && (
              <div className="flex flex-col items-center justify-center text-center gap-4 py-20">
                <Search size={32} style={{ color: '#30363D' }} />
                <p className="text-sm" style={{ color: '#8B949E' }}>Analyze a log to see results</p>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center gap-4 py-20">
                <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#388bfd' }} />
                <p className="text-sm" style={{ color: '#8B949E' }}>Scanning log patterns...</p>
              </div>
            )}

            {result && !loading && (
              <div className="space-y-5">

                {/* Error type + severity */}
                <div
                  className="flex items-center gap-3 rounded-xl border p-4"
                  style={{ background: sm.bg, borderColor: sm.border }}
                >
                  <sm.icon size={20} style={{ color: sm.color }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border"
                        style={{ color: sm.color, borderColor: sm.border, background: sm.bg }}
                      >
                        {sm.label}
                      </span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: '#21262D', color: '#8B949E' }}>
                        {result.error_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sm font-medium mt-1.5 leading-snug" style={{ color: '#E6EDF3' }}>
                      {result.root_cause}
                    </p>
                  </div>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between text-xs mb-1.5">
                    <span style={{ color: '#8B949E' }}>Classification confidence</span>
                    <span className="font-mono font-semibold" style={{ color: '#E6EDF3' }}>
                      {(result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: '#21262D' }}>
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${result.confidence * 100}%`, background: sm.color }}
                    />
                  </div>
                </div>

                {/* Suggested fix */}
                <div className="rounded-lg border" style={{ background: '#21262D', borderColor: '#30363D' }}>
                  <div className="flex items-center justify-between px-3 py-2.5 border-b" style={{ borderColor: '#30363D' }}>
                    <span className="text-xs font-semibold" style={{ color: '#E6EDF3' }}>Suggested Fix</span>
                    <button
                      onClick={copyFix}
                      className="flex items-center gap-1.5 text-xs transition-colors hover:text-[#388bfd]"
                      style={{ color: '#8B949E' }}
                    >
                      <Clipboard size={12} />
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <div className="px-3 py-3">
                    {result.suggested_fix.split('\n').map((line, i) => (
                      <p key={i} className="text-sm leading-relaxed" style={{ color: line.match(/^\d\./) ? '#E6EDF3' : '#8B949E' }}>
                        {line}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Matched lines */}
                {result.matched_lines?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold mb-2" style={{ color: '#8B949E' }}>
                      Matched log lines ({result.matched_lines.length})
                    </p>
                    <div className="rounded-md border overflow-hidden" style={{ borderColor: '#30363D' }}>
                      {result.matched_lines.map((line, i) => (
                        <p
                          key={i}
                          className="px-3 py-1.5 text-xs font-mono border-b last:border-0 truncate"
                          style={{ background: '#0D1117', borderColor: '#21262D', color: sm.color }}
                        >
                          {line}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
