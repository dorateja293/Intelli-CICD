export default function StatCard({ title, value }) {
  return (
    <div className="bg-githubCard border border-githubBorder p-8 rounded-xl hover:shadow-lg transition-shadow">
      <h3 className="text-githubTextSecondary text-sm font-semibold mb-2">{title}</h3>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}