import { useAuth } from '../store/auth';

export default function Navbar() {
  const { user, logout } = useAuth();

  const handleLogout = async () => { await logout(); };

  return (
    <nav className="bg-navy-950 border-b border-navy-800 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className="text-green-500 text-2xl font-bold">Green</span>
        <span className="text-navy-100 text-2xl font-bold">Lane</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-slate-400 text-sm">{user?.email}</span>
        <span className="bg-navy-800 text-slate-300 px-3 py-1 rounded text-xs font-medium">{user?.role}</span>
        <button onClick={handleLogout} className="text-sm text-red-400 hover:text-red-300 transition-colors">Logout</button>
      </div>
    </nav>
  );
}
