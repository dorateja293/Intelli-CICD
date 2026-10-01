import { Link, useLocation, useNavigate } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('intelli_ci_token');
    localStorage.removeItem('intelli_ci_user');
    navigate('/login', { replace: true });
  };
  
  const navItems = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Projects', path: '/projects' },
    { name: 'Commits', path: '/commits' },
    { name: 'Analytics', path: '/analytics' },
    { name: 'Predict', path: '/predict' },
    { name: 'Logs', path: '/logs' },
    { name: 'Profile', path: '/profile' }
  ];

  return (
    <div className="w-64 bg-githubBg border-r border-githubBorder flex flex-col">
      <div className="h-16 flex items-center px-6 font-bold text-xl border-b border-githubBorder text-white">
        Intelli-CI
      </div>
      <div className="flex-1 py-6 flex flex-col gap-2 px-4">
        {navItems.map((item) => {
          const isActive = location.pathname.startsWith(item.path);
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-githubCard text-white' 
                  : 'text-githubTextSecondary hover:text-white hover:bg-githubCard cursor-pointer'
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </div>
      <div className="p-4 border-t border-githubBorder">
        <button
          type="button"
          onClick={handleLogout}
          className="w-full text-left px-4 py-2 rounded-lg text-sm font-medium text-githubTextSecondary hover:text-white hover:bg-githubCard cursor-pointer transition-colors"
        >
          Logout
        </button>
      </div>
    </div>
  );
}
