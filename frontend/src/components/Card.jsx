/**
 * Reusable KPI Card — metric display with icon, value, subtitle.
 * Use for dashboard stats and key performance indicators.
 */
export default function Card({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = 'var(--color-accent)',
  loading = false,
  className = '',
  trend,
}) {
  if (loading) {
    return (
      <div
        className={`bg-[#161b22] border border-[#30363d] rounded-xl p-8 ${className}`}
      >
        <div className="skeleton h-4 w-28 mb-5" />
        <div className="skeleton h-11 w-24 mb-3" />
        <div className="skeleton h-3 w-28" />
      </div>
    )
  }

  return (
    <div
      className={`bg-[#161b22] border border-[#30363d] rounded-xl p-8 card-hover ${className}`}
    >
      <div className="flex items-start justify-between gap-3 mb-5">
        <span className="text-base font-semibold text-[var(--color-text-secondary)] leading-tight">
          {title}
        </span>
        {Icon && (
          <div
            className="p-3 rounded-xl shrink-0"
            style={{ background: `${accent}1a` }}
          >
            <Icon size={20} style={{ color: accent }} strokeWidth={1.5} />
          </div>
        )}
      </div>
      <div className="text-4xl sm:text-5xl font-bold tracking-tight mb-2 text-[var(--color-text-primary)]">
        {value ?? '—'}
      </div>
      <div className="flex items-center gap-2">
        {subtitle && (
          <span className="text-base text-[var(--color-text-secondary)]">{subtitle}</span>
        )}
        {trend && (
          <span
            className="text-xs font-semibold px-1.5 py-0.5 rounded"
            style={{
              color: trend.startsWith('+') ? 'var(--color-accent)' : '#f85149',
              background: trend.startsWith('+') ? 'rgba(46,160,67,0.12)' : 'rgba(248,81,73,0.12)',
            }}
          >
            {trend}
          </span>
        )}
      </div>
    </div>
  )
}
