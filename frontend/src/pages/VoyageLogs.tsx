import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { getVoyages, deleteVoyage, createVoyage, Voyage } from '../services/emissions';
import AddVoyageModal from '../components/AddVoyageModal';

export default function VoyageLogs() {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [voyages, setVoyages] = useState<Voyage[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [assetFilter, setAssetFilter] = useState('');
  const [periodFilter, setPeriodFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchVoyages = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (search) params.search = search;
      if (assetFilter) params.asset_id = assetFilter;
      if (periodFilter) params.period = periodFilter;
      const res = await getVoyages(params);
      setVoyages(res.voyages);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to fetch voyages:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchVoyages(); }, [search, assetFilter, periodFilter, page]);

  const handleCreate = async (data: any) => {
    setModalLoading(true);
    try {
      await createVoyage(data);
      setModalOpen(false);
      fetchVoyages();
    } catch (err) {
      console.error('Failed to create voyage:', err);
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this voyage?')) return;
    setDeletingId(id);
    try {
      await deleteVoyage(id);
      fetchVoyages();
    } catch (err) {
      console.error('Failed to delete voyage:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const FUEL_LABELS: Record<string, string> = {
    HFO: 'HFO', MGO: 'MGO', LNG: 'LNG', Methanol: 'Methanol',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-navy-50">Voyage Logs</h1>
          <p className="text-slate-400 mt-1">Track and manage fleet voyages</p>
        </div>
        <button onClick={() => setModalOpen(true)}
          className="bg-green-600 hover:bg-green-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2">
          <span>+</span> Log Voyage
        </button>
      </div>

      {/* Filters */}
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-slate-500 mb-1">Search</label>
            <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search ports..."
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
          </div>
          <div className="w-44">
            <label className="block text-xs text-slate-500 mb-1">Asset</label>
            <input type="text" value={assetFilter} onChange={(e) => { setAssetFilter(e.target.value); setPage(1); }}
              placeholder="Asset ID"
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
          </div>
          <div className="w-44">
            <label className="block text-xs text-slate-500 mb-1">Period</label>
            <select value={periodFilter} onChange={(e) => { setPeriodFilter(e.target.value); setPage(1); }}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
              <option value="">All</option>
              <option value={new Date().getFullYear().toString()}>This Year</option>
              <option value={`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`}>This Month</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-slate-400 text-center py-12">Loading voyages...</div>
      ) : voyages.length === 0 ? (
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-12 text-center">
          <p className="text-slate-400 text-lg">No voyages found</p>
          <p className="text-slate-600 text-sm mt-2">Log your first voyage to get started</p>
        </div>
      ) : (
        <div className="bg-navy-900 border border-navy-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-800">
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Voyage ID</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Route</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Dates</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Fuel</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Fuel (MT)</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Distance (NM)</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">CO2 (t)</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">CO2e (t)</th>
                <th className="text-right text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-800">
              {voyages.map((voyage) => {
                const em = voyage.emissions;
                const emissionsData = em?.emissions || { co2: 0, ch4: 0, n2o: 0, sox: 0, nox: 0 };
                const co2e = em?.co2_equivalent || 0;
                return (
                  <tr key={voyage.id} className="hover:bg-navy-800/50 transition-colors">
                    <td className="px-4 py-3 text-sm text-slate-300 font-mono">{voyage.id.slice(0, 8)}...</td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-navy-100">{voyage.departure_port}</div>
                      <div className="text-xs text-slate-500">{voyage.arrival_port}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {new Date(voyage.departure_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">{FUEL_LABELS[voyage.fuel_type] || voyage.fuel_type}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{voyage.fuel_consumed_mt}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{voyage.distance_nm}</td>
                    <td className="px-4 py-3 text-sm text-green-400">{(emissionsData.co2 || 0).toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm text-green-400">{co2e.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-sm">
                      <button onClick={() => navigate(`/voyages/${voyage.id}`)} className="text-slate-400 hover:text-green-400 mr-3">View</button>
                      <button onClick={() => handleDelete(voyage.id)}
                        disabled={deletingId === voyage.id}
                        className="text-slate-400 hover:text-red-400 disabled:opacity-50">
                        {deletingId === voyage.id ? '...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-slate-400 text-sm">
            Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total} voyages
          </p>
          <div className="flex gap-2">
            <button onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="bg-navy-800 border border-navy-700 text-slate-400 px-3 py-1.5 rounded text-sm hover:bg-navy-700 disabled:opacity-50">
              Previous
            </button>
            <button onClick={() => setPage((p) => p + 1)}
              disabled={page * 20 >= total}
              className="bg-navy-800 border border-navy-700 text-slate-400 px-3 py-1.5 rounded text-sm hover:bg-navy-700 disabled:opacity-50">
              Next
            </button>
          </div>
        </div>
      )}

      {/* Modal */}
      <AddVoyageModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSubmit={handleCreate} loading={modalLoading} />
    </div>
  );
}
