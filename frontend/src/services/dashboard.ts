import axios from 'axios';
import { axiosInstance } from './api';

export interface FleetSummary {
  total_ships: number;
  active_ships: number;
  green_count: number;
  yellow_count: number;
  red_count: number;
  total_co2_ytd: number;
  total_fuel_ytd: number;
  avg_cii_rating: string;
}

export interface MapVessel {
  name: string;
  imo: string;
  vessel_type: string;
  lat: number;
  lng: number;
  speed_knots: number;
  heading_deg: number;
  destination: string;
  eta: string;
  fuel_type: string;
  compliance_status: string;
}

export const getDashboardSummary = async (): Promise<{ data: FleetSummary }> => {
  const { data } = await axiosInstance.get<FleetSummary>('/dashboard/summary');
  return { data };
};

export const getMapVessels = async (): Promise<{ data: MapVessel[] }> => {
  const { data } = await axiosInstance.get<MapVessel[]>('/dashboard/map-vessels');
  return { data };
};
