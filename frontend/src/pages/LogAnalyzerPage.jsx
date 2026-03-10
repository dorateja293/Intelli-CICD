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
  critical: { color: '#f85149', bg: '#f8514926', border: '#f8514940', icon: AlertOctagon,  label: 'Critical' },
  high:     { color: '#d29922', bg: '#d2992226', border: '#d2992240', icon: AlertTriangle, label: 'High' },
  medium:   { color: '#58a6ff', bg: '#58a6ff26', border: '#58a6ff40', icon: Info,          label: 'Medium' },
  low:      { color: '#3fb950', bg: '#2ea04326', border: '#3fb95040', icon: CheckCircle,   label: 'Low' },
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
    <div className="max-w-[1100px] mx-auto space-y-8 fade-in">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div>
          <h1 className="page-title">CI Log Analyzer</h1>
          <p className="page-sub">Paste CI log output to classify the error and get actionable fix suggestions</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span className="text-xs font-medium text-[var(--color-text-secondary)]">Try sample:</span>
          {Object.keys(SAMPLE_LOGS).map((k) => (
            <button
              key={k}
              onClick={() => loadSample(k)}
              className="text-sm px-3 py-1.5 rounded-md border font-medium bg-[#21262d] border-[#30363d] text-[var(--color-text-secondary)] transition-colors hover:border-[#8b949e] hover:text-[var(--color-text-primary)] shadow-sm"
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
            <span className="text-xs font-medium text-[var(--color-text-secondary)]">{logText.split('\n').filter(Boolean).length} lines</span>
          </div>
          <div className="p-5 flex flex-col gap-4">
            <textarea
              rows={20}
              value={logText}
              onChange={(e) => { setLogText(e.target.value); setResult(null) }}
              placeholder="Paste your CI log output here..."
              className="w-full font-mono text-xs rounded-lg border px-4 py-3 outline-none resize-none bg-[#0d1117] border-[#30363d] text-[var(--color-text-primary)] focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all duration-200 hover:border-[#8b949e]"
              style={{ lineHeight: 1.65 }}
            />

            {error && (
              <p className="text-sm rounded-md border px-4 py-3 bg-[#f8514926] text-[#f85149] border-[#f8514940]">
                {error}
              </p>
            )}

            <button
              onClick={handleAnalyze}
              disabled={loading || !logText.trim()}
              className="flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-sm transition-all duration-200 bg-[#2ea043] text-white hover:bg-[#238636] disabled:opacity-50"
              style={{ minHeight: '48px' }}
            >
              <Search size={16} strokeWidth={2} />
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
                <Search size={36} className="text-[#30363d]" />
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">Analyze a log to see results</p>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-center justify-center gap-4 py-20">
                <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin border-[#58a6ff]" />
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">Scanning log patterns...</p>
              </div>
            )}

            {result && !loading && (
              <div className="space-y-6">

                {/* Error type + severity */}
                <div
                  className="flex items-center gap-4 rounded-xl border p-5 shadow-sm"
                  style={{ background: sm.bg, borderColor: sm.border }}
                >
                  <sm.icon size={26} style={{ color: sm.color }} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <span
                        className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md border"
                        style={{ color: sm.color, borderColor: sm.border, background: sm.bg }}
                      >
                        {sm.label}
                      </span>
                      <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-md bg-[#21262d] text-[var(--color-text-secondary)] border border-[#30363d]">
                        {result.error_type.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <p className="text-sm font-semibold leading-snug text-[var(--color-text-primary)]">
                      {result.root_cause}
                    </p>
                  </div>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between text-xs mb-1.5 font-medium">
                    <span className="text-[var(--color-text-secondary)]">Classification confidence</span>
                    <span className="font-mono font-bold text-[var(--color-text-primary)]">
                      {(result.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-[#21262d]">
                    <div
                      className="h-full rounded-full transition-all duration-500 shadow-[0_0_8px_currentColor] opacity-90"
                      style={{ width: `${result.confidence * 100}%`, background: sm.color }}
                    />
                  </div>
                </div>

                {/* Suggested fix */}
                <div className="rounded-xl border bg-[#0d1117] border-[#30363d]">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-[#30363d]">
                    <span className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">Suggested Fix</span>
                    <button
                      onClick={copyFix}
                      className="flex items-center gap-1.5 text-xs font-medium text-[#2f81f7] hover:text-[#58a6ff] transition-colors"
                    >
                      <Clipboard size={14} />
                      {copied ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                  <div className="px-5 py-4">
                    {result.suggested_fix.split('\n').map((line, i) => (
                      <p key={i} className={`text-sm leading-relaxed mb-1 last:mb-0 ${line.match(/^\d\./) ? 'text-[var(--color-text-primary)] font-medium' : 'text-[var(--color-text-secondary)]'}`}>
                        {line}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Matched lines */}
                {result.matched_lines?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider mb-2 text-[var(--color-text-secondary)]">
                      Matched log lines ({result.matched_lines.length})
                    </p>
                    <div className="rounded-xl border overflow-hidden border-[#30363d]">
                      {result.matched_lines.map((line, i) => (
                        <p
                          key={i}
                          className="px-4 py-2.5 text-xs font-mono border-b border-[#30363d] last:border-0 truncate font-medium bg-[#161b22]"
                          style={{ color: sm.color }}
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
