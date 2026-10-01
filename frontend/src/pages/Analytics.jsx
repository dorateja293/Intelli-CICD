import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Activity,
  AlertOctagon,
  CheckCircle2,
  Clock,
  Layers,
  Radio,
  RefreshCw,
  TrendingUp,
  XCircle,
  Zap,
  FolderGit2,
} from 'lucide-react';
import { analyticsService } from '../services/api';

const chartMargin = { top: 10, right: 10, bottom: 0, left: -15 };
const tooltipStyle = {
  backgroundColor: '#161b22',
  border: '1px solid #30363d',
  borderRadius: '8px',
  color: '#c9d1d9',
};

const CATEGORY_COLORS = ['#388bfd', '#f85149', '#d29922', '#2ea043', '#a371f7', '#8b949e'];

export default function Analytics() {
  const { selectedProject, lastEvent } = useProject();
  const [timeRange, setTimeRange] = useState(30);
  const [overview, setOverview] = useState(null);
  const [durations, setDurations] = useState(null);
  const [stages, setStages] = useState([]);
  const [failures, setFailures] = useState(null);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [livePulse, setLivePulse] = useState(false);

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const repoId = selectedProject?.id;
      const [overviewRes, durRes, stageRes, failRes, trendRes] = await Promise.allSettled([
        analyticsService.getAnalytics(timeRange, repoId),
        analyticsService.getDurations(repoId),
        analyticsService.getStages(repoId),
        analyticsService.getFailures(repoId),
        analyticsService.getTrends(timeRange, repoId),
      ]);

      if (overviewRes.status === 'fulfilled' && overviewRes.value.data?.data) {
        setOverview(overviewRes.value.data.data);
      }
      if (durRes.status === 'fulfilled' && durRes.value.data?.data) {
        setDurations(durRes.value.data.data);
      }
      if (stageRes.status === 'fulfilled' && stageRes.value.data?.data) {
        setStages(stageRes.value.data.data);
      }
      if (failRes.status === 'fulfilled' && failRes.value.data?.data) {
        setFailures(failRes.value.data.data);
      }
      if (trendRes.status === 'fulfilled' && trendRes.value.data?.data) {
        setTrends(trendRes.value.data.data);
      }
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedProject, timeRange]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  // Live SSE auto-refresh
  useEffect(() => {
    if (lastEvent) {
      setLivePulse(true);
      loadAnalytics();
      const timer = setTimeout(() => setLivePulse(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [lastEvent, loadAnalytics]);

  const failureCategories = failures?.category_distribution || [];

  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] bg-githubCard border border-githubBorder rounded-3xl p-10 text-center max-w-xl mx-auto my-8">
        <FolderGit2 size={40} className="text-githubPrimary mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">No Repository Selected</h2>
        <p className="text-xs text-githubTextSecondary mb-6 max-w-sm">
          Select or register a GitHub repository to view historical duration percentiles, DAG stage bottlenecks, and failure trends.
        </p>
        <Link
          to="/projects"
          className="px-5 py-2.5 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold text-xs rounded-xl transition-colors"
        >
          Browse Repositories
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Live SSE Pulse Indicator */}
      {livePulse && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center justify-between animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <Radio size={14} className="animate-pulse text-emerald-400" />
            <span className="font-semibold">Live Telemetry Synchronized!</span>
            <span className="text-githubTextSecondary">
              Metrics and percentile distributions updated automatically.
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400/80">SSE Stream Active</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-3xl font-bold text-white tracking-tight">CI/CD Performance & Bottleneck Analytics</h1>
            {selectedProject && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-githubCard border border-githubBorder text-githubPrimary font-mono font-semibold">
                {selectedProject.full_name || selectedProject.name}
              </span>
            )}
          </div>
          <p className="text-githubTextSecondary mt-2">
            Historical duration distributions, percentile latency analysis, stage breakdowns, and failure category trends.
          </p>
        </div>
        <div className="flex items-center gap-2.5 self-start lg:self-auto flex-wrap">
          {/* Time Range Filter Buttons */}
          <div className="flex items-center bg-githubCard border border-githubBorder rounded-lg p-1 text-xs">
            {[
              { label: '7d', value: 7 },
              { label: '14d', value: 14 },
              { label: '30d', value: 30 },
              { label: '90d', value: 90 },
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => setTimeRange(tab.value)}
                className={`px-3 py-1 rounded-md font-semibold transition-colors cursor-pointer ${
                  timeRange === tab.value
                    ? 'bg-githubPrimary text-white shadow-sm'
                    : 'text-githubTextSecondary hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <button
            onClick={loadAnalytics}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-githubCard hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-lg transition-colors cursor-pointer"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin text-githubPrimary' : ''} />
            Refresh Metrics
          </button>
        </div>
      </div>

      {/* Percentiles & Latency Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">P50 (Median)</p>
          <p className="text-2xl font-bold text-white mt-1.5">{durations?.p50 || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">50% completed in</span>
        </div>
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">P90 Duration</p>
          <p className="text-2xl font-bold text-amber-400 mt-1.5">{durations?.p90 || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">90% completed in</span>
        </div>
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">P95 Duration</p>
          <p className="text-2xl font-bold text-rose-400 mt-1.5">{durations?.p95 || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">Tail latency</span>
        </div>
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">Mean Duration</p>
          <p className="text-2xl font-bold text-white mt-1.5">{durations?.average || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">Average cycle time</span>
        </div>
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">Fastest Run</p>
          <p className="text-2xl font-bold text-emerald-400 mt-1.5">{durations?.min || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">Minimum recorded</span>
        </div>
        <div className="bg-githubCard border border-githubBorder p-4 rounded-xl">
          <p className="text-xs text-githubTextSecondary uppercase tracking-wider font-semibold">Slowest Run</p>
          <p className="text-2xl font-bold text-rose-400 mt-1.5">{durations?.max || 0}s</p>
          <span className="text-[10px] text-githubTextSecondary">Maximum recorded</span>
        </div>
      </div>

      {/* Main Charts: Stage Runtimes & Volume Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stage Performance Breakdown */}
        <div className="bg-githubCard border border-githubBorder rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Stage-by-Stage Average Duration</h2>
              <p className="text-xs text-githubTextSecondary mt-1">Average runtime in seconds per execution phase</p>
            </div>
            <Layers size={18} className="text-blue-400" />
          </div>

          <div className="h-64 w-full">
            {stages.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stages} margin={chartMargin}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                  <XAxis dataKey="stage" stroke="#8b949e" tickLine={false} />
                  <YAxis stroke="#8b949e" tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="avg_duration" name="Avg Runtime (sec)" fill="#388bfd" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-githubBorder rounded-xl text-githubTextSecondary">
                <Clock size={28} className="mb-2 opacity-50" />
                <p className="text-sm font-semibold text-white">No Stage Execution Data</p>
                <p className="text-xs mt-1">Execute GitHub Actions workflows to capture DAG stage runtimes.</p>
              </div>
            )}
          </div>
        </div>

        {/* Daily Volume Trends */}
        <div className="bg-githubCard border border-githubBorder rounded-xl p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-bold text-white">Execution Volume Trends</h2>
              <p className="text-xs text-githubTextSecondary mt-1">Daily success vs failure volume</p>
            </div>
            <TrendingUp size={18} className="text-emerald-400" />
          </div>

          <div className="h-64 w-full">
            {trends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={chartMargin}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                  <XAxis dataKey="date" stroke="#8b949e" tickLine={false} />
                  <YAxis stroke="#8b949e" tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="success" name="Passed" stackId="1" stroke="#2ea043" fill="#2ea043" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="failed" name="Failed" stackId="1" stroke="#f85149" fill="#f85149" fillOpacity={0.4} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 border border-dashed border-githubBorder rounded-xl text-githubTextSecondary">
                <TrendingUp size={28} className="mb-2 opacity-50" />
                <p className="text-sm font-semibold text-white">No Trend Data in Period</p>
                <p className="text-xs mt-1">Workflow volume over the last 14 days will be plotted here.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Failure Category Distribution & Stage Bottleneck Table */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Failure Categories Donut */}
        <div className="bg-githubCard border border-githubBorder rounded-xl p-6 flex flex-col">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-white">Failure Root Causes</h2>
            <p className="text-xs text-githubTextSecondary mt-1">Categorized errors from AI rule engine</p>
          </div>

          <div className="h-52 w-full">
            {failureCategories.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={failureCategories}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={5}
                    dataKey="count"
                    nameKey="category"
                  >
                    {failureCategories.map((entry, index) => (
                      <Cell key={entry.category} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4 border border-dashed border-githubBorder rounded-xl text-githubTextSecondary">
                <CheckCircle2 size={24} className="mb-2 text-emerald-400 opacity-70" />
                <p className="text-xs font-semibold text-white">0 Failures Recorded</p>
                <p className="text-[11px] mt-0.5">All recent pipeline executions passed cleanly.</p>
              </div>
            )}
          </div>

          <div className="space-y-2 mt-auto pt-4 border-t border-githubBorder/50">
            {failureCategories.map((item, index) => (
              <div key={item.category} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-githubTextSecondary">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} />
                  {item.category}
                </span>
                <span className="font-semibold text-white">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Stage Reliability & Bottlenecks Table */}
        <div className="lg:col-span-2 bg-githubCard border border-githubBorder rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-white">Stage Bottleneck & Reliability Summary</h2>
              <p className="text-xs text-githubTextSecondary mt-1">Stage runtime overhead and failure occurrence</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-githubBorder text-githubTextSecondary uppercase font-semibold">
                <tr>
                  <th className="pb-3 pr-4">Stage Name</th>
                  <th className="pb-3 px-4">Avg Duration</th>
                  <th className="pb-3 px-4">Executions</th>
                  <th className="pb-3 px-4">Failures</th>
                  <th className="pb-3 pl-4">Failure Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-githubBorder/40">
                {stages.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-6 text-center text-githubTextSecondary">
                      No stage executions recorded yet.
                    </td>
                  </tr>
                ) : (
                  stages.map((stg) => (
                    <tr key={stg.stage} className="hover:bg-githubBg/40 transition-colors">
                      <td className="py-3 pr-4 font-semibold text-white">{stg.stage}</td>
                      <td className="py-3 px-4 font-mono text-githubTextPrimary">{stg.avg_duration}s</td>
                      <td className="py-3 px-4 text-githubTextSecondary">{stg.total_executions}</td>
                      <td className="py-3 px-4 font-semibold text-rose-400">{stg.failure_count}</td>
                      <td className="py-3 pl-4 font-mono">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          stg.failure_rate > 15
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : stg.failure_rate > 5
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {stg.failure_rate}%
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
