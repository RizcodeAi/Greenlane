import { axiosInstance } from './api';

export interface LiveVessel {
  imo: string;
  name: string;
  lat: number;
  lng: number;
  heading: number;
  speed: number;
  compliance_status: string;
}

export const getLiveFleet = () => {
  return axiosInstance.get<LiveVessel[]>('/tracking/live');
};
