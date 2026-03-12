import { useState } from 'react'
import { TerminalSquare, AlertTriangle, PlayCircle, BrainCircuit } from 'lucide-react'
import { logService, getErrorMessage } from '../services/api'

export default function LogAnalyzerPage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [logs, setLogs] = useState('')

  const handleAnalyze = async () => {
    if (!logs.trim()) return
    setError(null)
    setLoading(true)
    try {
      const { data } = await logService.analyzeLogs(logs)
      setResult(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Analysis failed. Ensure the backend is running.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#c9d1d9] tracking-tight">AI Log Analyzer</h1>
        <p className="text-[#8b949e] text-sm mt-1">Paste your CI/CD logs to identify root causes and get suggested fixes</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[700px]">
        {/* Left Side: Input */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl flex flex-col overflow-hidden shadow-xl">
          <div className="p-4 border-b border-[#30363d] bg-[#0d1117]/50 flex items-center gap-2">
            <TerminalSquare size={18} className="text-[#8b949e]" />
            <span className="text-sm font-medium text-[#c9d1d9]">Raw Build Output</span>
          </div>
          <div className="flex-1 p-6 flex flex-col">
            <textarea 
              value={logs}
              onChange={(e) => setLogs(e.target.value)}
              className="flex-1 w-full bg-[#0d1117] border border-[#30363d] text-[#c9d1d9] font-mono text-sm rounded-lg p-4 outline-none focus:border-[#58a6ff] focus:ring-1 focus:ring-[#58a6ff] transition-all resize-none shadow-inner"
              placeholder="Paste terminal error trace here..."
            />
            <button 
              onClick={handleAnalyze}
              disabled={loading || !logs}
              className="w-full mt-6 bg-[#2ea043] hover:bg-[#2c974b] disabled:bg-[#2ea043]/50 disabled:cursor-not-allowed text-white font-bold py-3.5 px-4 rounded-lg shadow-sm transition-colors flex justify-center items-center gap-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              ) : (
                <>
                  <PlayCircle size={18} />
                  Analyze Logs
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Side: Output */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-xl flex flex-col overflow-hidden shadow-xl">
          <div className="p-4 border-b border-[#30363d] bg-[#0d1117]/50 flex items-center gap-2">
            <BrainCircuit size={18} className="text-[#58a6ff]" />
            <span className="text-sm font-medium text-[#c9d1d9]">AI Diagnosis</span>
          </div>
          
          <div className="flex-1 p-8 overflow-y-auto">
            {error && (
              <div className="mb-4 text-sm text-[#f85149] bg-[#3d1a1a] border border-[#6e2020] rounded-lg px-4 py-3">{error}</div>
            )}
            {result ? (
              <div className="space-y-8 fade-in">
                {/* Error Type */}
                <div>
                  <h4 className="text-[#8b949e] text-xs font-semibold uppercase tracking-widest mb-3">Error Classification</h4>
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#f85149]/10 border border-[#f85149]/20 text-[#f85149] rounded-lg">
                    <AlertTriangle size={18} />
                    <span className="font-bold">{result.error_type}</span>
                  </div>
                </div>

                {/* Root Cause */}
                <div>
                  <h4 className="text-[#8b949e] text-xs font-semibold uppercase tracking-widest mb-3">Root Cause Analysis</h4>
                  <p className="text-[#c9d1d9] text-sm leading-relaxed bg-[#0d1117] p-5 rounded-lg border border-[#30363d] shadow-inner">
                    {result.root_cause}
                  </p>
                </div>

                {/* Confidence + Severity */}
                <div className="flex items-center justify-between border-y border-[#30363d] py-4">
                  <span className="text-[#c9d1d9] font-medium text-sm">Confidence</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs px-2 py-0.5 rounded border font-semibold"
                      style={{
                        color: result.severity === 'HIGH' ? '#f85149' : result.severity === 'LOW' ? '#3fb950' : '#e3b341',
                        borderColor: result.severity === 'HIGH' ? '#6e2020' : result.severity === 'LOW' ? '#255130' : '#5c4a00',
                        background: result.severity === 'HIGH' ? '#3d1a1a' : result.severity === 'LOW' ? '#1a3a1e' : '#2a2a0a',
                      }}
                    >{result.severity}</span>
                    <div className="w-2 h-2 rounded-full bg-[#2ea043] animate-pulse"></div>
                    <span className="text-[#2ea043] font-mono font-bold">{(result.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {/* Matched Lines */}
                {result.matched_lines?.length > 0 && (
                  <div>
                    <h4 className="text-[#8b949e] text-xs font-semibold uppercase tracking-widest mb-3">Matched Log Lines</h4>
                    <div className="bg-[#0d1117] border border-[#30363d] rounded-lg p-4 font-mono text-xs text-[#f85149] space-y-1 max-h-40 overflow-y-auto">
                      {result.matched_lines.map((line, i) => <div key={i}>{line}</div>)}
                    </div>
                  </div>
                )}

                {/* Fix */}
                <div>
                  <h4 className="text-[#8b949e] text-xs font-semibold uppercase tracking-widest mb-3">Suggested Remediation</h4>
                  <div className="bg-[#0d1117] rounded-lg border border-[#30363d] overflow-hidden shadow-inner">
                    <div className="px-4 py-2 border-b border-[#30363d] bg-[#161b22] text-[#8b949e] text-xs font-mono">Suggested Fix</div>
                    <div className="p-5 text-sm text-[#c9d1d9] whitespace-pre-wrap">{result.suggested_fix}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-[#8b949e] border-2 border-dashed border-[#30363d] rounded-xl bg-[#0d1117]/50 p-6 text-center">
                <TerminalSquare size={48} className="text-[#30363d] mb-4" />
                <p>Paste logs on the left and trigger analysis to diagnose the failure.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
