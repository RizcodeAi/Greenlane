import { ThemeToggle } from './ThemeToggle';
import { useAuth } from '../store/auth';

export default function Navbar() {
  const { user, logout } = useAuth();

  const handleLogout = async () => { await logout(); };

  return (
    <nav className="bg-white dark:bg-navy-950 border-b border-slate-200 dark:border-navy-800 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-green-500 text-2xl font-bold">Green</span>
        <span className="text-navy-950 dark:text-navy-100 text-2xl font-bold">Lane</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-slate-600 dark:text-slate-400 text-sm">{user?.email}</span>
        <span className="bg-slate-100 dark:bg-navy-800 text-slate-800 dark:text-slate-300 px-3 py-1 rounded text-xs font-medium">{user?.role}</span>
        <ThemeToggle />
        <button onClick={handleLogout} className="text-sm text-red-400 hover:text-red-300 transition-colors">Logout</button>
      </div>
    </nav>
  );
}
