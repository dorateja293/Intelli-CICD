export default function Button({ children, variant = 'primary', size = 'default', ...props }) {
  const baseStyle = "inline-flex items-center justify-center font-semibold transition-all duration-300 w-full rounded-xl"
  
  const sizes = {
    default: "px-6 py-3.5 text-sm",
    lg: "px-8 py-4 text-base",
    sm: "px-4 py-2 text-xs"
  }
  
  const styles = {
    primary: "bg-white text-black hover:bg-gray-200 shadow-[0_0_20px_rgba(255,255,255,0.15)] hover:shadow-[0_0_25px_rgba(255,255,255,0.25)] hover:-translate-y-0.5",
    indigo: "bg-indigo-500 text-white hover:bg-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] hover:-translate-y-0.5 border border-indigo-400/50",
    secondary: "bg-white/5 border border-white/10 text-white hover:bg-white/10 backdrop-blur-sm",
    ghost: "bg-transparent text-[#a1a1aa] hover:text-white hover:bg-white/5"
  }
  
  return (
    <button className={`${baseStyle} ${sizes[size]} ${styles[variant]}`} {...props}>
      {children}
    </button>
  )
}