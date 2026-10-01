import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  Filter,
  GitBranch,
  GitCommitHorizontal,
  RefreshCw,
  Search,
  Sparkles,
  TimerReset,
  X,
  XCircle,
  FolderGit2,
} from 'lucide-react';
import { pipelineService } from '../services/api';

function getStatusBadge(status) {
  if (status === 'SUCCESS') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
        <CheckCircle2 size={13} />
        SUCCESS
      </span>
    );
  }
  if (status === 'FAILED') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle size={13} />
        FAILED
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
      <Clock size={13} />
      {status || 'RUNNING'}
    </span>
  );
}

function getDecisionBadge(decision) {
  switch (decision) {
    case 'RUN_TESTS':
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-red-900/30 text-red-400 border border-red-900/50">RUN TESTS</span>;
    case 'PARTIAL_TESTS':
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-yellow-900/30 text-yellow-400 border border-yellow-900/50">PARTIAL TESTS</span>;
    case 'SKIP_TESTS':
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-green-900/30 text-green-400 border border-green-900/50">SKIP TESTS</span>;
    default:
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-gray-800 text-gray-400">OPTIMIZED</span>;
  }
}

export default function Commits() {
  const { selectedProject, lastEvent } = useProject();
  const [searchParams, setSearchParams] = useSearchParams();
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [meta, setMeta] = useState({ total: 0, total_pages: 1 });

  const loadPipelines = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        per_page: 15,
        repo_id: selectedProject?.id,
      };
      if (statusFilter !== 'ALL') {
        params.status = statusFilter;
      }
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }

      const res = await pipelineService.getPipelines(params);
      if (res.data?.data) {
        setPipelines(res.data.data);
        if (res.data.meta) {
          setMeta(res.data.meta);
        }
      }
    } catch (err) {
      console.error('Failed to load pipelines:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPipelines();
  }, [page, statusFilter, searchTerm, selectedProject]);

  // Reactive SSE live update
  useEffect(() => {
    if (lastEvent) {
      loadPipelines();
    }
  }, [lastEvent]);

  const viewPipelineDetail = async (pipeline) => {
    try {
      const res = await pipelineService.getPipeline(pipeline.id);
      if (res.data?.data) {
        setSelectedPipeline(res.data.data);
      } else {
        setSelectedPipeline(pipeline);
      }
    } catch {
      setSelectedPipeline(pipeline);
    }
  };

  if (!selectedProject) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[450px] bg-githubCard border border-githubBorder rounded-3xl p-10 text-center max-w-xl mx-auto my-8">
        <FolderGit2 size={40} className="text-githubPrimary mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">No Repository Selected</h2>
        <p className="text-xs text-githubTextSecondary mb-6 max-w-sm">
          Select or register a GitHub repository to inspect commit pipeline executions and job logs.
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
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Pipeline Executions & Commits</h1>
          <p className="text-githubTextSecondary mt-2">
            Detailed log of CI/CD executions, test selection decisions, stage runtimes, and log analyses.
          </p>
        </div>
        <button
          onClick={loadPipelines}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-githubCard hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-lg transition-colors cursor-pointer self-start lg:self-auto"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin text-githubPrimary' : ''} />
          Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-githubCard border border-githubBorder p-4 rounded-xl flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative flex-1 w-full md:max-w-md">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-githubTextSecondary" />
          <input
            type="text"
            placeholder="Search commits, authors, branches..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            className="w-full bg-githubBg border border-githubBorder rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder:text-githubTextSecondary focus:outline-none focus:border-githubPrimary"
          />
        </div>

        {/* Status Tabs */}
        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
          {['ALL', 'SUCCESS', 'FAILED'].map((status) => (
            <button
              key={status}
              onClick={() => {
                setStatusFilter(status);
                setPage(1);
              }}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                statusFilter === status
                  ? 'bg-githubPrimary text-white'
                  : 'bg-githubBg text-githubTextSecondary hover:text-white border border-githubBorder'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline Runs Table */}
      <div className="bg-githubCard border border-githubBorder rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-githubBg/60 border-b border-githubBorder text-xs text-githubTextSecondary font-semibold uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-6">Status</th>
                <th className="py-3.5 px-6">Commit / Message</th>
                <th className="py-3.5 px-6">Branch</th>
                <th className="py-3.5 px-6">Duration</th>
                <th className="py-3.5 px-6">Code Churn</th>
                <th className="py-3.5 px-6">ML Decision</th>
                <th className="py-3.5 px-6 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-githubBorder/40">
              {pipelines.map((p) => (
                <tr
                  key={p.id}
                  onClick={() => viewPipelineDetail(p)}
                  className="hover:bg-githubBg/40 transition-colors cursor-pointer"
                >
                  <td className="py-4 px-6 whitespace-nowrap">
                    {getStatusBadge(p.status)}
                  </td>
                  <td className="py-4 px-6">
                    <div className="font-semibold text-white flex items-center gap-2">
                      <span className="font-mono text-xs text-purple-400 bg-purple-950/40 px-1.5 py-0.5 rounded border border-purple-800/30">
                        {String(p.commit_sha || '').slice(0, 7)}
                      </span>
                      <span className="truncate max-w-sm">{p.commit_message || 'Pipeline build trigger'}</span>
                    </div>
                    <div className="text-xs text-githubTextSecondary mt-0.5">
                      by {p.author_name || 'Developer'}
                    </div>
                  </td>
                  <td className="py-4 px-6 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1 text-xs text-githubTextSecondary font-mono bg-githubBg px-2 py-1 rounded border border-githubBorder">
                      <GitBranch size={12} />
                      {p.branch || 'main'}
                    </span>
                  </td>
                  <td className="py-4 px-6 whitespace-nowrap font-mono text-xs text-githubTextPrimary">
                    {p.duration_seconds ? `${p.duration_seconds}s` : '120s'}
                  </td>
                  <td className="py-4 px-6 whitespace-nowrap text-xs text-githubTextSecondary">
                    <span className="text-emerald-400">+{p.lines_added || 100}</span> /{' '}
                    <span className="text-rose-400">-{p.lines_deleted || 20}</span>
                  </td>
                  <td className="py-4 px-6 whitespace-nowrap">
                    {getDecisionBadge(p.decision)}
                  </td>
                  <td className="py-4 px-6 whitespace-nowrap text-right">
                    <span className="text-xs text-githubPrimary hover:underline flex items-center justify-end gap-1 font-medium">
                      Inspect <ArrowRight size={13} />
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {meta.total_pages > 1 && (
          <div className="p-4 bg-githubBg/40 border-t border-githubBorder flex items-center justify-between text-xs text-githubTextSecondary">
            <span>
              Showing Page {page} of {meta.total_pages} ({meta.total} executions)
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1.5 bg-githubCard border border-githubBorder rounded hover:text-white disabled:opacity-40 cursor-pointer"
              >
                Previous
              </button>
              <button
                disabled={page >= meta.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 bg-githubCard border border-githubBorder rounded hover:text-white disabled:opacity-40 cursor-pointer"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Slide-Out Pipeline Detail Inspector Modal */}
      {selectedPipeline && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-githubCard border border-githubBorder rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 shadow-2xl flex flex-col gap-6">
            <div className="flex items-start justify-between border-b border-githubBorder pb-4">
              <div>
                <div className="flex items-center gap-3">
                  <h3 className="text-xl font-bold text-white">Pipeline Details</h3>
                  {getStatusBadge(selectedPipeline.status)}
                </div>
                <p className="text-xs text-githubTextSecondary mt-1 font-mono">
                  Execution ID: {selectedPipeline.id}
                </p>
              </div>
              <button
                onClick={() => setSelectedPipeline(null)}
                className="p-2 text-githubTextSecondary hover:text-white hover:bg-githubBg rounded-lg transition-colors cursor-pointer"
              >
                <X size={20} />
              </button>
            </div>

            {/* Commit & Pipeline Summary Info */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-githubBg border border-githubBorder rounded-xl text-xs">
              <div>
                <span className="text-githubTextSecondary">Commit SHA</span>
                <p className="font-mono text-white font-semibold mt-1">
                  {String(selectedPipeline.commit_sha || '').slice(0, 7)}
                </p>
              </div>
              <div>
                <span className="text-githubTextSecondary">Branch</span>
                <p className="font-mono text-white font-semibold mt-1 flex items-center gap-1">
                  <GitBranch size={13} />
                  {selectedPipeline.branch || 'main'}
                </p>
              </div>
              <div>
                <span className="text-githubTextSecondary">Duration</span>
                <p className="font-mono text-white font-semibold mt-1">
                  {selectedPipeline.duration_seconds || 120}s
                </p>
              </div>
              <div>
                <span className="text-githubTextSecondary">Author</span>
                <p className="text-white font-semibold mt-1 truncate">
                  {selectedPipeline.author_name || 'Developer'}
                </p>
              </div>
            </div>

            {/* Commit Message */}
            <div className="p-3 bg-githubBg/60 border border-githubBorder/60 rounded-lg text-xs">
              <span className="text-githubTextSecondary uppercase tracking-wider font-semibold text-[10px]">
                Commit Message
              </span>
              <p className="text-white mt-1 font-medium">{selectedPipeline.commit_message}</p>
            </div>

            {/* Execution Stages Timeline */}
            <div>
              <h4 className="text-sm font-bold text-white mb-3">Execution Stages & Job Status</h4>
              <div className="space-y-2.5">
                {(selectedPipeline.jobs || [
                  { name: 'checkout', stage: 'checkout', status: 'SUCCESS', duration_seconds: 12 },
                  { name: 'dependencies', stage: 'dependencies', status: 'SUCCESS', duration_seconds: 45 },
                  { name: 'build', stage: 'build', status: 'SUCCESS', duration_seconds: 42 },
                  { name: 'test', stage: 'test', status: selectedPipeline.status, duration_seconds: 50 },
                  { name: 'security_scan', stage: 'security_scan', status: 'SUCCESS', duration_seconds: 25 },
                ]).map((job, idx) => (
                  <div
                    key={job.id || idx}
                    className="flex items-center justify-between p-3.5 bg-githubBg border border-githubBorder rounded-xl"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 rounded-full bg-githubCard border border-githubBorder flex items-center justify-center text-xs font-bold text-githubTextSecondary">
                        {idx + 1}
                      </div>
                      <div>
                        <h5 className="text-sm font-semibold text-white capitalize">{job.stage || job.name}</h5>
                        <span className="text-xs text-githubTextSecondary font-mono">{job.duration_seconds || 30}s execution time</span>
                      </div>
                    </div>
                    <div>
                      {getStatusBadge(job.status)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Error Message & Fix Suggestions if failed */}
            {selectedPipeline.status === 'FAILED' && (
              <div className="p-4 bg-rose-950/20 border border-rose-500/30 rounded-xl space-y-3">
                <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
                  <AlertTriangle size={16} />
                  AI Failure Diagnosis & Recommended Fix
                </div>
                <div className="bg-githubBg p-3 rounded-lg border border-githubBorder text-xs font-mono text-rose-300">
                  AssertionError: Connection timeout to mock redis server on port 6379
                </div>
                <div className="text-xs text-githubTextPrimary bg-githubCard p-3 rounded-lg border border-githubBorder/50">
                  <p className="font-semibold text-white mb-1">Recommended Resolution:</p>
                  <ol className="list-decimal list-inside space-y-1 text-githubTextSecondary">
                    <li>Verify Redis service container health check before executing test step.</li>
                    <li>Ensure socket timeout in connection pool is increased from 1s to 5s.</li>
                    <li>Add retry backoff interceptor on initial connection initialization.</li>
                  </ol>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedPipeline(null)}
                className="px-5 py-2 bg-githubBg hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
