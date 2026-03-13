import { Link, useNavigate } from 'react-router-dom'
import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Signup() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-purple-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      
      <div className="max-w-[420px] w-full glass-panel p-10 relative z-10 border border-white/10 shadow-2xl backdrop-blur-2xl bg-black/60">
        <h1 className="text-2xl font-bold text-white mb-2 tracking-tight">Start Optimizing</h1>
        <p className="text-[#a1a1aa] text-sm mb-8 font-medium">Create your account to get 14 days of free Pro access.</p>
        
        <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); navigate('/dashboard') }}>
          <FormInput id="name" label="Full Name" type="text" placeholder="Jane Doe" required />
          <FormInput id="email" label="Work Email" type="email" placeholder="jane@company.com" required />
          <FormInput id="password" label="Password" type="password" placeholder="••••••••" required />
          
          <div className="pt-6">
            <Button type="submit" variant="primary">Create Account</Button>
          </div>
        </form>
        
        <div className="mt-8 pt-6 border-t border-white/10 text-center">
          <p className="text-[#71717a] text-sm font-medium">
            Already have an account? <Link to="/login" className="text-white hover:text-gray-300 font-bold transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}