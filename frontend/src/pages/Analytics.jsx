import ChartCard from '../components/ChartCard'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Analytics() {
  const data = [
    { name: 'Week 1', rate: 20 },
    { name: 'Week 2', rate: 25 },
    { name: 'Week 3', rate: 35 },
    { name: 'Week 4', rate: 42 },
    { name: 'Week 5', rate: 58 },
    { name: 'Week 6', rate: 65 },
  ]
  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Insights</h1>
        <p className="page-sub">Analyze your CI savings and AI performance metrics</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="lg:col-span-2">
          <ChartCard title="Overall Skip Rate Over Time" subtitle="Percentage of total tests skipped securely by the AI.">
            <ResponsiveContainer width="100%" height="85%" className="mt-4">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dy={10} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} dx={-10} tickFormatter={(val) => `${val}%`} />
                <Tooltip contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', borderColor: 'rgba(255,255,255,0.1)', color: '#fff', borderRadius: '8px' }} itemStyle={{ color: '#10b981', fontWeight: 'bold' }} />
                <Area type="monotone" dataKey="rate" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorRate)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      </div>
    </div>
  )
}