import { Link, useNavigate } from 'react-router-dom'
import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Login() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      
      <div className="max-w-[420px] w-full glass-panel p-10 relative z-10 border border-white/10 shadow-2xl backdrop-blur-2xl bg-black/60">
        <div className="w-12 h-12 bg-white rounded-xl text-black flex items-center justify-center font-bold text-xl mb-8 shadow-[0_0_20px_rgba(255,255,255,0.2)]">IC</div>
        
        <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Welcome back</h1>
        <p className="text-[#a1a1aa] text-sm mb-8 font-medium">Enter your credentials to access your dashboard.</p>
        
        <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); navigate('/dashboard') }}>
          <FormInput id="email" label="Email Address" type="email" placeholder="name@company.com" required />
          <FormInput id="password" label="Password" type="password" placeholder="••••••••" required />
          
          <div className="pt-4">
            <Button type="submit" variant="indigo">Sign In</Button>
          </div>
        </form>
        
        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <p className="text-[#71717a] text-sm font-medium">
            New to Intelli-CI? <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 font-bold transition-colors">Create an account</Link>
          </p>
        </div>
      </div>
    </div>
  )
}