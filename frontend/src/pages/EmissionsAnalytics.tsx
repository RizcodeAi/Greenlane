import { useEffect, useState } from 'react';
import { useAuth } from '../store/auth';
import { getEmissionsAnalytics, EmissionsAnalyticsData } from '../services/emissions';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts';

const COLORS = ['#16A34A', '#EAB308', '#EF4444', '#3B82F6', '#8B5CF6'];

export default function EmissionsAnalytics() {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState<EmissionsAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    getEmissionsAnalytics()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (loading) return <div className="p-8 text-slate-400 text-center">Loading analytics...</div>;
  if (error) return <div className="p-8 text-red-400 text-center">Error: {error}</div>;
  if (!data) return <div className="p-8 text-slate-400 text-center">No data available</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-navy-50">Emissions Analytics</h1>
        <p className="text-slate-400 mt-1">Visualize fleet CO2 output and fuel breakdown</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Main Area Chart */}
        <div className="lg:col-span-2 bg-navy-900 border border-navy-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-navy-50 mb-6">CO2 Emissions Over Time (mt)</h3>
          <div className="h-[400px] w-full">
            {data.time_series.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.time_series} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCo2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#16A34A" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#16A34A" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="name" stroke="#64748B" tick={{fill: '#94A3B8'}} />
                  <YAxis stroke="#64748B" tick={{fill: '#94A3B8'}} />
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', color: '#F8FAFC' }}
                    itemStyle={{ color: '#4ADE80' }}
                  />
                  <Area type="monotone" dataKey="co2" stroke="#16A34A" fillOpacity={1} fill="url(#colorCo2)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500">Not enough data to render chart</div>
            )}
          </div>
        </div>

        {/* Pie Chart */}
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-6 flex flex-col">
          <h3 className="text-lg font-bold text-navy-50 mb-6">CO2 by Fuel Type</h3>
          <div className="h-[400px] w-full flex-1">
            {data.fuel_breakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.fuel_breakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={80}
                    outerRadius={120}
                    paddingAngle={5}
                    dataKey="value"
                    stroke="none"
                  >
                    {data.fuel_breakdown.map((_entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', color: '#F8FAFC', borderRadius: '8px' }}
                    itemStyle={{ color: '#F8FAFC' }}
                  />
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ color: '#94A3B8' }}/>
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500">Not enough data to render chart</div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
