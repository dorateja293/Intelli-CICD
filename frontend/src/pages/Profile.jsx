import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function Profile() {
  return (
    <div className="max-w-4xl space-y-8">
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-sub">Manage your personal profile and preferences</p>
      </div>
      
      <div className="glass-panel p-8 border border-white/10 flex items-center gap-8 relative overflow-hidden">
        <div className="absolute right-0 top-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-[80px]"></div>
        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=6366f1" alt="Avatar" className="w-24 h-24 rounded-2xl border border-white/20 shadow-xl relative z-10" />
        <div className="relative z-10">
          <h2 className="text-3xl font-bold text-white tracking-tight mb-1">Pro Developer</h2>
          <p className="text-indigo-400 font-medium mb-3">pro@company.com</p>
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-white/10 border border-white/10 text-white">Administrator</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-panel p-8 border border-white/10 space-y-6">
          <div className="mb-6 pb-4 border-b border-white/5">
            <h3 className="text-lg font-bold text-white">Personal Info</h3>
          </div>
          <FormInput id="name" label="Display Name" defaultValue="Pro Developer" />
          <FormInput id="email" label="Email Address" defaultValue="pro@company.com" />
          <div className="pt-4">
            <Button variant="secondary">Save Changes</Button>
          </div>
        </div>

        <div className="glass-panel p-8 border border-white/10 space-y-6">
           <div className="mb-6 pb-4 border-b border-white/5">
            <h3 className="text-lg font-bold text-white">Security</h3>
          </div>
          <FormInput type="password" id="cur" label="Current Password" placeholder="••••••••" />
          <FormInput type="password" id="new" label="New Password" placeholder="••••••••" />
          <div className="pt-4">
             <Button variant="indigo">Update Password</Button>
          </div>
        </div>
      </div>
    </div>
  )
}