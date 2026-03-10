import Button from './Button'

export default function ProjectCard({
  project,
  onViewCommits,
  onViewAnalytics,
  onDelete,
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 group">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-bold text-lg text-slate-900 truncate group-hover:text-indigo-600 transition-colors">{project.name}</h3>
          <p className="text-sm text-slate-500 mt-1 truncate">{project.repo}</p>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Skip rate</p>
          <p className="font-mono text-base font-bold text-emerald-600 mt-1">{project.skipRate ?? '—'}</p>
        </div>
      </div>

      <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-2 gap-4 text-xs">
        <div>
          <p className="font-semibold uppercase tracking-wider text-slate-400">Total commits</p>
          <p className="font-mono text-sm font-semibold text-slate-700 mt-1.5">{project.totalCommits ?? '—'}</p>
        </div>
        <div>
          <p className="font-semibold uppercase tracking-wider text-slate-400">Updated</p>
          <p className="font-mono text-sm font-semibold text-slate-700 mt-1.5">{project.updatedAt ?? '—'}</p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <Button variant="secondary" onClick={onViewCommits}>View Commits</Button>
        <Button variant="secondary" onClick={onViewAnalytics}>View Analytics</Button>
        <Button variant="danger" onClick={onDelete}>Delete Project</Button>
      </div>
    </div>
  )
}

