export default function Avatar({ name = 'User', size = 36 }) {
  const initials = name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')

  // Generate consistent color from name
  const colors = ['#238636', '#1f6feb', '#a371f7', '#db6d28', '#e3b341']
  const colorIndex =
    name.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % colors.length
  const bg = colors[colorIndex]

  return (
    <div
      className="flex items-center justify-center rounded-full font-semibold shrink-0 select-none"
      style={{ width: size, height: size, background: bg, fontSize: size * 0.38, color: '#fff' }}
      title={name}
    >
      {initials}
    </div>
  )
}
