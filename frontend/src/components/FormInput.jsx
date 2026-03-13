export default function FormInput({ label, id, ...props }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-xs font-semibold uppercase tracking-wider text-[#a1a1aa] ml-1">{label}</label>
      <input
        id={id}
        {...props}
        className="w-full bg-black/40 border border-white/10 text-white p-3.5 rounded-xl text-sm
        focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 focus:bg-white/5
        placeholder:text-[#71717a] transition-all shadow-inner"
      />
    </div>
  )
}