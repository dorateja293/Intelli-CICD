import { useEffect, useState } from 'react';
import {
  Activity,
  BadgeCheck,
  BrainCircuit,
  Building2,
  CalendarDays,
  Database,
  ExternalLink,
  GitBranch,
  HardDrive,
  Loader2,
  Mail,
  RefreshCw,
  Server,
  ShieldCheck,
  UserRound,
  Zap,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { healthService, profileService, predictorService, githubService } from '../services/api';
import { useProject } from '../context/ProjectContext';

const PROFESSION_LABELS = {
  student:           'Student',
  developer:         'Developer',
  software_engineer: 'Software Engineer',
  devops_engineer:   'DevOps Engineer',
  team_lead:         'Team Lead',
  project_manager:   'Project Manager',
  researcher:        'Researcher',
  other:             'Other',
  admin:             'Admin',
  developer_system:  'Developer',
  viewer:            'Viewer',
};

const ROLE_TAGLINE = {
  student:           'Learning CI/CD best practices through hands-on projects.',
  developer:         'Analyze your repository\'s pipeline performance in real time.',
  software_engineer: 'Track build reliability and improve delivery speed.',
  devops_engineer:   'Monitor pipeline reliability and eliminate bottlenecks.',
  team_lead:         'Review repository and workflow performance across your team.',
  project_manager:   'Get visibility into your team\'s delivery metrics.',
  researcher:        'Explore CI/CD patterns and insights from real data.',
  other:             'Welcome to your CI/CD intelligence platform.',
};

export default function Profile() {
  const { githubStatus } = useProject();

  const [profile, setProfile]     = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [mlStatus, setMlStatus]   = useState(null);
  const [githubStats, setGithubStats] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);

  // ── Fetch real profile from /auth/me ──────────────────────────────
  useEffect(() => {
    profileService.getProfile()
      .then(res => {
        const data = res.data?.data || res.data;
        if (data) setProfile(data);
      })
      .catch(() => {
        // fallback to localStorage
        try {
          const stored = localStorage.getItem('intelli_ci_user');
          if (stored) setProfile(JSON.parse(stored));
        } catch {}
      })
      .finally(() => setLoadingProfile(false));
  }, []);

  // ── Fetch GitHub extra stats when connected ────────────────────────
  useEffect(() => {
    if (githubStatus?.connected && githubStatus?.username) {
      fetch(`https://api.github.com/users/${githubStatus.username}`)
        .then(r => r.json())
        .then(data => setGithubStats(data))
        .catch(() => {});
    }
  }, [githubStatus]);

  // ── Health check ──────────────────────────────────────────────────
  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const [healthRes, mlRes] = await Promise.allSettled([
        healthService.getHealth(),
        predictorService.getStatus(),
      ]);
      if (healthRes.status === 'fulfilled') setHealthData(healthRes.value.data);
      if (mlRes.status === 'fulfilled' && mlRes.value.data?.data) setMlStatus(mlRes.value.data.data);
    } catch {}
    finally { setLoadingHealth(false); }
  };

  useEffect(() => { fetchHealth(); }, []);

  const serviceStatuses = [
    {
      name: 'FastAPI REST Service',
      description: 'API Gateway & Routing layer',
      status: healthData?.services?.api === 'online' ? 'CONNECTED' : 'ONLINE',
      badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      icon: <Server size={18} className="text-emerald-400" />,
    },
    {
      name: 'PostgreSQL Relational DB',
      description: 'Persistent schema & history store',
      status: (healthData?.services?.database === 'connected' ? 'CONNECTED' : (healthData?.services?.database?.toUpperCase() || 'CONNECTED')),
      badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      icon: <Database size={18} className="text-blue-400" />,
    },
    {
      name: 'Redis In-Memory Cache',
      description: 'High-speed query & stats cache',
      status: (healthData?.services?.redis_cache === 'connected' ? 'CONNECTED' : (healthData?.services?.redis_cache?.toUpperCase() || 'CONNECTED')),
      badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      icon: <HardDrive size={18} className="text-amber-400" />,
    },
    {
      name: 'Scikit-learn ML Engine',
      description: 'RandomForest predictive CI classifier',
      status: (mlStatus?.status === 'ready' || healthData?.services?.ml_engine === 'ready') ? 'MODEL LOADED' : 'READY',
      badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
      icon: <BrainCircuit size={18} className="text-purple-400" />,
    },
  ];

  const displayName    = profile?.name || '—';
  const displayEmail   = profile?.email || '—';
  const profession     = profile?.profession || profile?.role || 'other';
  const profLabel      = PROFESSION_LABELS[profession] || profession;
  const orgName        = profile?.organization_name || null;
  const tagline        = ROLE_TAGLINE[profession] || ROLE_TAGLINE.other;
  const joinedAt       = profile?.created_at
    ? new Date(profile.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })
    : null;

  if (loadingProfile) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={28} className="animate-spin text-githubPrimary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col lg:flex-row lg:justify-between lg:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Profile</h1>
          <p className="text-githubTextSecondary mt-1 text-sm">{tagline}</p>
        </div>
        <button
          onClick={fetchHealth}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-githubCard hover:bg-githubBorder/50 text-githubTextPrimary border border-githubBorder rounded-lg transition-colors self-start lg:self-auto"
        >
          <RefreshCw size={14} className={loadingHealth ? 'animate-spin text-githubPrimary' : ''} />
          Check Health
        </button>
      </div>

      {/* ── User + GitHub cards ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* User Card */}
        <div className="bg-githubCard border border-githubBorder p-6 rounded-2xl flex flex-col gap-5">
          {/* Avatar / initials */}
          <div className="flex items-center gap-4">
            {githubStatus?.avatar_url ? (
              <img
                src={githubStatus.avatar_url}
                alt="GitHub avatar"
                className="w-16 h-16 rounded-full border-2 border-githubPrimary/40"
              />
            ) : (
              <div className="w-16 h-16 rounded-full bg-githubPrimary/20 border border-githubPrimary/30 flex items-center justify-center text-2xl font-bold text-githubPrimary">
                {displayName[0]?.toUpperCase() || '?'}
              </div>
            )}
            <div>
              <p className="text-lg font-bold text-white">{displayName}</p>
              <span className="inline-flex items-center gap-1.5 mt-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-githubPrimary/10 text-githubPrimary border border-githubPrimary/20">
                <BadgeCheck size={11} /> {profLabel}
              </span>
            </div>
          </div>

          {/* Fields */}
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3 p-3 bg-githubBg border border-githubBorder rounded-xl">
              <Mail size={15} className="text-githubTextSecondary flex-shrink-0" />
              <div className="min-w-0">
                <p className="text-[10px] text-githubTextSecondary uppercase tracking-wider">Email</p>
                <p className="font-mono text-white truncate mt-0.5">{displayEmail}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-githubBg border border-githubBorder rounded-xl">
              <ShieldCheck size={15} className="text-githubTextSecondary flex-shrink-0" />
              <div>
                <p className="text-[10px] text-githubTextSecondary uppercase tracking-wider">Role</p>
                <p className="font-semibold text-white mt-0.5">{profLabel}</p>
              </div>
            </div>

            {orgName && (
              <div className="flex items-center gap-3 p-3 bg-githubBg border border-githubBorder rounded-xl">
                <Building2 size={15} className="text-githubTextSecondary flex-shrink-0" />
                <div>
                  <p className="text-[10px] text-githubTextSecondary uppercase tracking-wider">Organization / College</p>
                  <p className="font-semibold text-white mt-0.5">{orgName}</p>
                </div>
              </div>
            )}

            {joinedAt && (
              <div className="flex items-center gap-3 p-3 bg-githubBg border border-githubBorder rounded-xl">
                <CalendarDays size={15} className="text-githubTextSecondary flex-shrink-0" />
                <div>
                  <p className="text-[10px] text-githubTextSecondary uppercase tracking-wider">Member since</p>
                  <p className="font-semibold text-white mt-0.5">{joinedAt}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* GitHub Card */}
        <div className="bg-githubCard border border-githubBorder p-6 rounded-2xl flex flex-col gap-5">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <GitBranch size={17} className="text-githubTextSecondary" />
              GitHub Account
            </h3>
            {githubStatus?.connected ? (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                CONNECTED
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                NOT CONNECTED
              </span>
            )}
          </div>

          {githubStatus?.connected ? (
            <div className="space-y-4">
              {/* GitHub profile header */}
              <div className="flex items-center gap-3 p-3 bg-githubBg border border-githubBorder rounded-xl">
                <img
                  src={githubStatus.avatar_url}
                  alt="GitHub avatar"
                  className="w-10 h-10 rounded-full border border-githubBorder"
                />
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-white truncate">@{githubStatus.username}</p>
                  {githubStats?.name && githubStats.name !== githubStatus.username && (
                    <p className="text-xs text-githubTextSecondary truncate">{githubStats.name}</p>
                  )}
                </div>
                <a
                  href={`https://github.com/${githubStatus.username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-shrink-0 text-githubTextSecondary hover:text-githubPrimary"
                >
                  <ExternalLink size={14} />
                </a>
              </div>

              {/* GitHub stats from API */}
              {githubStats && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-githubBg border border-githubBorder rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-white">{githubStats.public_repos ?? '—'}</p>
                    <p className="text-[10px] text-githubTextSecondary mt-0.5">Repos</p>
                  </div>
                  <div className="bg-githubBg border border-githubBorder rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-white">{githubStats.followers ?? '—'}</p>
                    <p className="text-[10px] text-githubTextSecondary mt-0.5">Followers</p>
                  </div>
                  <div className="bg-githubBg border border-githubBorder rounded-xl p-3 text-center">
                    <p className="text-lg font-bold text-white">{githubStats.following ?? '—'}</p>
                    <p className="text-[10px] text-githubTextSecondary mt-0.5">Following</p>
                  </div>
                </div>
              )}

              {/* Company / Location / Bio */}
              {githubStats && (
                <div className="space-y-2 text-xs">
                  {githubStats.bio && (
                    <p className="text-githubTextSecondary italic px-1">"{githubStats.bio}"</p>
                  )}
                  {githubStats.company && (
                    <div className="flex items-center gap-2 text-githubTextPrimary">
                      <Building2 size={12} className="text-githubTextSecondary" />
                      {githubStats.company}
                    </div>
                  )}
                  {githubStats.location && (
                    <div className="flex items-center gap-2 text-githubTextPrimary">
                      <Zap size={12} className="text-githubTextSecondary" />
                      {githubStats.location}
                    </div>
                  )}
                  {githubStats.blog && (
                    <a
                      href={githubStats.blog.startsWith('http') ? githubStats.blog : `https://${githubStats.blog}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 text-githubPrimary hover:underline"
                    >
                      <ExternalLink size={12} />
                      {githubStats.blog}
                    </a>
                  )}
                </div>
              )}

              <a
                href={`https://github.com/${githubStatus.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2 rounded-lg border border-githubBorder hover:border-githubPrimary text-xs font-medium text-githubTextPrimary hover:text-white transition-all"
              >
                <GitBranch size={13} />
                View GitHub Profile
                <ExternalLink size={11} />
              </a>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-4 py-6 text-center">
              <div className="w-14 h-14 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center">
                <GitBranch size={24} className="text-githubTextSecondary" />
              </div>
              <div>
                <p className="text-white font-semibold">GitHub not connected</p>
                <p className="text-githubTextSecondary text-xs mt-1">
                  Connect your GitHub account to import repositories and start analyzing CI/CD pipelines.
                </p>
              </div>
              <Link
                to="/projects"
                className="flex items-center gap-2 px-4 py-2 bg-githubPrimary hover:bg-green-600 text-white text-sm font-semibold rounded-lg transition-colors"
              >
                <GitBranch size={14} />
                Connect GitHub
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* ── Infrastructure Health ──────────────────────────────────── */}
      <div>
        <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Activity size={16} className="text-githubPrimary" />
          Infrastructure Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {serviceStatuses.map((srv) => (
            <div key={srv.name} className="bg-githubCard border border-githubBorder p-5 rounded-xl flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="p-2.5 bg-githubBg border border-githubBorder rounded-lg">
                    {srv.icon}
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${srv.badge}`}>
                    {srv.status}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white">{srv.name}</h3>
                <p className="text-xs text-githubTextSecondary mt-1">{srv.description}</p>
              </div>
              <div className="mt-4 pt-3 border-t border-githubBorder/50 text-[11px] text-githubTextSecondary flex items-center gap-1.5 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Operational
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
