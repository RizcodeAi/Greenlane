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

      <div className="mt-8 px-3">
        <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">Live Fleet Control</p>
        <button
          onClick={() => window.dispatchEvent(new CustomEvent('center-fleet'))}
          className="w-full text-left px-4 py-2 rounded-lg text-slate-300 hover:text-white hover:bg-navy-800 transition-colors text-sm border border-navy-700 shadow-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Focus 3D Globe
        </button>
      </div>

    </aside>
  );
}
