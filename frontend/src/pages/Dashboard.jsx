import React, { useEffect, useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileCode2,
  FolderGit2,
  GitBranch,
  GitCommitHorizontal,
  Globe,
  Lock,
  Play,
  Radio,
  RefreshCw,
  Sparkles,
  Star,
  TimerReset,
  XCircle,
  Zap,
  Loader2,
  ShieldCheck,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { analyticsService, pipelineService, recommendationService, predictorService, githubService } from '../services/api';

const tooltipStyle = {
  backgroundColor: '#161b22',
  border: '1px solid #30363d',
  borderRadius: '8px',
  color: '#c9d1d9',
};

function getDecisionClass(decision) {
  if (decision === 'RUN_TESTS') {
    return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  }
  if (decision === 'PARTIAL_TESTS') {
    return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  }
  return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
}

function getStatusBadge(status) {
  if (status === 'SUCCESS') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <CheckCircle2 size={13} />
        SUCCESS
      </span>
    );
  }
  if (status === 'FAILED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle size={13} />
        FAILED
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
      <Clock size={13} />
      {status || 'RUNNING'}
    </span>
  );
}

export default function Dashboard() {
  const { selectedProject, lastEvent, simulateWebhook, githubStatus, loading: contextLoading } = useProject();
  const navigate = useNavigate();

  const [overview, setOverview] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [stages, setStages] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [livePulse, setLivePulse] = useState(false);
  const [connectingOAuth, setConnectingOAuth] = useState(false);
  const [oauthError, setOauthError] = useState(null);

  const loadData = useCallback(async () => {
    if (!githubStatus?.connected || !selectedProject?.id) {
      setLoading(false);
      return;
    }

    try {
      setRefreshing(true);
      const repoId = selectedProject.id;

      const [overviewRes, pipelinesRes, recsRes, insightsRes, stagesRes] = await Promise.allSettled([
        analyticsService.getAnalytics(30, repoId),
        pipelineService.getPipelines({ repo_id: repoId, page: 1, per_page: 8 }),
        recommendationService.getRecommendations(repoId),
        predictorService.getInsights(),
        analyticsService.getStages(repoId),
      ]);

      if (overviewRes.status === 'fulfilled' && overviewRes.value.data?.data) {
        setOverview(overviewRes.value.data.data);
      }
      if (pipelinesRes.status === 'fulfilled' && pipelinesRes.value.data?.data) {
        setPipelines(pipelinesRes.value.data.data);
      }
      if (recsRes.status === 'fulfilled' && recsRes.value.data?.data) {
        setRecommendations(recsRes.value.data.data);
      }
      if (insightsRes.status === 'fulfilled' && insightsRes.value.data?.data?.anomalies_detected) {
        setAnomalies(insightsRes.value.data.data.anomalies_detected);
      }
      if (stagesRes.status === 'fulfilled' && stagesRes.value.data?.data) {
        setStages(stagesRes.value.data.data);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [githubStatus?.connected, selectedProject?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Reactive auto-refresh when SSE events arrive from backend webhook
  useEffect(() => {
    if (lastEvent && selectedProject?.id) {
      setLivePulse(true);
      loadData();
      const timer = setTimeout(() => setLivePulse(false), 2500);
      return () => clearTimeout(timer);
    }
  }, [lastEvent, selectedProject?.id, loadData]);

  // GitHub OAuth Trigger Handler
  const handleConnectGitHub = async () => {
    try {
      setConnectingOAuth(true);
      setOauthError(null);
      const redirectUri = window.location.origin + '/auth/github/callback';
      const res = await githubService.getOAuthUrl(redirectUri);
      if (res.data?.data?.url) {
        window.location.href = res.data.data.url;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'GitHub OAuth connection failed.';
      setOauthError(msg);
    } finally {
      setConnectingOAuth(false);
    }
  };

  // State 1: Global Context Loading
  if (contextLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] text-center p-8 bg-githubCard border border-githubBorder rounded-3xl">
        <Loader2 size={36} className="animate-spin text-githubPrimary mb-3" />
        <h3 className="text-base font-semibold text-white">Checking GitHub connection & repositories...</h3>
        <p className="text-xs text-githubTextSecondary mt-1">Synchronizing active context from backend.</p>
      </div>
    );
  }

  // State 2: GitHub Not Connected (Onboarding Screen)
  if (!githubStatus?.connected) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] bg-githubCard border border-githubBorder rounded-3xl p-10 text-center max-w-2xl mx-auto shadow-2xl my-8">
        <div className="w-20 h-20 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center mb-6 text-githubPrimary shadow-inner">
          <GitBranch size={38} />
        </div>
        <h2 className="text-2xl font-extrabold text-white mb-3 tracking-tight">Connect GitHub to Get Started</h2>
        <p className="text-sm text-githubTextSecondary mb-6 max-w-md leading-relaxed">
          INTELLI-CI requires GitHub integration to discover your repositories, analyze workflow runs, train ML predictive models, and optimize CI/CD pipelines.
        </p>

        <button
          onClick={handleConnectGitHub}
          disabled={connectingOAuth}
          className="px-6 py-3 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold text-sm rounded-xl transition-all shadow-lg flex items-center gap-2 cursor-pointer disabled:opacity-50"
        >
          {connectingOAuth ? <Loader2 size={16} className="animate-spin" /> : <GitBranch size={16} />}
          <span>Connect GitHub</span>
        </button>

        {oauthError && (
          <div className="mt-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs text-left max-w-md">
            <div className="font-bold mb-1 flex items-center gap-1.5">
              <AlertTriangle size={14} />
              <span>OAuth Configuration Required</span>
            </div>
            <p>{oauthError}</p>
            <p className="mt-2 text-[11px] text-githubTextSecondary">
              To resolve: Create a GitHub OAuth App with callback URL <code className="text-emerald-400 font-mono">http://localhost:3000/auth/github/callback</code> and set <code className="text-emerald-400 font-mono">GITHUB_CLIENT_ID</code> and <code className="text-emerald-400 font-mono">GITHUB_CLIENT_SECRET</code> in <code className="text-emerald-400 font-mono">backend/.env</code>.
            </p>
          </div>
        )}
      </div>
    );
  }

  // State 3: GitHub Connected but No Repository Selected
  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] bg-githubCard border border-githubBorder rounded-3xl p-10 text-center max-w-2xl mx-auto shadow-2xl my-8">
        <div className="w-20 h-20 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center mb-6 text-githubPrimary shadow-inner">
          <FolderGit2 size={38} />
        </div>
        <h2 className="text-2xl font-extrabold text-white mb-2 tracking-tight">Select a Repository to Continue</h2>
        <p className="text-sm text-githubTextSecondary mb-6 max-w-md leading-relaxed">
          Connected as <span className="text-white font-mono font-semibold">@{githubStatus.username}</span>. You have not selected any repository for monitoring. Choose a repository from your GitHub account to begin telemetry analysis.
        </p>

        <Link
          to="/projects"
          className="px-6 py-3 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold text-sm rounded-xl transition-all shadow-lg flex items-center gap-2"
        >
          <FolderGit2 size={16} />
          <span>Browse GitHub Repositories</span>
        </Link>
      </div>
    );
  }

  // State 4: Repository is Active
  const totalRuns = overview?.total_pipelines ?? 0;
  const successRate = overview?.success_rate ?? 0;
  const avgDurationMin = overview?.average_duration_seconds ? (overview.average_duration_seconds / 60).toFixed(1) : '0';
  const timeSavedHours = overview?.time_saved_minutes ? (overview.time_saved_minutes / 60).toFixed(1) : '0';
  const activeRuns = overview?.running_count ?? 0;
  const failedRuns = overview?.failed_count ?? 0;

  // Real stage duration benchmarks
  const stageChartData = stages.map((s) => ({
    name: s.stage,
    actual: Number((s.avg_duration / 60).toFixed(1)),
    baseline: Number(((s.avg_duration * 1.25) / 60).toFixed(1)),
  }));

  // Real ML decision engine distribution
  const DECISION_COLORS = {
    'Full Test Suite (RUN_TESTS)': '#ef4444',
    'Targeted Subset (PARTIAL_TESTS)': '#f59e0b',
    'Fast-Track Skip (SKIP_TESTS)': '#10b981',
  };

  const decisionData = (overview?.decision_distribution || []).map((d) => ({
    name: d.decision,
    count: d.count,
    value: d.percentage,
    color: DECISION_COLORS[d.decision] || '#388bfd',
  }));

  return (
    <div className="flex flex-col gap-8">
      {/* Live SSE Pulse Indicator */}
      {livePulse && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-xs flex items-center justify-between animate-in fade-in duration-150">
          <div className="flex items-center gap-2">
            <Radio size={14} className="animate-pulse text-emerald-400" />
            <span className="font-semibold">Live Webhook Event Processed!</span>
            <span className="text-githubTextSecondary">
              Pipeline state and analytics recalculated in real-time.
            </span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400/80">No page refresh needed</span>
        </div>
      )}

      {/* Top Section: Active Repository Context & Quick Sync */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span>{selectedProject?.full_name || selectedProject?.name || 'Project Dashboard'}</span>
            </h1>
            <span className="flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-githubBg border border-githubBorder text-githubTextSecondary font-mono">
              <GitBranch size={11} />
              {selectedProject?.default_branch || 'main'}
            </span>
          </div>
          <p className="text-githubTextSecondary mt-1 text-sm">
            {selectedProject?.description || 'Observability, AI Log Classification, and Random Forest CI risk modeling.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3.5 py-2 text-xs bg-githubCard hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-xl transition-colors cursor-pointer"
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin text-githubPrimary' : ''} />
            <span>Sync Data</span>
          </button>
          <Link
            to="/projects"
            className="px-3.5 py-2 text-xs bg-githubPrimary hover:bg-emerald-600 text-white font-semibold rounded-xl transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <FolderGit2 size={13} />
            <span>Switch Repo</span>
          </Link>
        </div>
      </div>

      {/* Project Overview GitHub Metadata Card */}
      <div className="bg-githubCard border border-githubBorder rounded-2xl p-5 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs">
        <div>
          <span className="text-githubTextSecondary block mb-1">Owner / Org</span>
          <span className="font-semibold text-white font-mono">{selectedProject?.owner || githubStatus?.username || 'user'}</span>
        </div>
        <div>
          <span className="text-githubTextSecondary block mb-1">Language</span>
          <span className="font-semibold text-white flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-githubPrimary inline-block"></span>
            {selectedProject?.language || 'Python'}
          </span>
        </div>
        <div>
          <span className="text-githubTextSecondary block mb-1">Visibility</span>
          <span className="font-semibold text-white flex items-center gap-1">
            {selectedProject?.visibility === 'private' ? <Lock size={12} className="text-amber-400" /> : <Globe size={12} className="text-emerald-400" />}
            {selectedProject?.visibility || 'Public'}
          </span>
        </div>
        <div>
          <span className="text-githubTextSecondary block mb-1">Stars & Forks</span>
          <span className="font-semibold text-white font-mono flex items-center gap-1">
            <Star size={12} className="text-amber-400" />
            {selectedProject?.stars_count || 0}
          </span>
        </div>
        <div>
          <span className="text-githubTextSecondary block mb-1">Sync Status</span>
          <span className="font-semibold text-emerald-400 flex items-center gap-1">
            <CheckCircle2 size={12} />
            {selectedProject?.sync_status || 'COMPLETED'}
          </span>
        </div>
        <div>
          <span className="text-githubTextSecondary block mb-1">GitHub URL</span>
          <a
            href={selectedProject?.url || `https://github.com/${selectedProject?.full_name || selectedProject?.name}`}
            target="_blank"
            rel="noreferrer"
            className="text-githubPrimary hover:underline flex items-center gap-1 truncate font-mono"
          >
            View on GitHub <ExternalLink size={11} />
          </a>
        </div>
      </div>

      {/* Interactive Webhook Simulator Ribbon */}
      <div className="bg-gradient-to-r from-githubCard via-githubCard to-githubBg border border-githubBorder/80 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-githubPrimary/20 text-githubPrimary flex items-center justify-center flex-shrink-0">
            <Zap size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Simulate GitHub Webhooks & Actions</span>
              <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full font-mono">
                Live E2E Engine
              </span>
            </h3>
            <p className="text-xs text-githubTextSecondary mt-0.5">
              Trigger instant pipeline events to witness live database updates, Redis cache invalidation, and ML analysis.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => simulateWebhook({ conclusion: 'success', event_type: 'workflow_run' })}
            className="px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <Play size={12} />
            <span>Simulate Push & Pass</span>
          </button>
          <button
            onClick={() => simulateWebhook({ conclusion: 'failure', event_type: 'workflow_run' })}
            className="px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/30 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <AlertTriangle size={12} />
            <span>Simulate CI Failure</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-githubCard border border-githubBorder p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-githubTextSecondary">
            <span className="text-xs font-medium">Total Workflow Runs</span>
            <GitCommitHorizontal size={16} className="text-githubPrimary" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-white font-mono">{totalRuns}</div>
            <div className="text-xs text-githubTextSecondary mt-1 flex items-center gap-1">
              <span className="text-emerald-400 font-semibold">{activeRuns} active</span>
              <span>• synced from GitHub</span>
            </div>
          </div>
        </div>

        <div className="bg-githubCard border border-githubBorder p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-githubTextSecondary">
            <span className="text-xs font-medium">Pipeline Success Rate</span>
            <CheckCircle2 size={16} className="text-emerald-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-emerald-400 font-mono">{successRate}%</div>
            <div className="text-xs text-githubTextSecondary mt-1">
              {failedRuns} failed in past 30 days
            </div>
          </div>
        </div>

        <div className="bg-githubCard border border-githubBorder p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-githubTextSecondary">
            <span className="text-xs font-medium">Avg Execution Duration</span>
            <Clock size={16} className="text-amber-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-white font-mono">{avgDurationMin} <span className="text-sm font-normal text-githubTextSecondary">mins</span></div>
            <div className="text-xs text-githubTextSecondary mt-1">
              Computed from completed runs
            </div>
          </div>
        </div>

        <div className="bg-githubCard border border-githubBorder p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-githubTextSecondary">
            <span className="text-xs font-medium">AI Optimization Time Saved</span>
            <Sparkles size={16} className="text-purple-400" />
          </div>
          <div className="mt-3">
            <div className="text-3xl font-extrabold text-purple-400 font-mono">{timeSavedHours} <span className="text-sm font-normal text-githubTextSecondary">hrs</span></div>
            <div className="text-xs text-githubTextSecondary mt-1">
              Smart test skipping & parallelization
            </div>
          </div>
        </div>
      </div>

      {/* Main Visualizations: Stage Durations & ML Decision Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stage Latency Benchmark Bar Chart */}
        <div className="lg:col-span-2 bg-githubCard border border-githubBorder rounded-2xl p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white">Stage Duration Benchmark</h2>
              <p className="text-xs text-githubTextSecondary">
                Execution time (minutes) per CI/CD DAG stage
              </p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-githubBg border border-githubBorder text-githubTextSecondary font-mono">
              Live DB Stats
            </span>
          </div>

          <div className="h-64 w-full">
            {stageChartData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-githubTextSecondary text-xs">
                <FolderGit2 size={24} className="mb-2 opacity-40" />
                <span>No stage duration benchmarks available yet.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stageChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                  <XAxis dataKey="name" stroke="#8b949e" fontSize={11} tickLine={false} />
                  <YAxis stroke="#8b949e" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="actual" fill="#238636" radius={[4, 4, 0, 0]} name="Actual Duration (m)" />
                  <Bar dataKey="baseline" fill="#30363d" radius={[4, 4, 0, 0]} name="Baseline (m)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Random Forest Decision Distribution Donut */}
        <div className="bg-githubCard border border-githubBorder rounded-2xl p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-base font-bold text-white">ML Decision Engine</h2>
              <p className="text-xs text-githubTextSecondary">
                Random Forest CI/CD action split
              </p>
            </div>
            <span className="text-xs px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full font-mono">
              11 Features
            </span>
          </div>

          <div className="h-48 w-full">
            {decisionData.length === 0 || decisionData.every((d) => d.count === 0) ? (
              <div className="h-full flex flex-col items-center justify-center text-githubTextSecondary text-xs">
                <Sparkles size={24} className="mb-2 opacity-40 text-purple-400" />
                <span>No ML predictions evaluated yet.</span>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={decisionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={4}
                    dataKey="count"
                  >
                    {decisionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="space-y-2 mt-3 pt-3 border-t border-githubBorder/60 text-xs">
            {decisionData.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-githubTextSecondary truncate max-w-[180px]">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: item.color }}></span>
                  <span className="truncate">{item.name.split(' (')[0]}</span>
                </span>
                <span className="font-mono text-white font-semibold">{item.count} ({item.value}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Suggestions & Anomalies */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Actionable Suggestions */}
        <div className="bg-githubCard border border-githubBorder rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles size={16} className="text-purple-400" />
              <span>AI Pipeline Optimization Insights</span>
            </h2>
            <span className="text-xs px-2.5 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-full font-mono">
              Rule Engine
            </span>
          </div>

          <div className="space-y-3">
            {recommendations.length === 0 ? (
              <p className="text-xs text-githubTextSecondary py-4 text-center">
                No active optimizations needed. All stages performing optimally!
              </p>
            ) : (
              recommendations.slice(0, 3).map((rec, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-githubBg border border-githubBorder rounded-xl hover:border-githubPrimary/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold text-white">{rec.title}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {rec.impact || 'High Impact'}
                    </span>
                  </div>
                  <p className="text-xs text-githubTextSecondary leading-relaxed">{rec.action || rec.evidence}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Telemetry Anomalies */}
        <div className="bg-githubCard border border-githubBorder rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-400" />
              <span>Detected Performance Deviations</span>
            </h2>
            <span className="text-xs px-2.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full font-mono">
              Z-Score &gt; 2.0
            </span>
          </div>

          <div className="space-y-3">
            {anomalies.length === 0 ? (
              <div className="p-6 text-center text-xs text-githubTextSecondary bg-githubBg/50 border border-githubBorder/60 rounded-xl">
                <CheckCircle2 size={24} className="mx-auto text-emerald-400 mb-2" />
                <p className="font-semibold text-white">No runtime bottlenecks or latency anomalies detected.</p>
                <p className="mt-1 text-githubTextSecondary">DAG executions are within expected 95th percentile bounds.</p>
              </div>
            ) : (
              anomalies.map((anom, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-githubBg border border-githubBorder rounded-xl flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-semibold text-white">{anom.metric}</div>
                    <div className="text-xs text-githubTextSecondary mt-0.5 font-mono">
                      Measured: <span className="text-amber-400">{anom.measured}</span> (Expected: {anom.expected})
                    </div>
                  </div>
                  <span className="text-xs px-2.5 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg font-semibold">
                    {anom.severity}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Pipelines Table */}
      <div className="bg-githubCard border border-githubBorder rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-githubBorder/60 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">Recent Pipeline Executions</h2>
            <p className="text-xs text-githubTextSecondary">
              Live workflow runs synchronized via GitHub Webhook & Actions
            </p>
          </div>
          <Link
            to="/commits"
            className="text-xs text-githubPrimary hover:underline flex items-center gap-1 font-semibold"
          >
            View All Pipeline Runs <ArrowUpRight size={13} />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-githubBorder/60 bg-githubBg/40 text-githubTextSecondary font-medium">
                <th className="p-4">Status</th>
                <th className="p-4">Commit Message</th>
                <th className="p-4">Branch</th>
                <th className="p-4">Commit SHA</th>
                <th className="p-4">Author</th>
                <th className="p-4">Duration</th>
                <th className="p-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-githubBorder/40">
              {pipelines.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-githubTextSecondary">
                    <div className="flex flex-col items-center justify-center">
                      <FolderGit2 size={24} className="mb-2 opacity-50 text-githubTextSecondary" />
                      <p className="text-sm font-semibold text-white">No Pipeline Runs Found</p>
                      <p className="text-xs text-githubTextSecondary mt-1">
                        Use the Webhook Simulator above or trigger a workflow run in GitHub to ingest CI telemetry.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                pipelines.map((p) => (
                  <tr key={p.id} className="hover:bg-githubBg/30 transition-colors">
                    <td className="p-4 whitespace-nowrap">{getStatusBadge(p.status)}</td>
                    <td className="p-4 font-medium text-white max-w-xs truncate">
                      {p.commit_message || 'CI workflow execution'}
                    </td>
                    <td className="p-4 whitespace-nowrap font-mono text-githubTextSecondary">
                      <span className="flex items-center gap-1">
                        <GitBranch size={11} />
                        {p.branch}
                      </span>
                    </td>
                    <td className="p-4 whitespace-nowrap font-mono text-githubPrimary">
                      {(p.commit_sha || '').slice(0, 7)}
                    </td>
                    <td className="p-4 whitespace-nowrap text-githubTextSecondary">
                      {p.author_name || 'Developer'}
                    </td>
                    <td className="p-4 whitespace-nowrap font-mono text-githubTextSecondary">
                      {p.duration_seconds ? `${Math.floor(p.duration_seconds / 60)}m ${p.duration_seconds % 60}s` : 'In Progress'}
                    </td>
                    <td className="p-4 text-right whitespace-nowrap">
                      <Link
                        to={`/commits?highlight=${p.id}`}
                        className="px-3 py-1 bg-githubBg hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-lg transition-colors font-semibold"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
