import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import { githubService, projectService } from '../services/api';
import {
  FolderGit2,
  GitBranch,
  Star,
  GitFork,
  ExternalLink,
  RefreshCw,
  Search,
  CheckCircle,
  AlertCircle,
  Loader2,
  Lock,
  Globe,
  Sparkles,
  Zap,
  ArrowRight,
  Plus,
  Play,
  AlertTriangle,
} from 'lucide-react';

export default function Projects() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { projects, selectedProject, setSelectedProject, githubStatus, fetchGithubStatus, fetchProjects, simulateWebhook } = useProject();

  const [activeTab, setActiveTab] = useState('browse'); // 'browse' | 'registered'
  const [githubRepos, setGithubRepos] = useState([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [syncingRepoId, setSyncingRepoId] = useState(null);
  const [syncProgress, setSyncProgress] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [toastType, setToastType] = useState('info'); // 'info' | 'error'

  useEffect(() => {
    if (searchParams.get('connected') === 'true') {
      setToastMessage('✓ GitHub OAuth connected successfully!');
      setToastType('info');
      fetchGithubStatus();
      loadGitHubRepos();
      setTimeout(() => setToastMessage(null), 4000);
    }
  }, [searchParams]);

  // Fetch GitHub repos available to select
  const loadGitHubRepos = async () => {
    if (!githubStatus?.connected) {
      setGithubRepos([]);
      return;
    }
    try {
      setLoadingRepos(true);
      const res = await githubService.getRepositories({ search: searchQuery });
      setGithubRepos(res.data?.data || []);
    } catch (err) {
      console.error('Failed to load GitHub repositories:', err);
    } finally {
      setLoadingRepos(false);
    }
  };

  useEffect(() => {
    if (githubStatus?.connected) {
      loadGitHubRepos();
    }
  }, [searchQuery, githubStatus?.connected]);

  // Connect GitHub OAuth Handler
  const handleConnectGitHub = async () => {
    try {
      const redirectUri = window.location.origin + '/auth/github/callback';
      const res = await githubService.getOAuthUrl(redirectUri);
      if (res.data?.data?.url) {
        window.location.href = res.data.data.url;
      }
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Error connecting GitHub.';
      setToastMessage(msg);
      setToastType('error');
    }
  };

  // Select and Register Repository
  const handleSelectRepository = async (repo) => {
    try {
      setSyncingRepoId(repo.name);
      setSyncProgress({
        step: 1,
        text: `Connecting repository ${repo.full_name || repo.name}...`,
      });

      const ownerName = typeof repo.owner === 'string' ? repo.owner : (repo.owner?.login || githubStatus?.username || 'user');
      const fullName = repo.full_name || `${ownerName}/${repo.name}`;
      const repoUrl = repo.html_url || `https://github.com/${fullName}`;

      const payload = {
        name: repo.name,
        owner: ownerName,
        full_name: fullName,
        url: repoUrl,
        default_branch: repo.default_branch || 'main',
        language: repo.language || 'Python',
        description: repo.description || 'Synchronized Project',
        visibility: repo.private ? 'private' : 'public',
        stars_count: repo.stargazers_count || 0,
        forks_count: repo.forks_count || 0,
        github_repo_id: repo.id,
      };

      const res = await githubService.selectRepository(payload);
      const registered = res.data?.data?.repository;

      setSyncProgress({
        step: 3,
        text: 'Fetching workflows and pipeline history...',
      });

      await new Promise((r) => setTimeout(r, 600));

      setSyncProgress({
        step: 5,
        text: 'Generating ML risk predictions and recommendations...',
      });

      await new Promise((r) => setTimeout(r, 600));

      setSyncProgress({
        step: 6,
        text: '✓ Dashboard ready! Redirecting...',
      });

      await fetchProjects();
      if (registered) {
        setSelectedProject(registered);
      }

      setTimeout(() => {
        setSyncingRepoId(null);
        setSyncProgress(null);
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      setSyncProgress({
        step: -1,
        text: `Sync Failed: ${err.response?.data?.detail || err.message}`,
      });
      setTimeout(() => {
        setSyncingRepoId(null);
        setSyncProgress(null);
      }, 3000);
    }
  };

  // Trigger manual sync for registered repository
  const handleSyncNow = async (repoId) => {
    try {
      setSyncingRepoId(repoId);
      await githubService.syncRepository(repoId);
      await fetchProjects();
      setToastMessage('✓ Repository synchronized with latest GitHub data.');
      setToastType('info');
      setTimeout(() => setToastMessage(null), 3000);
    } catch (err) {
      setToastMessage(`Sync failed: ${err.message}`);
      setToastType('error');
    } finally {
      setSyncingRepoId(null);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Toast Notification */}
      {toastMessage && (
        <div
          className={`p-4 rounded-xl text-sm flex items-center justify-between animate-in fade-in duration-200 ${
            toastType === 'error'
              ? 'bg-rose-500/10 border border-rose-500/30 text-rose-400'
              : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
          }`}
        >
          <div className="flex items-center gap-2">
            {toastType === 'error' ? <AlertTriangle size={16} /> : <Sparkles size={16} />}
            <span>{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Header & GitHub Status */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <span>Repositories & Projects</span>
            <span className="text-xs px-2.5 py-1 bg-githubPrimary/20 text-githubPrimary border border-githubPrimary/30 rounded-full font-mono font-medium">
              GitHub-Centric
            </span>
          </h1>
          <p className="text-githubTextSecondary mt-2">
            Select and register your GitHub repositories to enable automated CI failure prediction, live webhook tracking, and performance analytics.
          </p>
        </div>

        {/* GitHub OAuth Connection Status Box */}
        <div className="flex items-center gap-3 bg-githubCard border border-githubBorder p-3 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center text-white overflow-hidden">
            {githubStatus?.avatar_url ? (
              <img src={githubStatus.avatar_url} alt="GitHub" className="w-full h-full object-cover" />
            ) : (
              <FolderGit2 size={18} />
            )}
          </div>
          <div>
            <div className="text-xs font-semibold text-white flex items-center gap-1.5">
              <span>{githubStatus?.connected ? `@${githubStatus.username}` : 'GitHub Not Connected'}</span>
              {githubStatus?.connected ? (
                <CheckCircle size={13} className="text-githubPrimary" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
              )}
            </div>
            <div className="text-[11px] text-githubTextSecondary font-mono">
              {githubStatus?.connected ? 'OAuth: Active Token' : 'Disconnected'}
            </div>
          </div>
          <button
            onClick={handleConnectGitHub}
            className="ml-2 px-3 py-1.5 bg-githubPrimary hover:bg-emerald-600 text-white text-xs font-medium rounded-lg transition-colors cursor-pointer"
          >
            {githubStatus?.connected ? 'Reconnect' : 'Connect GitHub'}
          </button>
        </div>
      </div>

      {/* Sync Progress Modal / Banner */}
      {syncProgress && (
        <div className="p-6 bg-githubCard border border-githubPrimary/50 rounded-2xl shadow-xl flex flex-col gap-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Loader2 size={20} className="animate-spin text-githubPrimary" />
              <span className="text-base font-bold text-white">Synchronizing Repository with INTELLI-CI...</span>
            </div>
            <span className="text-xs font-mono text-githubPrimary">Stage {syncProgress.step > 0 ? syncProgress.step : '!'}/6</span>
          </div>
          <div className="w-full bg-githubBg h-2.5 rounded-full overflow-hidden border border-githubBorder">
            <div
              className={`h-full transition-all duration-500 ${
                syncProgress.step < 0 ? 'bg-rose-500' : 'bg-githubPrimary'
              }`}
              style={{ width: `${Math.max(15, (syncProgress.step / 6) * 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-githubTextSecondary font-mono">{syncProgress.text}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-3 border-b border-githubBorder pb-3">
        <button
          onClick={() => setActiveTab('browse')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'browse'
              ? 'bg-githubPrimary text-white shadow-sm'
              : 'text-githubTextSecondary hover:text-white hover:bg-githubCard'
          }`}
        >
          <Globe size={15} />
          <span>Browse GitHub Repositories</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-black/20">{githubRepos.length}</span>
        </button>

        <button
          onClick={() => setActiveTab('registered')}
          className={`px-4 py-2 text-sm font-semibold rounded-lg transition-colors cursor-pointer flex items-center gap-2 ${
            activeTab === 'registered'
              ? 'bg-githubPrimary text-white shadow-sm'
              : 'text-githubTextSecondary hover:text-white hover:bg-githubCard'
          }`}
        >
          <FolderGit2 size={15} />
          <span>Active Monitored Projects</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-black/20">{projects.length}</span>
        </button>
      </div>

      {/* TAB 1: BROWSE GITHUB REPOSITORIES */}
      {activeTab === 'browse' && (
        <div className="flex flex-col gap-6">
          {!githubStatus?.connected ? (
            <div className="p-12 bg-githubCard border border-githubBorder rounded-3xl text-center flex flex-col items-center shadow-lg">
              <div className="w-16 h-16 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center mb-4 text-githubPrimary">
                <GitBranch size={32} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Connect GitHub to Browse Repositories</h3>
              <p className="text-xs text-githubTextSecondary mb-6 max-w-md leading-relaxed">
                Authorize INTELLI-CI with your GitHub account to automatically discover repositories and configure real-time workflow telemetry.
              </p>
              <button
                onClick={handleConnectGitHub}
                className="px-6 py-2.5 bg-githubPrimary hover:bg-emerald-600 text-white font-semibold text-xs rounded-xl transition-all shadow-md flex items-center gap-2 cursor-pointer"
              >
                <GitBranch size={14} />
                <span>Connect GitHub</span>
              </button>
            </div>
          ) : (
            <>
              {/* Search bar */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-githubTextSecondary" />
                  <input
                    type="text"
                    placeholder="Search accessible repositories by name or description..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-githubCard border border-githubBorder rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder:text-githubTextSecondary focus:outline-none focus:border-githubPrimary transition-colors"
                  />
                </div>
                <button
                  onClick={loadGitHubRepos}
                  className="px-4 py-2.5 bg-githubCard hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-xl text-sm font-medium transition-colors flex items-center gap-2 self-start cursor-pointer"
                >
                  <RefreshCw size={14} className={loadingRepos ? 'animate-spin text-githubPrimary' : ''} />
                  <span>Refresh List</span>
                </button>
              </div>

              {/* Repository Cards Grid */}
              {githubRepos.length === 0 && !loadingRepos ? (
                <div className="p-12 bg-githubCard border border-githubBorder rounded-2xl text-center text-xs text-githubTextSecondary">
                  <FolderGit2 size={32} className="mx-auto mb-2 opacity-40" />
                  <p className="font-semibold text-white">No repositories found.</p>
                  <p className="mt-1 text-githubTextSecondary">Your connected GitHub account has no matching repositories.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {githubRepos.map((repo) => {
                    const isRegistered = projects.some((p) => (p.name === repo.name || p.full_name === repo.full_name));
                    const isSyncing = syncingRepoId === repo.name;
                    const repoOwner = typeof repo.owner === 'string' ? repo.owner : (repo.owner?.login || githubStatus?.username || 'user');

                    return (
                      <div
                        key={repo.id || repo.name}
                        className="bg-githubCard border border-githubBorder hover:border-githubBorder/80 rounded-2xl p-6 flex flex-col justify-between transition-all shadow-sm group"
                      >
                        <div>
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex items-center gap-2.5 truncate">
                              <div className="w-8 h-8 rounded-lg bg-githubBg border border-githubBorder flex items-center justify-center text-githubPrimary flex-shrink-0">
                                <FolderGit2 size={16} />
                              </div>
                              <div className="truncate">
                                <h3 className="text-base font-bold text-white group-hover:text-githubPrimary transition-colors truncate">
                                  {repo.full_name || repo.name}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-githubTextSecondary font-mono mt-0.5">
                                  <span>Owner: {repoOwner}</span>
                                  <span>•</span>
                                  <span className="flex items-center gap-1">
                                    <GitBranch size={11} />
                                    {repo.default_branch || 'main'}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <span className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-mono border border-githubBorder bg-githubBg text-githubTextSecondary">
                              {repo.private ? <Lock size={10} className="text-amber-400" /> : <Globe size={10} className="text-emerald-400" />}
                              <span>{repo.private ? 'Private' : 'Public'}</span>
                            </span>
                          </div>

                          <p className="text-xs text-githubTextSecondary line-clamp-2 my-3 min-h-[32px]">
                            {repo.description || 'Repository tracked with INTELLI-CI optimization engine.'}
                          </p>

                          <div className="flex items-center gap-4 text-xs text-githubTextSecondary font-mono pt-2">
                            {repo.language && (
                              <span className="flex items-center gap-1.5 text-white">
                                <span className="w-2.5 h-2.5 rounded-full bg-githubPrimary inline-block"></span>
                                {repo.language}
                              </span>
                            )}
                            <span className="flex items-center gap-1">
                              <Star size={12} className="text-amber-400" />
                              {repo.stargazers_count || 0}
                            </span>
                            <span className="flex items-center gap-1">
                              <GitFork size={12} />
                              {repo.forks_count || 0}
                            </span>
                          </div>
                        </div>

                        <div className="mt-5 pt-4 border-t border-githubBorder/50 flex items-center justify-between gap-3">
                          <a
                            href={repo.html_url || `https://github.com/${repo.full_name || repo.name}`}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-githubTextSecondary hover:text-white flex items-center gap-1 transition-colors"
                          >
                            GitHub <ExternalLink size={11} />
                          </a>

                          {isRegistered ? (
                            <button
                              onClick={() => {
                                const p = projects.find((x) => x.name === repo.name || x.full_name === repo.full_name);
                                if (p) setSelectedProject(p);
                                navigate('/dashboard');
                              }}
                              className="px-3.5 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-semibold rounded-xl transition-colors flex items-center gap-1.5 cursor-pointer"
                            >
                              <CheckCircle size={13} />
                              <span>Registered • Open Dashboard</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSelectRepository(repo)}
                              disabled={isSyncing}
                              className="px-4 py-2 bg-githubPrimary hover:bg-emerald-600 text-white text-xs font-semibold rounded-xl transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50 shadow-sm"
                            >
                              {isSyncing ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
                              <span>Select & Register Repository</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* TAB 2: ACTIVE MONITORED PROJECTS */}
      {activeTab === 'registered' && (
        <div className="flex flex-col gap-4">
          {projects.length === 0 ? (
            <div className="p-12 bg-githubCard border border-githubBorder rounded-3xl text-center text-xs text-githubTextSecondary">
              <FolderGit2 size={32} className="mx-auto mb-2 opacity-40 text-githubPrimary" />
              <p className="font-semibold text-white text-sm">No registered repositories yet.</p>
              <p className="mt-1 text-githubTextSecondary">
                Browse your GitHub repositories in Tab 1 and select one to register it in INTELLI-CI.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => {
                const isSelected = selectedProject?.id === project.id;
                const isSyncing = syncingRepoId === project.id;

                return (
                  <div
                    key={project.id}
                    className={`bg-githubCard border rounded-2xl p-5 flex flex-col justify-between transition-all ${
                      isSelected ? 'border-githubPrimary ring-1 ring-githubPrimary/50 shadow-lg' : 'border-githubBorder hover:border-githubBorder/80'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-githubBg border border-githubBorder text-githubTextSecondary">
                          {project.language || 'Python'}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          {project.sync_status || 'COMPLETED'}
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-white hover:text-githubPrimary transition-colors truncate">
                        {project.full_name || project.name}
                      </h3>
                      <p className="text-xs text-githubTextSecondary mt-1 line-clamp-2">
                        {project.description || 'CI/CD pipeline metrics, DAG stages, and ML predictions.'}
                      </p>
                    </div>

                    <div className="mt-5 pt-4 border-t border-githubBorder/50 flex items-center justify-between gap-2">
                      <button
                        onClick={() => handleSyncNow(project.id)}
                        disabled={isSyncing}
                        className="px-2.5 py-1.5 bg-githubBg hover:bg-githubBorder/40 text-githubTextSecondary hover:text-white border border-githubBorder rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 cursor-pointer"
                      >
                        <RefreshCw size={12} className={isSyncing ? 'animate-spin text-githubPrimary' : ''} />
                        <span>Sync Now</span>
                      </button>

                      <button
                        onClick={() => {
                          setSelectedProject(project);
                          navigate('/dashboard');
                        }}
                        className="px-3.5 py-1.5 bg-githubPrimary hover:bg-emerald-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1 cursor-pointer"
                      >
                        <span>View Dashboard</span>
                        <ArrowRight size={13} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
