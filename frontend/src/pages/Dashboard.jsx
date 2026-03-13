import StatCard from '../components/StatCard'
import CommitTable from '../components/CommitTable'
import ChartCard from '../components/ChartCard'
import { GitCommitHorizontal, FastForward, Clock, Crosshair, Zap } from 'lucide-react'
import { AreaChart, Area, PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const pieData = [
    { name: 'Run Tests', value: 400, color: '#f43f5e' },
    { name: 'Skip Tests', value: 300, color: '#10b981' },
    { name: 'Partial', value: 100, color: '#f59e0b' }
  ]
  const barData = [
    { name: 'Mon', commits: 12 }, { name: 'Tue', commits: 19 },
    { name: 'Wed', commits: 15 }, { name: 'Thu', commits: 25 }, { name: 'Fri', commits: 22 }
  ]
  
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/80 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-xl">
          <p className="text-white font-bold text-sm">{`${payload[0].name || ''} : ${payload[0].value}`}</p>
        </div>
      );
    }
    return null;
  };
  
  return (
    <div className="space-y-8 pb-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="page-sub">Your infrastructure savings and AI performance.</p>
        </div>
        <div className="flex gap-3">
          <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium text-white transition-colors">Download Report</button>
          <button className="px-4 py-2 bg-indigo-500 hover:bg-indigo-400 border border-indigo-400/50 rounded-lg text-sm font-medium text-white shadow-[0_0_15px_rgba(99,102,241,0.3)] transition-all flex items-center gap-2">
            <Zap size={16}/> Connect Repo
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
        <StatCard title="Analyzed Commits" value="1,248" subValue="/ 7 days" trend={12} icon={GitCommitHorizontal} colorClass="bg-blue-500" gradientClass="bg-blue-500/30" />
        <StatCard title="Tests Skipped" value="342" trend={24} icon={FastForward} colorClass="bg-emerald-500" gradientClass="bg-emerald-500/30" />
        <StatCard title="Compute Saved" value="142" subValue="hrs" trend={18} icon={Clock} colorClass="bg-purple-500" gradientClass="bg-purple-500/30" />
        <StatCard title="AI Accuracy" value="99.2%" icon={Crosshair} colorClass="bg-indigo-500" gradientClass="bg-indigo-500/30" />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="Commit Flow Timeline" subtitle="Daily commit volume tracked across all connected repositories.">
            <ResponsiveContainer width="100%" height="80%">
              <AreaChart data={barData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCommits" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dx={-10} />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1, fill: 'transparent' }} />
                <Area type="monotone" dataKey="commits" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorCommits)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
        <div>
          <ChartCard title="AI Decisions" subtitle="Distribution of predictive actions taken by the engine.">
            <ResponsiveContainer width="100%" height="80%">
              <PieChart>
                <Pie data={pieData} innerRadius={70} outerRadius={100} paddingAngle={2} dataKey="value" stroke="rgba(255,255,255,0.05)" strokeWidth={2}>
                  {pieData.map((d, i) => <Cell key={i} fill={d.color} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pt-16 mt-4 pointer-events-none">
                <span className="text-3xl font-bold text-white tracking-tight">800</span>
                <span className="text-[10px] text-[#71717a] font-bold uppercase tracking-widest mt-1">Total</span>
            </div>
          </ChartCard>
        </div>
      </div>
      
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title text-white">Latest Analysis</h2>
          <button className="text-sm font-semibold text-indigo-400 hover:text-indigo-300">View All →</button>
        </div>
        <CommitTable />
      </div>
    </div>
  )
}