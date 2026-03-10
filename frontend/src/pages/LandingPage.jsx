import { Link } from 'react-router-dom'
import { Cpu, Bot, Zap, Activity, GitBranch } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  {
    icon: Bot,
    title: 'ML-based CI prediction',
    desc: 'Predict pipeline failures early using commit-level intelligence.',
  },
  {
    icon: Zap,
    title: 'Smart test execution',
    desc: 'Run only the right tests and skip low-risk executions confidently.',
  },
  {
    icon: Activity,
    title: 'CI analytics dashboard',
    desc: 'Visualize trends for commit risk, time savings, and pipeline health.',
  },
  {
    icon: GitBranch,
    title: 'GitHub Integration',
    desc: 'Mirror your commit activity and CI outcomes in one place.',
  },
]

export default function LandingPage() {
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#E6EDF3] font-sans selection:bg-[#2ea043]/30 flex flex-col items-center">
      {/* Navbar aligned with the hero container */}
      <nav className="w-full border-b border-[#30363d] bg-transparent">
        <div className="max-w-[1024px] mx-auto px-6 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 no-underline">
            <Cpu size={20} className="text-[#2ea043]" strokeWidth={2} />
            <span className="font-bold text-sm tracking-wide text-[#E6EDF3]">
              INTELLI-CI
            </span>
          </Link>
          <div className="flex items-center gap-4">
            {user ? (
              <Link
                to="/dashboard"
                className="text-sm font-medium text-[#8B949E] hover:text-[#E6EDF3] transition-colors py-2 px-5 rounded-full border border-[#30363d] hover:bg-[#21262d]"
              >
                Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium text-[#8B949E] transition-colors py-2 px-6 rounded-full border border-[#30363d] hover:text-[#E6EDF3] hover:bg-[#21262d]"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="text-sm font-semibold bg-[#2ea043] text-white px-6 py-2.5 rounded-full hover:bg-[#238636] transition-colors shadow-sm"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="w-full max-w-[1024px] px-6 flex flex-col justify-center flex-1 py-16 pb-24">
        {/* Hero Section */}
        <div className="mb-14">
          <div className="inline-flex items-center px-4 py-1.5 mb-8 rounded-full bg-[#161b22] border border-[#30363d] text-[11px] font-bold tracking-widest text-[#8B949E] uppercase">
            AI / DEVOPS PLATFORM
          </div>
          
          <h1 className="text-[44px] sm:text-5xl md:text-[56px] font-bold leading-[1.15] mb-5 tracking-tight text-[#E6EDF3]">
            Intelligent CI/CD<br />
            Optimization Platform
          </h1>
          
          <p className="text-[#8B949E] text-[17px] sm:text-lg mb-10 max-w-xl leading-relaxed">
            Reduce CI execution time using AI-powered failure prediction.
          </p>

          <div className="flex items-center gap-4">
            <Link
              to={user ? '/dashboard' : '/signup'}
              className="inline-flex items-center justify-center font-semibold text-[15px] bg-[#2ea043] text-white px-7 py-3 rounded-full hover:bg-[#238636] transition-colors shadow-sm"
            >
              Get Started
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-center font-semibold text-[15px] bg-[#21262d] border border-[#30363d] text-[#E6EDF3] px-7 py-3 rounded-full hover:bg-[#30363d] transition-colors"
            >
              View Dashboard
            </Link>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 w-full">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <div
              key={i}
              className="p-8 pb-10 rounded-2xl bg-[#161b22] border border-[#30363d] hover:border-[#484f58] transition-colors group"
            >
              <Icon className="text-[#2ea043] mb-5 transform group-hover:scale-110 transition-transform duration-300" size={20} strokeWidth={2} />
              <h3 className="text-[#E6EDF3] font-semibold text-[15px] mb-2 tracking-tight">
                {title}
              </h3>
              <p className="text-[#8B949E] text-sm leading-relaxed">
                {desc}
              </p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
