import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getShipById, deleteShip, Ship } from '../services/fleet';

export default function ShipDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ship, setShip] = useState<Ship | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [, _setActionLoading] = useState(false);

  const FUEL_LABELS: Record<string, string> = { HFO: 'HFO', MGO: 'MGO', LNG: 'LNG', Methanol: 'Methanol' };
  const VESSEL_TYPE_LABELS: Record<string, string> = {
    'Bulk Carrier': 'Bulk Carrier', 'Tanker': 'Tanker', 'Container': 'Container',
    'Ro-Ro': 'Ro-Ro', 'General Cargo': 'General Cargo', 'Gas Carrier': 'Gas Carrier',
  };

  useEffect(() => {
    const fetchShip = async () => {
      try {
        const res = await getShipById(id!);
        setShip(res.ship);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load ship details');
      } finally {
        setLoading(false);
      }
    };
    fetchShip();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this vessel? This action cannot be undone.')) return;
    setDeleting(true);
    try {
      await deleteShip(id!);
      navigate('/fleet');
    } catch (err) {
      console.error('Delete failed:', err);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return <div className="p-6 max-w-7xl mx-auto text-slate-400">Loading vessel details...</div>;
  }

  if (error || !ship) {
    return (
      <div className="p-6 max-w-7xl mx-auto text-center">
        <h2 className="text-2xl font-bold text-navy-50 mb-4">Vessel Not Found</h2>
        <p className="text-slate-400 mb-6">{error || 'The requested vessel could not be found.'}</p>
        <button onClick={() => navigate('/fleet')} className="bg-green-600 hover:bg-green-500 text-white font-semibold px-5 py-2.5 rounded-lg transition-colors">
          Back to Fleet
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <button onClick={() => navigate('/fleet')} className="text-slate-400 hover:text-green-400 text-sm mb-2 inline-flex items-center gap-1">
            &larr; Back to Fleet
          </button>
          <h1 className="text-3xl font-bold text-navy-50">{ship.name}</h1>
          <p className="text-slate-400 mt-1">IMO {ship.imo_number}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(`/fleet/${ship.id}/edit`)}
            className="bg-navy-700 hover:bg-navy-600 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm">
            Edit
          </button>
          <button onClick={handleDelete} disabled={deleting}
            className="bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600/30 font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm disabled:opacity-50">
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
          ship.status === 'active'
            ? 'bg-green-500/20 text-green-400 border-green-500/30'
            : 'bg-red-500/20 text-red-400 border-red-500/30'
        }`}>
          {ship.status.charAt(0).toUpperCase() + ship.status.slice(1)}
        </span>
      </div>

      {/* Spec Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'IMO Number', value: ship.imo_number, icon: '📋' },
          { label: 'Flag State', value: ship.flag_state, icon: '🚩' },
          { label: 'Vessel Type', value: VESSEL_TYPE_LABELS[ship.vessel_type] || ship.vessel_type, icon: '🚢' },
          { label: 'Gross Tonnage', value: `${ship.gross_tonnage} GT`, icon: '📏' },
          { label: 'Deadweight Tonnage', value: `${ship.dwt} DWT`, icon: '⚖️' },
          { label: 'Fuel Type', value: FUEL_LABELS[ship.fuel_type] || ship.fuel_type, icon: '⛽' },
        ].map((spec) => (
          <div key={spec.label} className="bg-navy-900 border border-navy-800 rounded-lg p-5">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">{spec.label}</p>
            <p className="text-lg font-semibold text-navy-50">{spec.value}</p>
          </div>
        ))}
      </div>

      {/* Engine / Additional Info Section */}
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-bold text-navy-50 mb-4">Vessel Specifications</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400 mb-1">IMO Number</p>
            <p className="text-white font-medium">{ship.imo_number}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Flag State</p>
            <p className="text-white font-medium">{ship.flag_state}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Vessel Type</p>
            <p className="text-white font-medium">{VESSEL_TYPE_LABELS[ship.vessel_type] || ship.vessel_type}</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Gross Tonnage</p>
            <p className="text-white font-medium">{ship.gross_tonnage} GT</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Deadweight Tonnage</p>
            <p className="text-white font-medium">{ship.dwt} DWT</p>
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Fuel Type</p>
            <p className="text-white font-medium">{FUEL_LABELS[ship.fuel_type] || ship.fuel_type}</p>
          </div>
        </div>
      </div>

      {/* Meta */}
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-4">
        <div className="flex items-center gap-6 text-sm text-slate-500">
          <span>Created: {new Date(ship.created_at).toLocaleDateString()}</span>
          {ship.updated_at && <span>Updated: {new Date(ship.updated_at).toLocaleDateString()}</span>}
          <span>Org ID: {ship.org_id}</span>
        </div>
      </div>
    </div>
  );
}
