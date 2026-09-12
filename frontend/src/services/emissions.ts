import axios from 'axios';
import { axiosInstance } from './api';

export interface VoyageEmissions {
  co2: number;
  ch4: number;
  n2o: number;
  sox: number;
  nox: number;
}

export interface EmissionRecord {
  id: string;
  asset_id: string;
  voyage_id: string;
  calculation_version: number;
  methodology: string;
  period: { year: number; month: number };
  fuel_type: string;
  fuel_consumed_mt: number;
  emissions: VoyageEmissions;
  co2_equivalent: number;
  calculated_at: string;
  is_current: boolean;
}

export interface Voyage {
  id: string;
  asset_id: string;
  departure_port: string;
  arrival_port: string;
  departure_date: string;
  arrival_date?: string;
  fuel_type: string;
  fuel_consumed_mt: number;
  distance_nm: number;
  cargo_mt: number;
  org_id: string;
  created_at: string;
  updated_at: string;
  emissions?: EmissionRecord;
  emissions_history?: EmissionRecord[];
}

export interface VoyageListResponse {
  voyages: Voyage[];
  total: number;
  page: number;
  page_size: number;
}

export interface VoyageDetailResponse {
  voyage: Voyage;
  emissions_history: EmissionRecord[];
}

export interface EmissionsSummary {
  total_co2: number;
  total_co2e: number;
  total_fuel_mt: number;
  avg_eefi: number | null;
  by_fuel_type: Record<string, {
    co2: number;
    co2e: number;
    fuel_mt: number;
    voyage_count: number;
  }>;
  by_pollutant: Record<string, number>;
  by_vessel: Record<string, {
    co2: number;
    co2e: number;
    fuel_mt: number;
  }>;
  period: string;
  group_by: string;
  voyage_count: number;
}

export const getVoyages = async (params?: {
  asset_id?: string;
  period?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<VoyageListResponse> => {
  const { data } = await axiosInstance.get<VoyageListResponse>('/emissions/voyages', { params });
  return data;
};

export const getVoyageById = async (id: string): Promise<VoyageDetailResponse> => {
  const { data } = await axiosInstance.get<VoyageDetailResponse>(`/emissions/voyages/${id}`);
  return data;
};

export const createVoyage = async (voyageData: any): Promise<{ voyage: Voyage; emissions: EmissionRecord }> => {
  const { data } = await axiosInstance.post('/emissions/voyages', voyageData);
  return data;
};

export const updateVoyage = async (id: string, voyageData: Partial<Voyage>): Promise<{ voyage: Voyage; emissions: EmissionRecord }> => {
  const { data } = await axiosInstance.put(`/emissions/voyages/${id}`, voyageData);
  return data;
};

export const deleteVoyage = async (id: string): Promise<{ message: string }> => {
  const { data } = await axiosInstance.delete(`/emissions/voyages/${id}`);
  return data;
};

export const getEmissionsSummary = async (params?: {
  period?: string;
  group_by?: string;
}): Promise<{ data: EmissionsSummary }> => {
  const { data } = await axiosInstance.get<EmissionsSummary>('/emissions/summary', { params });
  return { data };
};

export const getEmissionsSummaryData = async (params?: {
  period?: string;
  group_by?: string;
}): Promise<EmissionsSummary> => {
  const { data } = await axiosInstance.get<EmissionsSummary>('/emissions/summary', { params });
  return data;
};
