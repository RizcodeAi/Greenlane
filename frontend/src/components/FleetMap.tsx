import React, { useEffect, useState, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { getMapVessels } from '../services/dashboard';
import { MapVessel } from '../services/dashboard';

const COMPLIANCE_COLORS: Record<string, string> = {
  Compliant: '#16A34A',
  Warning: '#EAB308',
  'Non-Compliant': '#EF4444',
};

const COMPLIANCE_BADGE: Record<string, string> = {
  Compliant: 'bg-green-600',
  Warning: 'bg-yellow-600',
  'Non-Compliant': 'bg-red-600',
};

function createShipIcon(compliance: string) {
  const color = COMPLIANCE_COLORS[compliance] || '#16A34A';
  return L.divIcon({
    html: `<div style="
      width: 18px; height: 18px;
      background: ${color};
      border: 2px solid #fff;
      border-radius: 50%;
      box-shadow: 0 0 6px ${color}88;
    "></div>`,
    className: '',
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
}

export default function FleetMap() {
  const [vessels, setVessels] = useState<MapVessel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMapVessels()
      .then((res) => setVessels(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const defaultCenter: [number, number] = [30, 0];

  if (loading) {
    return (
      <div className="w-full h-full bg-navy-950 rounded-lg flex items-center justify-center">
        <p className="text-slate-400">Loading vessel map...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-full bg-navy-950 rounded-lg flex items-center justify-center">
        <p className="text-red-400">Error loading vessels: {error}</p>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-navy-950 rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-navy-800 flex items-center justify-between">
        <h2 className="text-lg font-bold text-navy-50">Fleet Map</h2>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500"></span> Compliant</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500"></span> Warning</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500"></span> Non-Compliant</span>
        </div>
      </div>
      <div className="h-[calc(100%-48px)]">
        <MapContainer
          center={defaultCenter}
          zoom={2}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {vessels.map((vessel, idx) => (
            <Marker
              key={`${vessel.imo}-${idx}`}
              position={[vessel.lat, vessel.lng]}
              icon={createShipIcon(vessel.compliance_status)}
            >
              <Popup>
                <div className="text-sm min-w-[220px]">
                  <h3 className="font-bold text-navy-900 text-base mb-2">{vessel.name}</h3>
                  <table className="w-full text-xs space-y-1">
                    <tr><td className="text-slate-500">IMO:</td><td className="font-medium">{vessel.imo}</td></tr>
                    <tr><td className="text-slate-500">Type:</td><td>{vessel.vessel_type}</td></tr>
                    <tr><td className="text-slate-500">Speed:</td><td>{vessel.speed_knots} knots</td></tr>
                    <tr><td className="text-slate-500">Heading:</td><td>{vessel.heading_deg}°</td></tr>
                    <tr><td className="text-slate-500">Destination:</td><td>{vessel.destination}</td></tr>
                    <tr><td className="text-slate-500">Fuel:</td><td>{vessel.fuel_type}</td></tr>
                    <tr><td className="text-slate-500">ETA:</td><td>{new Date(vessel.eta).toLocaleString()}</td></tr>
                  </table>
                  <div className="mt-2 pt-2 border-t border-slate-200">
                    <span className={`inline-block px-2 py-0.5 rounded text-white text-xs font-medium ${COMPLIANCE_BADGE[vessel.compliance_status] || 'bg-gray-500'}`}>
                      {vessel.compliance_status}
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
