/**
 * Reusable form input — accessible, responsive, touch-friendly.
 */
export default function FormInput({
  label,
  id,
  type = 'text',
  placeholder,
  value,
  onChange,
  required,
  error,
  autoComplete,
  hint,
  className = '',
}) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label
          htmlFor={id}
          className="text-sm font-medium text-[var(--color-text-primary)]"
        >
          {label}
          {required && <span className="text-[var(--color-error)] ml-0.5">*</span>}
          {hint && (
            <span className="ml-1.5 text-xs font-normal text-[var(--color-text-secondary)]">
              {hint}
            </span>
          )}
        </label>
      )}
      <input
        id={id}
        name={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
        autoComplete={autoComplete}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        className={`w-full px-4 py-3 rounded-lg border text-sm outline-none transition-colors duration-150 bg-[#0d1117] text-[var(--color-text-primary)] min-h-[48px] focus:border-[var(--color-accent)] focus:ring-1 focus:ring-[var(--color-accent)] ${error ? 'border-[var(--color-error)]' : 'border-[#30363d]'}`}
      />
      {error && (
        <p
          id={`${id}-error`}
          className="text-xs text-[var(--color-error)]"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  )
}
