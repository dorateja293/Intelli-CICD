export default function ChartCard({ title, subtitle, children }) {
  return (
    <div className="glass-panel p-6 md:p-8 min-h-[360px] flex flex-col relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
      <div className="mb-8 relative z-10">
        <h3 className="section-title text-white">{title}</h3>
        {subtitle && <p className="text-xs text-[#a1a1aa] mt-1">{subtitle}</p>}
      </div>
      <div className="flex-1 w-full relative z-10">
        {children}
      </div>
    </div>
  )
}