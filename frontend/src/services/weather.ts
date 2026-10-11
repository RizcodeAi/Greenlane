import { axiosInstance } from './api';

export interface StormData {
  id: string;
  name: string;
  lat: number;
  lng: number;
  scale_x: number;
  scale_y: number;
  scale_height: number;
  wind_speed: number;
}

export const getStorms = () => {
  return axiosInstance.get<StormData[]>('/weather/storms');
};
