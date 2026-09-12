import React, { useState } from 'react';

interface VoyageFormData {
  asset_id: string;
  departure_port: string;
  arrival_port: string;
  departure_date: string;
  arrival_date: string;
  fuel_type: string;
  fuel_consumed_mt: string;
  distance_nm: string;
  cargo_mt: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: VoyageFormData) => Promise<void>;
  loading: boolean;
}

const VALID_FUEL_TYPES = ['HFO', 'MGO', 'LNG', 'Methanol'];

export default function AddVoyageModal({ isOpen, onClose, onSubmit, loading }: Props) {
  const [form, setForm] = useState<VoyageFormData>({
    asset_id: '',
    departure_port: '',
    arrival_port: '',
    departure_date: '',
    arrival_date: '',
    fuel_type: '',
    fuel_consumed_mt: '',
    distance_nm: '',
    cargo_mt: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form.asset_id.trim()) newErrors.asset_id = 'Asset ID is required';
    if (!form.departure_port.trim()) newErrors.departure_port = 'Departure port is required';
    if (!form.arrival_port.trim()) newErrors.arrival_port = 'Arrival port is required';
    if (!form.departure_date) newErrors.departure_date = 'Departure date is required';
    if (!form.fuel_type) newErrors.fuel_type = 'Fuel type is required';
    if (!form.fuel_consumed_mt || isNaN(Number(form.fuel_consumed_mt)) || Number(form.fuel_consumed_mt) <= 0)
      newErrors.fuel_consumed_mt = 'Valid fuel consumed is required';
    if (!form.distance_nm || isNaN(Number(form.distance_nm)) || Number(form.distance_nm) <= 0)
      newErrors.distance_nm = 'Valid distance is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      asset_id: form.asset_id.trim(),
      departure_port: form.departure_port.trim(),
      arrival_port: form.arrival_port.trim(),
      departure_date: form.departure_date,
      arrival_date: form.arrival_date || undefined as any,
      fuel_type: form.fuel_type,
      fuel_consumed_mt: Number(form.fuel_consumed_mt),
      distance_nm: Number(form.distance_nm),
      cargo_mt: Number(form.cargo_mt) || 0,
    });
  };

  const handleClose = () => {
    setForm({
      asset_id: '', departure_port: '', arrival_port: '',
      departure_date: '', arrival_date: '', fuel_type: '',
      fuel_consumed_mt: '', distance_nm: '', cargo_mt: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-navy-900 border border-navy-700 rounded-xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-navy-50">Log New Voyage</h2>
          <button onClick={handleClose} className="text-slate-400 hover:text-white text-xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Asset/Asset ID *</label>
            <input type="text" value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: e.target.value })}
              className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.asset_id ? 'border-red-500' : 'border-navy-600'}`}
              placeholder="e.g. asset-001" required />
            {errors.asset_id && <p className="text-red-400 text-xs mt-1">{errors.asset_id}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Departure Port *</label>
              <input type="text" value={form.departure_port} onChange={(e) => setForm({ ...form, departure_port: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.departure_port ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. Rotterdam" required />
              {errors.departure_port && <p className="text-red-400 text-xs mt-1">{errors.departure_port}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Arrival Port *</label>
              <input type="text" value={form.arrival_port} onChange={(e) => setForm({ ...form, arrival_port: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.arrival_port ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. Singapore" required />
              {errors.arrival_port && <p className="text-red-400 text-xs mt-1">{errors.arrival_port}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Departure Date *</label>
              <input type="datetime-local" value={form.departure_date} onChange={(e) => setForm({ ...form, departure_date: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.departure_date ? 'border-red-500' : 'border-navy-600'}`}
                required />
              {errors.departure_date && <p className="text-red-400 text-xs mt-1">{errors.departure_date}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Arrival Date</label>
              <input type="datetime-local" value={form.arrival_date} onChange={(e) => setForm({ ...form, arrival_date: e.target.value })}
                className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Fuel Type *</label>
              <select value={form.fuel_type} onChange={(e) => setForm({ ...form, fuel_type: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.fuel_type ? 'border-red-500' : 'border-navy-600'}`}
                required>
                <option value="">Select fuel</option>
                {VALID_FUEL_TYPES.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
              {errors.fuel_type && <p className="text-red-400 text-xs mt-1">{errors.fuel_type}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Cargo (MT)</label>
              <input type="number" value={form.cargo_mt} onChange={(e) => setForm({ ...form, cargo_mt: e.target.value })}
                className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500"
                placeholder="0" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Fuel Consumed (MT) *</label>
              <input type="number" value={form.fuel_consumed_mt} onChange={(e) => setForm({ ...form, fuel_consumed_mt: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.fuel_consumed_mt ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. 150" required />
              {errors.fuel_consumed_mt && <p className="text-red-400 text-xs mt-1">{errors.fuel_consumed_mt}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Distance (NM) *</label>
              <input type="number" value={form.distance_nm} onChange={(e) => setForm({ ...form, distance_nm: e.target.value })}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.distance_nm ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. 5000" required />
              {errors.distance_nm && <p className="text-red-400 text-xs mt-1">{errors.distance_nm}</p>}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={handleClose}
              className="flex-1 bg-navy-700 hover:bg-navy-600 text-white font-semibold py-2.5 rounded-lg transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-500 disabled:bg-navy-700 text-white font-semibold py-2.5 rounded-lg transition-colors">
              {loading ? 'Logging...' : 'Log Voyage'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
