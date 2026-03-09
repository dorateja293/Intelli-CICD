import Button from './Button'

export default function ProjectCard({
  project,
  onViewCommits,
  onViewAnalytics,
  onDelete,
}) {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 panel-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold text-[var(--color-text-primary)] truncate">{project.name}</h3>
          <p className="text-sm text-[var(--color-text-secondary)] mt-2 truncate">{project.repo}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-[var(--color-text-secondary)]">Skip rate</p>
          <p className="font-mono text-sm text-[var(--color-text-primary)]">{project.skipRate ?? '—'}</p>
        </div>
      </div>

      <div className="mt-5 pt-4 border-t border-[#30363d] grid grid-cols-2 gap-3 text-xs text-[var(--color-text-secondary)]">
        <div>
          <p>Total commits</p>
          <p className="font-mono text-[var(--color-text-primary)] mt-1">{project.totalCommits ?? '—'}</p>
        </div>
        <div>
          <p>Updated</p>
          <p className="font-mono text-[var(--color-text-primary)] mt-1">{project.updatedAt ?? '—'}</p>
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

