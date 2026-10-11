import { useEffect, useState } from 'react';
import { getLiveFleet, LiveVessel } from '../services/tracking';
import { Viewer, Entity, PointGraphics, CameraFlyTo } from 'resium';
import { Cartesian3, Color } from 'cesium';
import WeatherClouds from './WeatherClouds';

const COMPLIANCE_COLORS: Record<string, Color> = {
  Compliant: Color.LIMEGREEN,
  Warning: Color.GOLD,
  'Non-Compliant': Color.CRIMSON,
};

export default function FleetMap() {
  const [vessels, setVessels] = useState<LiveVessel[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flyToCenter, setFlyToCenter] = useState(false);


  useEffect(() => {
    getLiveFleet()
      .then((res) => setVessels(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const handleCenter = () => {
      setFlyToCenter(true);
      setTimeout(() => setFlyToCenter(false), 100);
    };
    window.addEventListener('center-fleet', handleCenter);
    return () => window.removeEventListener('center-fleet', handleCenter);
  }, []);


  if (loading) {
    return (
      <div className="w-full h-full bg-navy-950 rounded-lg flex items-center justify-center">
        <p className="text-slate-400">Loading 3D Globe...</p>
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
    <div className="w-full h-full bg-navy-950 rounded-lg overflow-hidden relative">
      <div className="absolute top-0 left-0 w-full z-10 px-4 py-3 bg-navy-950/80 backdrop-blur-sm border-b border-navy-800 flex items-center justify-between">
        <h2 className="text-lg font-bold text-navy-50">3D Global Tracker</h2>
        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-green-500"></span> Compliant</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-yellow-500"></span> Warning</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-red-500"></span> Non-Compliant</span>
        </div>
      </div>
      <div className="w-full h-full pt-[48px]">
        <Viewer
            full
            timeline={false}
            animation={false}
            baseLayerPicker={false}
            geocoder={false}
            homeButton={false}
            sceneModePicker={false}
            navigationHelpButton={false}
            infoBox={true}
            style={{ width: '100%', height: '100%' }}
        >
          {vessels.map((vessel, idx) => {
            const position = Cartesian3.fromDegrees(vessel.lng, vessel.lat, 100);
            const color = COMPLIANCE_COLORS[vessel.compliance_status] || Color.WHITE;

            const descriptionHtml = `
              <div style="font-family: sans-serif; color: white;">
                  <p><strong>IMO:</strong> ${vessel.imo}</p>
                  <p><strong>Speed:</strong> ${vessel.speed.toFixed(1)} knots</p>
                  <p><strong>Heading:</strong> ${vessel.heading.toFixed(1)}&deg;</p>
                  <p><strong>Status:</strong> ${vessel.compliance_status}</p>
              </div>
            `;

            return (
              <Entity
                  key={`${vessel.imo}-${idx}`}
                  name={vessel.name}
                  position={position}
                  description={descriptionHtml}
              >
                <PointGraphics
                    pixelSize={12}
                    color={color}
                    outlineColor={Color.WHITE}
                    outlineWidth={2}
                />
              </Entity>
            );
          })}
          <WeatherClouds />
          {flyToCenter && vessels.length > 0 && <CameraFlyTo destination={Cartesian3.fromDegrees(vessels[0].lng, vessels[0].lat, 5000000)} duration={2.0} />}
        </Viewer>
      </div>
    </div>
  );
}
