/**
 * Reusable Button component — responsive, accessible, touch-friendly.
 * Variants: primary | secondary | danger | ghost
 */
export default function Button({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled = false,
  loading = false,
  className = '',
  fullWidth = false,
  icon: Icon,
}) {
  const base =
    'inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)] disabled:opacity-50 disabled:cursor-not-allowed active:translate-y-px min-h-[44px]'

  const variants = {
    primary: 'bg-[#2ea043] text-white hover:bg-green-600 shadow-sm',
    secondary: 'bg-transparent border border-[#30363d] text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] hover:border-[#444c56]',
    danger: 'bg-[#da3633] text-white hover:opacity-90',
    ghost: 'bg-transparent text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]',
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${fullWidth ? 'w-full' : ''} ${className}`}
    >
      {loading ? (
        <span
          className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"
          aria-hidden
        />
      ) : (
        <>
          {Icon && <Icon size={17} strokeWidth={1.5} />}
          {children}
        </>
      )}
    </button>
  )
}
