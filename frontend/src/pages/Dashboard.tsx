import { useEffect, useState } from 'react';
import { useAuth } from '../store/auth';
import { getDashboardSummary } from '../services/dashboard';
import { FleetSummary } from '../services/dashboard';
import FleetMap from '../components/FleetMap';
import { getMapVessels } from '../services/dashboard';
import { MapVessel } from '../services/dashboard';

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [vessels, setVessels] = useState<MapVessel[]>([]);
  const [, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) return;
    Promise.all([
      getDashboardSummary().then((r) => setSummary(r.data)).catch(console.error),
      getMapVessels().then((r) => setVessels(r.data)).catch(console.error),
    ]).finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (!isAuthenticated) {
    return (
      <div className="p-8"><a href="/login" className="text-green-400 underline">Login required</a></div>
    );
  }

  const complianceCards = [
    { label: 'Green (Compliant)', count: summary?.green_count || 0, color: '#16A34A', bg: 'bg-green-900/40', border: 'border-green-700/50' },
    { label: 'Yellow (Warning)', count: summary?.yellow_count || 0, color: '#EAB308', bg: 'bg-yellow-900/40', border: 'border-yellow-700/50' },
    { label: 'Red (Non-Compliant)', count: summary?.red_count || 0, color: '#EF4444', bg: 'bg-red-900/40', border: 'border-red-700/50' },
  ];

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-4">
      {/* Hero header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy-50">Fleet Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Welcome back, <span className="text-green-400 font-medium">{user?.full_name || user?.email}</span></p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Live data
        </div>
      </div>

      {/* Top stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
          <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Total Vessels</p>
          <p className="text-3xl font-bold text-navy-50">{summary?.total_ships || 0}</p>
        </div>
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
          <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Active Fleet</p>
          <p className="text-3xl font-bold text-navy-50">{summary?.active_ships || 0}</p>
        </div>
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
          <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">YTD CO2 (tonnes)</p>
          <p className="text-3xl font-bold text-green-400">{summary?.total_co2_ytd || 0}</p>
        </div>
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
          <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">CII Rating</p>
          <p className="text-3xl font-bold text-navy-50">{summary?.avg_cii_rating || 'N/A'}</p>
        </div>
      </div>

      {/* Compliance status cards */}
      <div className="grid grid-cols-3 gap-3">
        {complianceCards.map((card) => (
          <div key={card.label} className={`${card.bg} border ${card.border} rounded-lg p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: card.color }}></span>
              <p className="text-xs uppercase tracking-wider text-slate-400">{card.label}</p>
            </div>
            <p className="text-4xl font-bold" style={{ color: card.color }}>{card.count}</p>
          </div>
        ))}
      </div>

      {/* Main map + alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4" style={{ height: 'calc(100vh - 320px)', minHeight: '400px' }}>
        {/* Map takes 2/3 */}
        <div className="lg:col-span-2 bg-navy-900 border border-navy-800 rounded-lg overflow-hidden" style={{ minHeight: '300px' }}>
          <FleetMap />
        </div>

        {/* Activity feed sidebar takes 1/3 */}
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-4 overflow-y-auto">
          <h3 className="text-sm font-bold text-navy-50 mb-3 uppercase tracking-wider">Recent Fleet Activity</h3>
          <div className="space-y-3">
            {vessels.slice(0, 8).map((vessel, idx) => (
              <div key={`${vessel.imo}-${idx}`} className="flex items-center gap-3 p-2 rounded-lg bg-navy-950 border border-navy-800 hover:border-navy-600 transition-colors cursor-default">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{
                  backgroundColor: vessel.compliance_status === 'Compliant' ? '#16A34A'
                    : vessel.compliance_status === 'Warning' ? '#EAB308' : '#EF4444'
                }}></span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-navy-100 truncate">{vessel.name}</p>
                  <p className="text-[10px] text-slate-500">{vessel.destination} &middot; {vessel.speed_knots} kts</p>
                </div>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  vessel.compliance_status === 'Compliant' ? 'bg-green-900/60 text-green-300'
                  : vessel.compliance_status === 'Warning' ? 'bg-yellow-900/60 text-yellow-300'
                  : 'bg-red-900/60 text-red-300'
                }`}>
                  {vessel.compliance_status}
                </span>
              </div>
            ))}
          </div>
          {vessels.length === 0 && (
            <p className="text-slate-500 text-xs text-center py-8">No vessel data available</p>
          )}
        </div>
      </div>
    </div>
  );
}
