import { useState } from 'react';
import {
  AlertTriangle,
  Bug,
  CheckCircle2,
  FileCode2,
  FileSearch,
  Lightbulb,
  Play,
  RefreshCw,
  Sparkles,
  Terminal,
  Zap,
} from 'lucide-react';
import { logsService } from '../services/api';

const SAMPLE_LOGS = {
  npm_eresolve: `npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR! Found: react@18.3.1
npm ERR! node_modules/react
npm ERR! Could not resolve dependency:
npm ERR! peer react@"^17.0.0" from legacy-ui-lib@2.1.0
npm ERR! Fix the upstream dependency conflict, or retry with --force / --legacy-peer-deps`,

  python_import: `Traceback (most recent call last):
  File "/app/services/worker/main.py", line 14, in <module>
    import asyncpg
ModuleNotFoundError: No module named 'asyncpg'
[ERROR] Process exited with status code 1 during build phase`,

  pytest_timeout: `============================= test session starts =============================
collected 42 items

tests/integration/test_pipeline.py::test_database_sync PASSED             [ 50%]
tests/integration/test_redis.py::test_cache_connection FAILED             [100%]

================================== FAILURES ===================================
___________________________ test_cache_connection ____________________________
asyncio.exceptions.TimeoutError: Connection timeout to Redis host at localhost:6379 after 10000ms`,

  docker_memory: `[FATAL] JavaScript heap out of memory
<--- Last few GCs --->
[1:0x55d28b0]    42050 ms: Mark-sweep 2045.2 (2080.5) -> 2038.1 (2080.5) MB, 142.1 / 0.0 ms  (average mu = 0.124, current mu = 0.051) allocation failure
[1:0x55d28b0]    42210 ms: Mark-sweep (reduce) 2039.4 (2080.5) -> 2038.5 (2080.5) MB, 159.2 / 0.0 ms
FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory`,
};

export default function Logs() {
  const [logText, setLogText] = useState(SAMPLE_LOGS.npm_eresolve);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!logText.trim()) return;

    try {
      setLoading(true);
      const res = await logsService.analyze({ logs: logText });
      if (res.data?.data) {
        setAnalysis(res.data.data);
      }
    } catch (err) {
      console.error('Log analysis failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = (key) => {
    setLogText(SAMPLE_LOGS[key]);
    setAnalysis(null);
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">AI Log Analyzer & Error Classifier</h1>
          <p className="text-githubTextSecondary mt-2">
            Parse raw CI/CD logs, isolate stack traces, classify error categories, and generate actionable fixes via the AI Rule Engine.
          </p>
        </div>
      </div>

      {/* Preset Log Samples Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-githubTextSecondary whitespace-nowrap font-medium flex items-center gap-1.5 mr-2">
          <Terminal size={14} /> Sample Scenarios:
        </span>
        <button
          onClick={() => handleLoadSample('npm_eresolve')}
          className="px-3 py-1.5 bg-githubCard hover:bg-githubBorder/60 border border-githubBorder rounded-lg text-githubTextPrimary transition-colors cursor-pointer whitespace-nowrap"
        >
          NPM Dependency Conflict (ERESOLVE)
        </button>
        <button
          onClick={() => handleLoadSample('python_import')}
          className="px-3 py-1.5 bg-githubCard hover:bg-githubBorder/60 border border-githubBorder rounded-lg text-githubTextPrimary transition-colors cursor-pointer whitespace-nowrap"
        >
          Python Module Import Error
        </button>
        <button
          onClick={() => handleLoadSample('pytest_timeout')}
          className="px-3 py-1.5 bg-githubCard hover:bg-githubBorder/60 border border-githubBorder rounded-lg text-githubTextPrimary transition-colors cursor-pointer whitespace-nowrap"
        >
          PyTest Socket Timeout
        </button>
        <button
          onClick={() => handleLoadSample('docker_memory')}
          className="px-3 py-1.5 bg-githubCard hover:bg-githubBorder/60 border border-githubBorder rounded-lg text-githubTextPrimary transition-colors cursor-pointer whitespace-nowrap"
        >
          Node.js Out of Memory
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Raw Log Input Console */}
        <div className="lg:col-span-7 bg-githubCard border border-githubBorder p-6 rounded-2xl flex flex-col gap-4 shadow-sm">
          <div className="flex items-center justify-between">
            <label className="text-sm font-bold text-white flex items-center gap-2">
              <Terminal size={16} className="text-githubPrimary" />
              Raw CI/CD Execution Log Output
            </label>
            <span className="text-xs font-mono text-githubTextSecondary">
              {logText.split('\n').length} lines
            </span>
          </div>

          <textarea
            value={logText}
            onChange={(e) => setLogText(e.target.value)}
            rows={14}
            className="w-full bg-[#0d1117] border border-githubBorder rounded-xl p-4 font-mono text-xs text-githubTextPrimary focus:border-githubPrimary focus:outline-none resize-y leading-relaxed"
            placeholder="Paste pipeline execution logs here..."
          />

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => {
                setLogText('');
                setAnalysis(null);
              }}
              className="px-4 py-2 bg-githubBg hover:bg-githubBorder/50 text-githubTextSecondary hover:text-white border border-githubBorder rounded-lg text-xs font-semibold transition-colors cursor-pointer"
            >
              Clear
            </button>
            <button
              onClick={handleAnalyze}
              disabled={loading || !logText.trim()}
              className="px-6 py-2.5 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold text-xs rounded-lg transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50 shadow-sm"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Analyzing Log Lines...' : 'Analyze with AI Rule Engine'}
            </button>
          </div>
        </div>

        {/* Analysis Output & Suggestions Display */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {analysis ? (
            <div className="bg-githubCard border border-githubBorder p-6 rounded-2xl flex flex-col gap-5">
              {/* Diagnosis Header */}
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-githubTextSecondary">
                    AI Diagnosis Result
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1">
                    {analysis.primary_error_type?.replace(/_/g, ' ') || 'General Build Failure'}
                  </h3>
                </div>
                <span className="px-2.5 py-1 rounded text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {Math.round(analysis.confidence * 100)}% Confidence
                </span>
              </div>

              {/* Error Category Pill */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-githubTextSecondary font-medium">Category:</span>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                  {analysis.category}
                </span>
                <span className="text-xs text-githubTextSecondary ml-auto font-mono">
                  {analysis.matches?.length || 1} rule match
                </span>
              </div>

              {/* Recommended Fix Box */}
              <div className="p-4 bg-githubBg border border-githubBorder rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-white">
                  <Lightbulb size={15} className="text-amber-400" />
                  Step-by-Step Resolution Strategy
                </div>
                <div className="text-xs text-githubTextSecondary whitespace-pre-line leading-relaxed font-sans bg-githubCard p-3 rounded-lg border border-githubBorder/50">
                  {analysis.recommended_fix}
                </div>
              </div>

              {/* Rule Match Details */}
              {analysis.matches?.length > 0 && (
                <div className="pt-2">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                    Engine Rule Information
                  </h4>
                  <div className="space-y-2 text-xs">
                    {analysis.matches.map((m, idx) => (
                      <div key={idx} className="p-3 bg-githubBg border border-githubBorder rounded-lg text-githubTextSecondary">
                        <div className="flex items-center justify-between text-[11px] text-githubTextPrimary font-mono">
                          <span className="font-semibold text-purple-400">Rule ID: {m.rule_id}</span>
                          <span className="text-emerald-400">{(m.confidence * 100).toFixed(0)}% Match</span>
                        </div>
                        <p className="mt-1 text-githubTextSecondary">{m.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-githubCard border border-githubBorder p-8 rounded-2xl text-center text-githubTextSecondary flex flex-col items-center justify-center min-h-[320px]">
              <FileSearch size={36} className="text-githubBorder mb-3" />
              <h4 className="text-sm font-semibold text-white">No Analysis Run Yet</h4>
              <p className="text-xs text-githubTextSecondary mt-1 max-w-xs">
                Click &quot;Analyze with AI Rule Engine&quot; to parse logs and generate failure classifications.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
