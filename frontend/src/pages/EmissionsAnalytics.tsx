import React, { useEffect, useState } from 'react';
import { useAuth } from '../store/auth';
import { getEmissionsSummaryData, EmissionsSummary } from '../services/emissions';

export default function EmissionsAnalytics() {
  const { isAuthenticated } = useAuth();
  const [summary, setSummary] = useState<EmissionsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('month');
  const [groupBy, setGroupBy] = useState('vessel');

  useEffect(() => {
    if (!isAuthenticated) return;
    getEmissionsSummaryData({ period, group_by: groupBy })
      .then((r) => setSummary(r))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated, period, groupBy]);

  if (!isAuthenticated) {
    return <div className="p-8"><a href="/login" className="text-green-400 underline">Login required</a></div>;
  }

  const fuelTypes = ['HFO', 'MGO', 'LNG', 'Methanol'];
  const fuelColors = { HFO: '#F97316', MGO: '#3B82F6', LNG: '#06B6D4', Methanol: '#A855F7' };
  const pollutantColors = { co2: '#22C55E', ch4: '#F59E0B', n2o: '#EF4444', sox: '#8B5CF6', nox: '#3B82F6' };
  const pollutantLabels = { co2: 'CO2', ch4: 'CH4', n2o: 'N2O', sox: 'SOx', nox: 'NOx' };

  const maxFuel = Math.max(...Object.values(summary?.by_fuel_type || {}).map((v: any) => v.co2e), 1);
  const maxPoll = Math.max(...Object.values(summary?.by_pollutant || {}), 1);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-navy-50">Emissions Analytics</h1>
          <p className="text-slate-400 mt-1">Fleet emissions overview and breakdowns</p>
        </div>
        <div className="flex gap-2">
          <select value={period} onChange={(e) => setPeriod(e.target.value)}
            className="bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
            <option value="month">Month</option>
            <option value="quarter">Quarter</option>
            <option value="year">Year</option>
          </select>
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}
            className="bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
            <option value="vessel">Group by Vessel</option>
            <option value="fuel_type">Group by Fuel Type</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="text-slate-400 text-center py-12">Loading emissions data...</div>
      ) : (
        <>
          {/* Summary stat cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
              <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Total CO2</p>
              <p className="text-2xl font-bold text-green-400">{summary?.total_co2?.toFixed(1) || 0} t</p>
            </div>
            <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
              <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Total CO2e</p>
              <p className="text-2xl font-bold text-navy-50">{summary?.total_co2e?.toFixed(1) || 0} t</p>
            </div>
            <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
              <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Total Fuel</p>
              <p className="text-2xl font-bold text-navy-50">{summary?.total_fuel_mt?.toFixed(1) || 0} MT</p>
            </div>
            <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
              <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">Avg EEOI</p>
              <p className="text-2xl font-bold text-navy-50">{summary?.avg_eefi?.toFixed(2) || 'N/A'}</p>
            </div>
          </div>

          {/* Fuel breakdown */}
          <div className="bg-navy-900 border border-navy-800 rounded-lg p-6">
            <h2 className="text-lg font-bold text-navy-50 mb-4">Fuel Type Breakdown</h2>
            <div className="space-y-3">
              {fuelTypes.map((ft) => {
                const data = summary?.by_fuel_type?.[ft];
                const co2e = data?.co2e || 0;
                const pct = maxFuel > 0 ? (co2e / maxFuel) * 100 : 0;
                return (
                  <div key={ft} className="flex items-center gap-3">
                    <div className="w-24 text-sm text-slate-400">{ft}</div>
                    <div className="flex-1 bg-navy-800 rounded-full h-6 overflow-hidden relative">
                      <div className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: fuelColors[ft] }} />
                    </div>
                    <div className="w-28 text-right text-sm">
                      <span className="text-navy-100 font-medium">{co2e.toFixed(2)} t</span>
                      <span className="text-slate-500 ml-2">CO2e</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pollutants breakdown */}
          <div className="bg-navy-900 border border-navy-800 rounded-lg p-6">
            <h2 className="text-lg font-bold text-navy-50 mb-4">Pollutant Breakdown</h2>
            <div className="grid grid-cols-5 gap-3">
              {Object.entries(summary?.by_pollutant || {}).map(([key, value]) => (
                <div key={key} className="bg-navy-800 rounded-lg p-4 text-center">
                  <p className="text-xs text-slate-500 uppercase mb-1">{pollutantLabels[key as string] || key}</p>
                  <p className="text-2xl font-bold" style={{ color: pollutantColors[key as string] || '#fff' }}>
                    {(value as number).toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">tonnes</p>
                </div>
              ))}
            </div>
          </div>

          {/* Vessel breakdown (if grouped by vessel) */}
          {groupBy === 'vessel' && summary?.by_vessel && Object.keys(summary.by_vessel).length > 0 && (
            <div className="bg-navy-900 border border-navy-800 rounded-lg p-6">
              <h2 className="text-lg font-bold text-navy-50 mb-4">Per-Vessel Breakdown</h2>
              <div className="space-y-3">
                {Object.entries(summary.by_vessel).map(([vesselId, data]: [string, any]) => (
                  <div key={vesselId} className="flex items-center gap-3">
                    <div className="w-32 text-sm text-slate-400 truncate">{vesselId}</div>
                    <div className="flex-1 bg-navy-800 rounded-full h-6 overflow-hidden">
                      <div className="h-full rounded-full bg-green-600 transition-all duration-500"
                        style={{ width: `${maxFuel > 0 ? (data.co2e / maxFuel) * 100 : 0}%` }} />
                    </div>
                    <div className="w-28 text-right text-sm text-navy-100">{data.co2e.toFixed(2)} t CO2e</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
