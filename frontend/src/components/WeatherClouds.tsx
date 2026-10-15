import { useEffect, useState } from 'react';
import { CloudCollection, CumulusCloud } from 'resium';
import { Cartesian3 } from 'cesium';
import { getStorms, StormData } from '../services/weather';

export default function WeatherClouds() {
  const [storms, setStorms] = useState<StormData[]>([]);

  useEffect(() => {
    getStorms()
      .then((res: any) => setStorms(res.data))
      .catch((err: any) => console.error("Failed to load storms:", err));
  }, []);

  return (
    <CloudCollection>
      {storms.map((storm) => {
        // Position the cloud above the ground
        const position = Cartesian3.fromDegrees(storm.lng, storm.lat, storm.scale_height / 2);

        return (
          <CumulusCloud
            key={storm.id}
            position={position}
            scale={new Cartesian3(storm.scale_x, storm.scale_y, storm.scale_height)}
            maximumSize={new Cartesian3(storm.scale_x * 0.8, storm.scale_y * 0.8, storm.scale_height * 0.8)}
            slice={0.3}
          />
        );
      })}
    </CloudCollection>
  );
}
