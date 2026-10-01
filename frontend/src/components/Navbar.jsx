import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProject } from '../context/ProjectContext';
import {
  FolderGit2,
  ChevronDown,
  GitBranch,
  User,
  Check,
  Play,
  Sparkles,
  Loader2,
} from 'lucide-react';

const PROFESSION_LABELS = {
  student: 'Student', developer: 'Developer', software_engineer: 'Software Engineer',
  devops_engineer: 'DevOps Engineer', team_lead: 'Team Lead', project_manager: 'Project Manager',
  researcher: 'Researcher', other: 'Other', admin: 'Admin', viewer: 'Viewer',
};

export default function Navbar() {
  const { projects, selectedProject, setSelectedProject, githubStatus, simulateWebhook } = useProject();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [simulating, setSimulating]     = useState(false);
  const [simToast, setSimToast]         = useState(null);

  // Real user from localStorage (set after login)
  const storedUser = (() => {
    try { return JSON.parse(localStorage.getItem('intelli_ci_user') || '{}'); } catch { return {}; }
  })();
  const displayName = githubStatus?.username || storedUser?.name?.split(' ')[0] || 'You';
  const displayRole = PROFESSION_LABELS[storedUser?.profession || storedUser?.role] || storedUser?.role || '';

  const handleSimulate = async (conclusion) => {
    try {
      setSimulating(true);
      await simulateWebhook({
        conclusion,
        event_type: 'workflow_run',
        commit_message: `feat(core): live push & test run [${conclusion.toUpperCase()}]`,
      });
      setSimToast(`Simulated Webhook (${conclusion.toUpperCase()}) received & processed!`);
      setTimeout(() => setSimToast(null), 4000);
    } catch {
      setSimToast('Simulation failed');
      setTimeout(() => setSimToast(null), 3000);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <nav className="h-16 border-b border-githubBorder bg-githubCard/60 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-40">

      {/* ── Left: Project selector ─────────────────────────────────── */}
      <div className="relative">
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex items-center gap-2.5 px-3.5 py-1.5 bg-githubBg hover:bg-githubBorder/40 border border-githubBorder rounded-xl text-sm font-semibold text-white transition-all shadow-sm group"
        >
          <div className="w-5 h-5 rounded-md bg-githubPrimary/20 text-githubPrimary flex items-center justify-center">
            <FolderGit2 size={13} />
          </div>
          <span className="font-mono text-xs text-githubTextSecondary">Project:</span>
          <span className="max-w-[180px] truncate text-white group-hover:text-githubPrimary transition-colors">
            {selectedProject?.full_name || selectedProject?.name || 'Select Project'}
          </span>
          <ChevronDown size={14} className={`text-githubTextSecondary transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropdownOpen && (
          <div className="absolute left-0 mt-2 w-72 bg-githubCard border border-githubBorder rounded-xl shadow-2xl py-2 z-50">
            <div className="px-3 py-1.5 text-[11px] font-semibold text-githubTextSecondary uppercase tracking-wider border-b border-githubBorder/50">
              Active Repositories ({projects.length})
            </div>
            <div className="max-h-60 overflow-y-auto py-1">
              {projects.map((p) => {
                const isSelected = selectedProject?.id === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => { setSelectedProject(p); setDropdownOpen(false); }}
                    className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between hover:bg-githubBorder/40 transition-colors ${
                      isSelected ? 'text-githubPrimary font-semibold bg-githubPrimary/10' : 'text-githubTextPrimary'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <GitBranch size={13} className="text-githubTextSecondary flex-shrink-0" />
                      <span className="truncate">{p.full_name || p.name}</span>
                    </div>
                    {isSelected && <Check size={14} className="text-githubPrimary flex-shrink-0" />}
                  </button>
                );
              })}
            </div>
            <div className="p-2 border-t border-githubBorder/50">
              <Link
                to="/projects"
                onClick={() => setDropdownOpen(false)}
                className="w-full block text-center py-1.5 text-xs bg-githubPrimary/20 hover:bg-githubPrimary/30 text-githubPrimary rounded-lg font-medium transition-colors"
              >
                + Connect New GitHub Repo
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* ── Right: Actions + Profile ───────────────────────────────── */}
      <div className="flex items-center gap-3">

        {/* Toast */}
        {simToast && (
          <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs rounded-lg">
            <Sparkles size={13} />
            <span>{simToast}</span>
          </div>
        )}

        {/* Live indicator */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 bg-githubBg border border-githubBorder rounded-lg text-xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-mono text-githubTextSecondary">
            {githubStatus?.connected ? 'GitHub Live Webhook' : 'Not Connected'}
          </span>
        </div>

        {/* Webhook Simulator */}
        <div className="flex items-center gap-1 bg-githubBg border border-githubBorder rounded-lg p-1">
          <button
            onClick={() => handleSimulate('success')}
            disabled={simulating}
            className="px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 text-xs rounded-md transition-colors flex items-center gap-1.5 font-medium disabled:opacity-50"
          >
            {simulating ? <Loader2 size={12} className="animate-spin" /> : <Play size={11} />}
            Simulate CI Run
          </button>
          <button
            onClick={() => handleSimulate('failure')}
            disabled={simulating}
            className="px-2 py-1 hover:bg-rose-500/20 text-rose-400 text-xs rounded-md transition-colors font-medium disabled:opacity-50"
          >
            Fail Run
          </button>
        </div>

        {/* Profile Link */}
        <Link
          to="/profile"
          className="flex items-center gap-2.5 rounded-lg border border-githubBorder bg-githubBg hover:border-githubPrimary px-3 py-1.5 transition-all"
        >
          {githubStatus?.avatar_url ? (
            <img
              src={githubStatus.avatar_url}
              alt="avatar"
              className="w-6 h-6 rounded-full border border-githubBorder flex-shrink-0"
            />
          ) : (
            <div className="w-6 h-6 rounded-full bg-githubPrimary/20 text-githubPrimary flex items-center justify-center flex-shrink-0 text-xs font-bold">
              {storedUser?.name?.[0]?.toUpperCase() || <User size={12} />}
            </div>
          )}
          <div className="hidden sm:flex flex-col leading-none">
            <span className="text-xs font-semibold text-white">{displayName}</span>
            {displayRole && <span className="text-[10px] text-githubTextSecondary mt-0.5">{displayRole}</span>}
          </div>
        </Link>
      </div>
    </nav>
  );
}
