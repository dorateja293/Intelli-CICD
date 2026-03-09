import {
  PieChart, Pie, Cell, Tooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar, ResponsiveContainer,
} from 'recharts'

const COLORS = { skip: '#238636', run: '#f85149', line: '#388bfd', bar: '#a371f7' }

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div
      className="rounded-md border px-3 py-2 text-sm shadow-lg"
      style={{ background: '#21262D', borderColor: '#30363D', color: '#E6EDF3' }}
    >
      {label && <p className="font-semibold mb-1" style={{ color: '#8B949E' }}>{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color ?? '#E6EDF3' }}>
          {p.name}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export function DecisionPieChart({ data = [], loading = false }) {
  if (loading) return <div className="skeleton h-72 w-full" />
  const pieData = [
    { name: 'Skip Tests', value: data.skipped ?? 0 },
    { name: 'Run Tests', value: data.executed ?? 0 },
  ]
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie data={pieData} cx="50%" cy="50%" innerRadius={70} outerRadius={115} dataKey="value">
          <Cell fill={COLORS.skip} />
          <Cell fill={COLORS.run} />
        </Pie>
        <Tooltip content={<ChartTooltip />} />
        <Legend
          formatter={(value) => (
            <span style={{ color: '#8B949E', fontSize: 13 }}>{value}</span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function DecisionBarChart({ data = [], loading = false }) {
  if (loading) return <div className="skeleton h-56 sm:h-72 w-full" />
  const chartData = [
    { name: 'Skip Tests', value: data.skipped ?? 0 },
    { name: 'Run Tests', value: data.executed ?? 0 },
  ]
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} barSize={42}>
        <CartesianGrid strokeDasharray="3 3" stroke="#30363D" vertical={false} />
        <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 12 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 12 }} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: '#21262D' }} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          <Cell fill={COLORS.skip} />
          <Cell fill={COLORS.run} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function CommitTimelineChart({ data = [], loading = false }) {
  if (loading) return <div className="skeleton h-72 w-full" />
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#30363D" />
        <XAxis
          dataKey="date"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#8B949E', fontSize: 11 }}
        />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 11 }} />
        <Tooltip content={<ChartTooltip />} />
        <Line
          type="monotone"
          dataKey="commits"
          stroke={COLORS.line}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: COLORS.line }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export function TimeSavedBarChart({ data = [], loading = false }) {
  if (loading) return <div className="skeleton h-72 w-full" />
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#30363D" vertical={false} />
        <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 11 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#8B949E', fontSize: 11 }} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: '#21262D' }} />
        <Bar dataKey="minutes_saved" name="Minutes Saved" fill={COLORS.bar} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}
