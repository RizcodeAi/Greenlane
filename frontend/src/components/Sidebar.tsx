import { Link } from 'react-router-dom';
import { useAuth } from '../store/auth';

export default function Sidebar() {
  const { user } = useAuth();
  const navItems = [
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Fleet', path: '/fleet' },
    { label: 'Voyage Logs', path: '/voyages' },
    { label: 'Emissions', path: '/emissions' },
    { label: 'Reports', path: '/reports' },
  ];

  return (
    <aside className="w-64 bg-navy-950 border-r border-navy-800 min-h-[calc(100vh-64px)] p-4 flex flex-col gap-2">
      <div className="mb-6 px-3 py-2">
        <p className="text-slate-500 text-xs uppercase tracking-wider">Organization</p>
        <p className="text-navy-100 font-medium text-sm">{user?.org_id || 'N/A'}</p>
      </div>
      {navItems.map((item) => (
        <Link key={item.path} to={item.path}
          className="px-4 py-2.5 rounded-lg text-slate-400 hover:text-green-400 hover:bg-navy-900 transition-colors text-sm">
          {item.label}
        </Link>
      ))}
    </aside>
  );
}
