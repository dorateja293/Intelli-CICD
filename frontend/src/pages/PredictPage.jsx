import { useState } from 'react'
import { BrainCircuit, CheckCircle2, AlertTriangle, PlayCircle } from 'lucide-react'
import { predictService } from '../services/api'
import { getErrorMessage } from '../services/api'

const DECISION_STYLE = {
  SKIP_TESTS:    { color: '#3fb950', bg: '#1a3a1e', border: '#255130', icon: CheckCircle2 },
  RUN_TESTS:     { color: '#f85149', bg: '#3d1a1a', border: '#6e2020', icon: AlertTriangle },
  PARTIAL_TESTS: { color: '#e3b341', bg: '#2a2a0a', border: '#5c4a00', icon: PlayCircle },
}

const FIELD_CLS = 'w-full bg-[#0d1117] border border-[#30363d] text-[#c9d1d9] rounded-md px-4 py-2.5 outline-none focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] transition-colors'

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-[#c9d1d9] mb-2">{label}</label>
      {children}
    </div>
  )
}

export default function PredictPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({
    files_changed: '3',
    lines_added: '45',
    lines_deleted: '10',
    previous_failures: '0',
    test_coverage: '80',
    is_merge_commit: '0',
    commit_message: '',
  })

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handlePredict = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const lines_added = parseInt(form.lines_added) || 0
      const lines_deleted = parseInt(form.lines_deleted) || 0
      const { data } = await predictService.predict({
        files_changed: parseInt(form.files_changed) || 0,
        lines_added,
        lines_deleted,
        code_churn: lines_added + lines_deleted,
        previous_failures: parseInt(form.previous_failures) || 0,
        test_coverage: parseFloat(form.test_coverage) || 0,
        is_merge_commit: parseInt(form.is_merge_commit) || 0,
        commit_message_length: form.commit_message.length,
        num_contributors_last_30d: 1,
        days_since_last_failure: 30,
        recent_failure_flag: parseInt(form.previous_failures) > 0 ? 1 : 0,
        commit_message: form.commit_message,
        diff: '',
        changed_files: [],
      })
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Prediction failed. Ensure the backend is running.'))
    } finally {
      setLoading(false)
    }
  }

  const ds = result ? (DECISION_STYLE[result.decision] ?? DECISION_STYLE.RUN_TESTS) : null
  const DecisionIcon = ds?.icon

  return (
    <div className="max-w-7xl mx-auto space-y-8 fade-in">
      <div>
        <h1 className="page-title">Manual Prediction</h1>
        <p className="page-sub">Submit commit parameters to get an AI-powered CI decision</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Side: Form */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-8 shadow-xl">
          <h2 className="text-lg font-bold text-[#c9d1d9] mb-6 flex items-center gap-2">
            <BrainCircuit size={20} className="text-[#58a6ff]" />
            Commit Parameters
          </h2>
          <form className="space-y-5" onSubmit={handlePredict}>
            <div className="grid grid-cols-2 gap-5">
              <Field label="Files Changed">
                <input type="number" min="0" value={form.files_changed} onChange={set('files_changed')} className={FIELD_CLS} />
              </Field>
              <Field label="Lines Added">
                <input type="number" min="0" value={form.lines_added} onChange={set('lines_added')} className={FIELD_CLS} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-5">
              <Field label="Lines Deleted">
                <input type="number" min="0" value={form.lines_deleted} onChange={set('lines_deleted')} className={FIELD_CLS} />
              </Field>
              <Field label="Previous Failures">
                <input type="number" min="0" value={form.previous_failures} onChange={set('previous_failures')} className={FIELD_CLS} />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-5">
              <Field label="Test Coverage (%)">
                <input type="number" min="0" max="100" step="0.1" value={form.test_coverage} onChange={set('test_coverage')} className={FIELD_CLS} />
              </Field>
              <Field label="Is Merge Commit">
                <select value={form.is_merge_commit} onChange={set('is_merge_commit')} className={FIELD_CLS}>
                  <option value="0">No</option>
                  <option value="1">Yes</option>
                </select>
              </Field>
            </div>
            <Field label="Commit Message (optional)">
              <input type="text" value={form.commit_message} onChange={set('commit_message')} placeholder="e.g. fix: resolve auth bug" className={FIELD_CLS} />
            </Field>

            {error && (
              <p className="text-sm text-[#f85149] bg-[#3d1a1a] border border-[#6e2020] rounded-lg px-4 py-3">{error}</p>
            )}

            <button disabled={loading} className="w-full mt-2 bg-[#2ea043] hover:bg-[#2c974b] disabled:opacity-60 text-white font-bold py-3 px-4 rounded-lg shadow-sm transition-colors flex justify-center items-center gap-2">
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Run Prediction'
              )}
            </button>
          </form>
        </div>

        {/* Right Side: Analysis */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-8 shadow-xl flex flex-col">
          <h2 className="text-lg font-bold text-[#c9d1d9] mb-6">AI Analysis Result</h2>

          {result ? (
            <div className="flex-1 flex flex-col fade-in space-y-6">
              {/* Decision badge */}
              <div
                className="flex items-center gap-3 px-5 py-4 rounded-xl border font-bold text-xl"
                style={{ background: ds.bg, borderColor: ds.border, color: ds.color }}
              >
                <DecisionIcon size={24} />
                {result.decision.replace('_', ' ')}
              </div>

              {/* Failure probability */}
              <div>
                <div className="flex justify-between text-sm font-medium mb-2">
                  <span className="text-[#8b949e]">Failure Probability</span>
                  <span className="text-[#c9d1d9] font-mono">{(result.failure_probability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-[#0d1117] h-2.5 rounded-full overflow-hidden border border-[#30363d]">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${(result.failure_probability * 100).toFixed(1)}%`, background: ds.color }}
                  />
                </div>
              </div>

              {/* ML / LLM confidence */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-[#0d1117] rounded-lg border border-[#30363d] p-4">
                  <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">ML Confidence</p>
                  <p className="text-[#c9d1d9] font-mono font-bold text-lg">{(result.ml_confidence * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-[#0d1117] rounded-lg border border-[#30363d] p-4">
                  <p className="text-[#8b949e] text-xs uppercase tracking-wider mb-1">LLM Risk</p>
                  <p className="font-bold text-lg" style={{ color: result.llm_risk_level === 'HIGH' ? '#f85149' : result.llm_risk_level === 'LOW' ? '#3fb950' : '#e3b341' }}>
                    {result.llm_risk_level}
                  </p>
                </div>
              </div>

              {/* Reasoning */}
              <div className="bg-[#0d1117] rounded-lg border border-[#30363d] p-5 flex-1">
                <h4 className="text-[#c9d1d9] font-medium mb-2 text-sm uppercase tracking-wide">Reasoning</h4>
                <p className="text-[#8b949e] text-sm leading-relaxed">{result.reasoning}</p>
                {result.affected_modules?.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {result.affected_modules.map((m) => (
                      <span key={m} className="px-2 py-0.5 text-xs rounded bg-[#21262d] text-[#8b949e] border border-[#30363d]">{m}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-[#8b949e] border-2 border-dashed border-[#30363d] rounded-xl bg-[#0d1117]/50 p-6 text-center">
              <BrainCircuit size={48} className="text-[#30363d] mb-4" />
              <p>Fill in the parameters and click <strong className="text-[#c9d1d9]">Run Prediction</strong> to get an AI evaluation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
