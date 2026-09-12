import React, { useState } from 'react';
import { Ship } from '../services/fleet';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Omit<Ship, 'id' | 'org_id' | 'created_at' | 'updated_at'>) => Promise<void>;
  loading: boolean;
}

const VALID_VESSEL_TYPES = ['Bulk Carrier', 'Tanker', 'Container', 'Ro-Ro', 'General Cargo', 'Gas Carrier'];
const VALID_FUEL_TYPES = ['HFO', 'MGO', 'LNG', 'Methanol'];
const VALID_STATUSES = ['active', 'inactive'];

export default function AddShipModal({ isOpen, onClose, onSubmit, loading }: Props) {
  const [name, setName] = useState('');
  const [imoNumber, setImoNumber] = useState('');
  const [flagState, setFlagState] = useState('');
  const [vesselType, setVesselType] = useState('');
  const [grossTonnage, setGrossTonnage] = useState('');
  const [dwt, setDwt] = useState('');
  const [fuelType, setFuelType] = useState('');
  const [status, setStatus] = useState('active');
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) newErrors.name = 'Name is required';
    if (!imoNumber.trim()) newErrors.imo_number = 'IMO number is required';
    if (!flagState.trim()) newErrors.flag_state = 'Flag state is required';
    if (!vesselType) newErrors.vessel_type = 'Vessel type is required';
    if (!grossTonnage || isNaN(Number(grossTonnage)) || Number(grossTonnage) <= 0)
      newErrors.gross_tonnage = 'Valid gross tonnage is required';
    if (!dwt || isNaN(Number(dwt)) || Number(dwt) <= 0)
      newErrors.dwt = 'Valid DWT is required';
    if (!fuelType) newErrors.fuel_type = 'Fuel type is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      name: name.trim(),
      imo_number: imoNumber.trim(),
      flag_state: flagState.trim(),
      vessel_type: vesselType,
      gross_tonnage: Number(grossTonnage),
      dwt: Number(dwt),
      fuel_type: fuelType,
      status,
    });
  };

  const handleClose = () => {
    setName(''); setImoNumber(''); setFlagState(''); setVesselType('');
    setGrossTonnage(''); setDwt(''); setFuelType(''); setStatus('active');
    setErrors({});
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-navy-900 border border-navy-700 rounded-xl p-6 w-full max-w-lg shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-navy-50">Add New Vessel</h2>
          <button onClick={handleClose} className="text-slate-400 hover:text-white text-xl">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Ship Name *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)}
              className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.name ? 'border-red-500' : 'border-navy-600'}`}
              placeholder="e.g. MV Ocean Star" required />
            {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">IMO Number *</label>
            <input type="text" value={imoNumber} onChange={(e) => setImoNumber(e.target.value)}
              className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.imo_number ? 'border-red-500' : 'border-navy-600'}`}
              placeholder="e.g. 9876543" required />
            {errors.imo_number && <p className="text-red-400 text-xs mt-1">{errors.imo_number}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Flag State *</label>
              <input type="text" value={flagState} onChange={(e) => setFlagState(e.target.value)}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.flag_state ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. Panama" required />
              {errors.flag_state && <p className="text-red-400 text-xs mt-1">{errors.flag_state}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Vessel Type *</label>
              <select value={vesselType} onChange={(e) => setVesselType(e.target.value)}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.vessel_type ? 'border-red-500' : 'border-navy-600'}`}
                required>
                <option value="">Select type</option>
                {VALID_VESSEL_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              {errors.vessel_type && <p className="text-red-400 text-xs mt-1">{errors.vessel_type}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Gross Tonnage *</label>
              <input type="number" value={grossTonnage} onChange={(e) => setGrossTonnage(e.target.value)}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.gross_tonnage ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. 45000" required />
              {errors.gross_tonnage && <p className="text-red-400 text-xs mt-1">{errors.gross_tonnage}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">DWT (Deadweight Tonnage) *</label>
              <input type="number" value={dwt} onChange={(e) => setDwt(e.target.value)}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.dwt ? 'border-red-500' : 'border-navy-600'}`}
                placeholder="e.g. 55000" required />
              {errors.dwt && <p className="text-red-400 text-xs mt-1">{errors.dwt}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Fuel Type *</label>
              <select value={fuelType} onChange={(e) => setFuelType(e.target.value)}
                className={`w-full bg-navy-800 border rounded px-3 py-2 text-white focus:outline-none focus:border-green-500 ${errors.fuel_type ? 'border-red-500' : 'border-navy-600'}`}
                required>
                <option value="">Select fuel</option>
                {VALID_FUEL_TYPES.map((f) => <option key={f} value={f}>{f}</option>)}
              </select>
              {errors.fuel_type && <p className="text-red-400 text-xs mt-1">{errors.fuel_type}</p>}
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Status</label>
              <select value={status} onChange={(e) => setStatus(e.target.value)}
                className="w-full bg-navy-800 border border-navy-600 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500">
                {VALID_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={handleClose}
              className="flex-1 bg-navy-700 hover:bg-navy-600 text-white font-semibold py-2.5 rounded-lg transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={loading}
              className="flex-1 bg-green-600 hover:bg-green-500 disabled:bg-navy-700 text-white font-semibold py-2.5 rounded-lg transition-colors">
              {loading ? 'Adding...' : 'Add Vessel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
