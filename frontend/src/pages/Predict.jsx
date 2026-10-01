import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Gauge,
  GitCommitHorizontal,
  Info,
  MinusCircle,
  RefreshCw,
  Sparkles,
  TimerReset,
  Zap,
} from 'lucide-react';
import { predictorService } from '../services/api';

const initialForm = {
  files_changed: 8,
  lines_added: 180,
  lines_deleted: 45,
  previous_failures: 0,
  test_coverage: 78.5,
  is_merge_commit: 0,
  commit_message_length: 45,
  num_contributors_last_30d: 3,
  days_since_last_failure: 14,
};

export default function Predict() {
  const [formValues, setFormValues] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Load ML model status
    predictorService.getStatus().then((res) => {
      if (res.data?.data) {
        setModelStatus(res.data.data);
      }
    }).catch(console.error);

    // Initial prediction on load
    runPrediction(initialForm);
  }, []);

  const runPrediction = async (values) => {
    try {
      setLoading(true);
      const res = await predictorService.predict({
        files_changed: Number(values.files_changed),
        lines_added: Number(values.lines_added),
        lines_deleted: Number(values.lines_deleted),
        previous_failures: Number(values.previous_failures),
        test_coverage: Number(values.test_coverage),
        is_merge_commit: Number(values.is_merge_commit ? 1 : 0),
        commit_message_length: Number(values.commit_message_length),
        num_contributors_last_30d: Number(values.num_contributors_last_30d),
        days_since_last_failure: Number(values.days_since_last_failure),
      });

      if (res.data?.data) {
        setPrediction(res.data.data);
      }
    } catch (err) {
      console.error('Prediction failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormValues((curr) => ({
      ...curr,
      [name]: type === 'checkbox' ? (checked ? 1 : 0) : value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    runPrediction(formValues);
  };

  const churn = Number(formValues.lines_added) + Number(formValues.lines_deleted);

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">ML Predictive CI Optimization</h1>
          <p className="text-githubTextSecondary mt-2">
            Evaluate commit risk using the trained RandomForest model to dynamically select optimal test suites.
          </p>
        </div>
        {modelStatus && (
          <div className="flex items-center gap-3 px-4 py-2 bg-githubCard border border-githubBorder rounded-xl text-xs">
            <BrainCircuit size={16} className="text-purple-400" />
            <div>
              <span className="text-githubTextSecondary">Model: </span>
              <span className="text-white font-mono font-semibold">{modelStatus.model_type}</span>
              <span className="text-emerald-400 ml-2 font-mono">
                ({(modelStatus.evaluation?.accuracy * 100).toFixed(1)}% Acc)
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Parameters Form */}
        <div className="lg:col-span-7 bg-githubCard border border-githubBorder p-6 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between border-b border-githubBorder pb-4 mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Commit Feature Vector</h2>
              <p className="text-xs text-githubTextSecondary mt-0.5">Parameters evaluated by the machine learning pipeline</p>
            </div>
            <span className="text-xs font-mono text-purple-400 bg-purple-950/40 px-2 py-1 rounded border border-purple-800/30">
              Code Churn: {churn} lines
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Files Changed</label>
                <input
                  type="number"
                  name="files_changed"
                  min="1"
                  max="100"
                  value={formValues.files_changed}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Lines Added (+)</label>
                <input
                  type="number"
                  name="lines_added"
                  min="0"
                  value={formValues.lines_added}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Lines Deleted (-)</label>
                <input
                  type="number"
                  name="lines_deleted"
                  min="0"
                  value={formValues.lines_deleted}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Test Coverage (%)</label>
                <input
                  type="number"
                  name="test_coverage"
                  min="0"
                  max="100"
                  step="0.5"
                  value={formValues.test_coverage}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Previous Build Failures</label>
                <input
                  type="number"
                  name="previous_failures"
                  min="0"
                  max="20"
                  value={formValues.previous_failures}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Days Since Last Failure</label>
                <input
                  type="number"
                  name="days_since_last_failure"
                  min="0"
                  max="365"
                  value={formValues.days_since_last_failure}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
              <div>
                <label className="block font-medium text-githubTextPrimary mb-1.5">Contributors in Last 30 Days</label>
                <input
                  type="number"
                  name="num_contributors_last_30d"
                  min="1"
                  max="50"
                  value={formValues.num_contributors_last_30d}
                  onChange={handleChange}
                  className="w-full bg-githubBg border border-githubBorder rounded-lg px-3 py-2 text-white focus:border-githubPrimary focus:outline-none font-mono"
                />
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <label className="flex items-center gap-2 text-githubTextPrimary cursor-pointer">
                <input
                  type="checkbox"
                  name="is_merge_commit"
                  checked={!!formValues.is_merge_commit}
                  onChange={handleChange}
                  className="rounded bg-githubBg border-githubBorder text-githubPrimary focus:ring-0 w-4 h-4 cursor-pointer"
                />
                Is Branch Merge Commit
              </label>

              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold rounded-lg transition-colors flex items-center gap-2 cursor-pointer shadow-sm"
              >
                <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
                {loading ? 'Evaluating Model...' : 'Run ML Prediction'}
              </button>
            </div>
          </form>
        </div>

        {/* Prediction Results Display */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          {prediction ? (
            <div className="bg-githubCard border border-githubBorder p-6 rounded-2xl flex flex-col gap-5">
              {/* Risk Gauge Header */}
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">
                    Failure Risk Assessment
                  </span>
                  <div className="flex items-center gap-3 mt-1.5">
                    <h3 className={`text-2xl font-black ${
                      prediction.risk_level === 'HIGH'
                        ? 'text-rose-400'
                        : prediction.risk_level === 'MEDIUM'
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    }`}>
                      {prediction.risk_level} RISK
                    </h3>
                    <span className="text-xs px-2 py-0.5 rounded font-mono font-semibold bg-githubBg border border-githubBorder text-githubTextSecondary">
                      {Math.round(prediction.failure_probability * 100)}% Failure Prob
                    </span>
                  </div>
                </div>

                <div className={`p-3 rounded-xl border ${
                  prediction.risk_level === 'HIGH'
                    ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    : prediction.risk_level === 'MEDIUM'
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                    : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                }`}>
                  {prediction.risk_level === 'HIGH' ? (
                    <AlertTriangle size={24} />
                  ) : prediction.risk_level === 'MEDIUM' ? (
                    <MinusCircle size={24} />
                  ) : (
                    <CheckCircle2 size={24} />
                  )}
                </div>
              </div>

              {/* Recommended Decision Banner */}
              <div className="p-4 bg-githubBg border border-githubBorder rounded-xl">
                <span className="text-[11px] text-githubTextSecondary uppercase tracking-wider font-semibold">
                  Intelligent CI Action
                </span>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-base font-bold text-white font-mono">
                    {prediction.decision.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs font-semibold text-emerald-400">
                    +{prediction.time_saved_minutes} min saved
                  </span>
                </div>
                <p className="text-xs text-githubTextSecondary mt-2">
                  Estimated duration: <span className="text-white font-mono">{prediction.estimated_duration_seconds}s</span> (vs 18m baseline)
                </p>
              </div>

              {/* Risk Drivers */}
              <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2">
                  Key Risk Drivers Identified
                </h4>
                <ul className="space-y-1.5 text-xs text-githubTextSecondary">
                  {prediction.key_risk_drivers?.map((driver, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-rose-400 mt-0.5">•</span>
                      <span>{driver}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Optimization Recommendations */}
              {prediction.optimization_tips?.length > 0 && (
                <div className="pt-3 border-t border-githubBorder/50">
                  <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Sparkles size={13} />
                    Optimization Recommendation
                  </h4>
                  <ul className="space-y-1.5 text-xs text-githubTextSecondary">
                    {prediction.optimization_tips.map((tip, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-purple-400 mt-0.5">✓</span>
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-githubCard border border-githubBorder p-8 rounded-2xl text-center text-githubTextSecondary">
              <BrainCircuit size={32} className="mx-auto text-githubBorder mb-3" />
              <p className="text-sm font-medium">Click &quot;Run ML Prediction&quot; to evaluate commit risk.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
