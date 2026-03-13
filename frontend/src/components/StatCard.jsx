export default function StatCard({ title, value, subValue, trend, icon: Icon, colorClass, gradientClass }) {
  const isPositive = trend > 0;
  return (
    <div className="glass-panel p-6 relative overflow-hidden group">
      <div className={`absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-500 ${gradientClass}`}></div>
      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-[#a1a1aa] text-sm font-medium mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
            {subValue && <span className="text-sm font-medium text-[#71717a]">{subValue}</span>}
          </div>
          {trend && (
            <p className={`text-xs font-semibold mt-2 flex items-center gap-1 ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isPositive ? '↑' : '↓'} {Math.abs(trend)}% from last week
            </p>
          )}
        </div>
        <div className={`p-3 rounded-2xl ${colorClass} bg-opacity-10 backdrop-blur-sm border border-white/5`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </div>
  )
}