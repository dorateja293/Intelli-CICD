import { useState } from 'react'
import { Zap, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, Activity } from 'lucide-react'
import { predictService, getErrorMessage } from '../services/api'

const DECISION_META = {
  SKIP_TESTS:    { label: 'SKIP TESTS',    bg: '#1a3a1e', color: '#3fb950', border: '#255130', icon: CheckCircle },
  RUN_TESTS:     { label: 'RUN TESTS',     bg: '#3d1a1a', color: '#f85149', border: '#6e2020', icon: AlertTriangle },
  PARTIAL_TESTS: { label: 'PARTIAL TESTS', bg: '#2a2a0a', color: '#e3b341', border: '#5c4a00', icon: Activity },
}

const DEFAULT_FORM = {
  files_changed: 3,
  lines_added: 45,
  lines_deleted: 12,
  code_churn: 57,
  previous_failures: 0,
  test_coverage: 80,
  is_merge_commit: 0,
  commit_message_length: 60,
  num_contributors_last_30d: 2,
  days_since_last_failure: 14,
  recent_failure_flag: 0,
  commit_message: 'fix: update user authentication logic',
  diff: '',
  changed_files: 'src/auth/user.py\nsrc/api/routes/auth.py',
}

function Field({ label, id, type = 'number', value, onChange, hint }) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium" style={{ color: '#E6EDF3' }}>
        {label}
        {hint && <span className="ml-1.5 text-xs font-normal" style={{ color: '#8B949E' }}>{hint}</span>}
      </label>
      <input
        id={id}
        type={type}
        step={type === 'number' ? 'any' : undefined}
        value={value}
        onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) || 0 : e.target.value)}
        className="w-full px-4 py-2.5 rounded-lg border text-sm outline-none transition-colors focus:border-[#388bfd]"
        style={{ background: '#0D1117', borderColor: '#30363D', color: '#E6EDF3', minHeight: '46px' }}
      />
    </div>
  )
}

function Toggle({ label, id, value, onChange }) {
  return (
    <div className="flex items-center justify-between">
      <label htmlFor={id} className="text-sm font-medium" style={{ color: '#E6EDF3' }}>{label}</label>
      <button
        id={id}
        type="button"
        onClick={() => onChange(value ? 0 : 1)}
              className="relative w-11 h-6 sm:w-10 sm:h-5 rounded-full transition-colors duration-200 min-w-[44px] min-h-[24px] shrink-0"
        style={{ background: value ? '#238636' : '#30363D' }}
      >
        <span
          className="absolute top-0.5 w-4 h-4 rounded-full transition-transform duration-200"
          style={{ background: '#E6EDF3', transform: value ? 'translateX(22px)' : 'translateX(2px)' }}
        />
      </button>
    </div>
  )
}

function RiskBar({ probability }) {
  const pct = Math.round(probability * 100)
  const color = pct >= 55 ? '#f85149' : pct >= 30 ? '#e3b341' : '#3fb950'
  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span style={{ color: '#8B949E' }}>Failure probability</span>
        <span className="font-mono font-bold" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-2 rounded-full overflow-hidden" style={{ background: '#21262D' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  )
}

export default function PredictPage() {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const set = (field) => (val) => setForm((f) => ({ ...f, [field]: val }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        ...form,
        changed_files: form.changed_files
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean),
      }
      const { data } = await predictService.predict(payload)
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Prediction failed. Is the backend running?'))
    } finally {
      setLoading(false)
    }
  }

  const dm = result ? (DECISION_META[result.decision] ?? DECISION_META.RUN_TESTS) : null

  return (
    <div className="max-w-6xl mx-auto space-y-8 sm:space-y-10 fade-in min-w-0">
      <div>
        <h1 className="page-title">Manual Prediction</h1>
        <p className="page-sub">Enter commit metrics to get an instant ML + rule-based CI decision</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 min-w-0">

        {/* ── Form ── */}
        <div className="panel">
          <div className="panel-header">
            <h2 className="section-title">Commit Metrics</h2>
          </div>
          <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-5">

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Field label="Files changed"    id="fc"  value={form.files_changed}    onChange={set('files_changed')} />
              <Field label="Lines added"      id="la"  value={form.lines_added}      onChange={set('lines_added')} />
              <Field label="Lines deleted"    id="ld"  value={form.lines_deleted}    onChange={set('lines_deleted')} />
              <Field label="Code churn"       id="cc"  value={form.code_churn}       onChange={set('code_churn')}   hint="(added+deleted)" />
              <Field label="Prev. failures"   id="pf"  value={form.previous_failures} onChange={set('previous_failures')} />
              <Field label="Test coverage %"  id="tc"  value={form.test_coverage}    onChange={set('test_coverage')} />
            </div>

            <Toggle label="Merge commit"      id="mc" value={form.is_merge_commit}     onChange={set('is_merge_commit')} />
            <Toggle label="Recent failure"    id="rf" value={form.recent_failure_flag}  onChange={set('recent_failure_flag')} />

            <Field
              label="Commit message"
              id="msg"
              type="text"
              value={form.commit_message}
              onChange={set('commit_message')}
            />

            {/* Advanced section */}
            <button
              type="button"
              className="flex items-center gap-1.5 text-xs transition-colors hover:text-[#388bfd]"
              style={{ color: '#8B949E' }}
              onClick={() => setShowAdvanced((v) => !v)}
            >
              {showAdvanced ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              Advanced options
            </button>

            {showAdvanced && (
              <div className="space-y-4 pt-1">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Msg length"         id="ml"  value={form.commit_message_length}     onChange={set('commit_message_length')} />
                  <Field label="Contributors (30d)"  id="nc"  value={form.num_contributors_last_30d} onChange={set('num_contributors_last_30d')} />
                  <Field label="Days since failure"  id="dsf" value={form.days_since_last_failure}   onChange={set('days_since_last_failure')} />
                </div>
                <div>
                  <label className="text-sm font-medium block mb-1.5" style={{ color: '#E6EDF3' }}>
                    Changed files <span className="text-xs font-normal" style={{ color: '#8B949E' }}>(one per line)</span>
                  </label>
                  <textarea
                    rows={4}
                    value={form.changed_files}
                    onChange={(e) => set('changed_files')(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-lg border text-sm font-mono outline-none resize-none focus:border-[#388bfd]"
                    style={{ background: '#0D1117', borderColor: '#30363D', color: '#E6EDF3' }}
                  />
                </div>
              </div>
            )}

            {error && (
              <p className="text-xs rounded-md border px-3 py-2" style={{ color: '#f85149', background: '#3d1a1a', borderColor: '#6e2020' }}>
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-lg font-semibold text-sm min-h-[50px] transition-all duration-200 hover:opacity-90 disabled:opacity-50 active:scale-[0.98]"
              style={{ background: '#238636', color: '#fff' }}
            >
              <Zap size={14} />
              {loading ? 'Predicting...' : 'Run Prediction'}
            </button>
          </form>
          </div>
        </div>

        {/* ── Result ── */}
        <div className="panel flex flex-col">
          <div className="panel-header">
            <h2 className="section-title">Prediction Result</h2>
          </div>
          <div className="p-6 flex flex-col gap-6 flex-1">

          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center gap-4 py-16">
              <Zap size={32} style={{ color: '#30363D' }} />
              <p className="text-sm" style={{ color: '#8B949E' }}>Fill in the form and run a prediction</p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 py-12">
              <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#3fb950' }} />
              <p className="text-sm" style={{ color: '#8B949E' }}>Analyzing commit...</p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              {/* Decision badge */}
              <div
                className="flex items-center gap-3 rounded-xl border p-4"
                style={{ background: dm.bg + '80', borderColor: dm.color + '40' }}
              >
                <dm.icon size={22} style={{ color: dm.color }} />
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider mb-0.5" style={{ color: dm.color + 'bb' }}>Decision</p>
                  <p className="text-xl font-bold" style={{ color: dm.color }}>{dm.label}</p>
                </div>
              </div>

              <RiskBar probability={result.failure_probability} />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  { label: 'ML Confidence',   value: `${(result.ml_confidence * 100).toFixed(1)}%` },
                  { label: 'LLM Risk',         value: result.llm_risk_level },
                  { label: 'LLM Confidence',  value: `${(result.llm_confidence * 100).toFixed(1)}%` },
                ].map((m) => (
                  <div
                    key={m.label}
                    className="rounded-lg p-3 border"
                    style={{ background: '#21262D', borderColor: '#30363D' }}
                  >
                    <p className="text-xs mb-1" style={{ color: '#8B949E' }}>{m.label}</p>
                    <p className="font-semibold text-sm" style={{ color: '#E6EDF3' }}>{m.value}</p>
                  </div>
                ))}
              </div>

              {result.reasoning && (
                <div className="rounded-lg p-3 border" style={{ background: '#21262D', borderColor: '#30363D' }}>
                  <p className="text-xs font-semibold mb-1.5" style={{ color: '#8B949E' }}>Reasoning</p>
                  <p className="text-sm leading-relaxed" style={{ color: '#E6EDF3' }}>{result.reasoning}</p>
                </div>
              )}

              {result.affected_modules?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold mb-2" style={{ color: '#8B949E' }}>Affected modules</p>
                  <div className="flex flex-wrap gap-1.5">
                    {result.affected_modules.map((m) => (
                      <span
                        key={m}
                        className="px-2 py-0.5 rounded-md text-xs font-mono border"
                        style={{ background: '#1a2d4a', color: '#79c0ff', borderColor: '#1f3a5f' }}
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {result.partial_test_paths?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold mb-2" style={{ color: '#8B949E' }}>Partial test paths</p>
                  <div className="space-y-1">
                    {result.partial_test_paths.map((p) => (
                      <p key={p} className="text-xs font-mono px-2 py-1 rounded" style={{ background: '#21262D', color: '#e3b341' }}>
                        {p}
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
