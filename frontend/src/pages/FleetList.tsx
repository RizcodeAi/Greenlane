import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getShips, deleteShip, createShip, Ship } from '../services/fleet';
import AddShipModal from '../components/AddShipModal';

export default function FleetList() {
  const [ships, setShips] = useState<Ship[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [vesselTypeFilter, setVesselTypeFilter] = useState('');
  const [fuelTypeFilter, setFuelTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const VESSEL_TYPES = ['Bulk Carrier', 'Tanker', 'Container', 'Ro-Ro', 'General Cargo', 'Gas Carrier'];
  const FUEL_TYPES = ['HFO', 'MGO', 'LNG', 'Methanol'];

  const fetchShips = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = { page, page_size: 20 };
      if (search) params.search = search;
      if (vesselTypeFilter) params.vessel_type = vesselTypeFilter;
      if (fuelTypeFilter) params.fuel_type = fuelTypeFilter;
      if (statusFilter) params.status = statusFilter;
      const res = await getShips(params);
      setShips(res.ships);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to fetch ships:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchShips(); }, [search, vesselTypeFilter, fuelTypeFilter, statusFilter, page]);

  const handleCreate = async (data: Omit<Ship, 'id' | 'org_id' | 'created_at' | 'updated_at'>) => {
    setModalLoading(true);
    try {
      await createShip(data as any);
      setModalOpen(false);
      fetchShips();
    } catch (err) {
      console.error('Failed to create ship:', err);
    } finally {
      setModalLoading(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete "${name}"?`)) return;
    setDeletingId(id);
    try {
      await deleteShip(id);
      fetchShips();
    } catch (err) {
      console.error('Failed to delete ship:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const VESSEL_TYPE_LABELS: Record<string, string> = {
    'Bulk Carrier': 'Bulk Carrier', 'Tanker': 'Tanker', 'Container': 'Container',
    'Ro-Ro': 'Ro-Ro', 'General Cargo': 'General Cargo', 'Gas Carrier': 'Gas Carrier',
  };

  const statusColors: Record<string, string> = {
    active: 'bg-green-500/20 text-green-400 border-green-500/30',
    inactive: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  const fuelLabels: Record<string, string> = {
    HFO: 'HFO', MGO: 'MGO', LNG: 'LNG', Methanol: 'Methanol',
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-navy-50">Fleet Management</h1>
          <p className="text-slate-400 mt-1">Manage your vessel fleet</p>
        </div>
        <button onClick={() => setModalOpen(true)}
          className="bg-green-600 hover:bg-green-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2">
          <span>+</span> Add Vessel
        </button>
      </div>

      {/* Filters */}
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs text-slate-500 mb-1">Search</label>
            <input type="text" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search by name or IMO..."
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500" />
          </div>
          <div className="w-44">
            <label className="block text-xs text-slate-500 mb-1">Vessel Type</label>
            <select value={vesselTypeFilter} onChange={(e) => { setVesselTypeFilter(e.target.value); setPage(1); }}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
              <option value="">All Types</option>
              {VESSEL_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="w-44">
            <label className="block text-xs text-slate-500 mb-1">Fuel Type</label>
            <select value={fuelTypeFilter} onChange={(e) => { setFuelTypeFilter(e.target.value); setPage(1); }}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
              <option value="">All Fuels</option>
              {FUEL_TYPES.map((f) => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div className="w-44">
            <label className="block text-xs text-slate-500 mb-1">Status</label>
            <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-green-500">
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="text-slate-400 text-center py-12">Loading fleet...</div>
      ) : ships.length === 0 ? (
        <div className="bg-navy-900 border border-navy-800 rounded-lg p-12 text-center">
          <p className="text-slate-400 text-lg">No vessels found</p>
          <p className="text-slate-600 text-sm mt-2">Add your first vessel to get started</p>
        </div>
      ) : (
        <div className="bg-navy-900 border border-navy-800 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-navy-800">
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Ship Name</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">IMO</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Flag</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Type</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">GT</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">DWT</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Fuel</th>
                <th className="text-left text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Status</th>
                <th className="text-right text-xs text-slate-500 uppercase tracking-wider font-medium px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-navy-800">
              {ships.map((ship) => (
                <tr key={ship.id} className="hover:bg-navy-800/50 transition-colors">
                  <td className="px-4 py-3">
                    <Link to={`/fleet/${ship.id}`} className="text-green-400 hover:text-green-300 font-medium text-sm">
                      {ship.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-300">{ship.imo_number}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{ship.flag_state}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{VESSEL_TYPE_LABELS[ship.vessel_type] || ship.vessel_type}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{ship.gross_tonnage}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{ship.dwt}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{fuelLabels[ship.fuel_type] || ship.fuel_type}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusColors[ship.status] || 'bg-gray-500/20 text-gray-400'}`}>
                      {ship.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm">
                    <Link to={`/fleet/${ship.id}`} className="text-slate-400 hover:text-green-400 mr-3">View</Link>
                    <button onClick={() => handleDelete(ship.id, ship.name)}
                      disabled={deletingId === ship.id}
                      className="text-slate-400 hover:text-red-400 disabled:opacity-50">
                      {deletingId === ship.id ? '...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-slate-400 text-sm">
            Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, total)} of {total} vessels
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
      <AddShipModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSubmit={handleCreate} loading={modalLoading} />
    </div>
  );
}
