import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-10 sm:py-14"
      style={{ background: 'var(--color-bg-primary)' }}
    >
      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full blur-3xl opacity-[0.06]"
          style={{ background: 'radial-gradient(ellipse, #388bfd 0%, transparent 60%)' }}
        />
      </div>
      <div className="w-full max-w-md relative z-10">
        <Outlet />
      </div>
    </div>
  )
}
