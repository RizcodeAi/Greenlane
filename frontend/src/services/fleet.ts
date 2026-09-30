import { axiosInstance } from './api';

export interface Ship {
  id: string;
  imo_number: string;
  name: string;
  flag_state: string;
  vessel_type: string;
  gross_tonnage: number;
  dwt: number;
  fuel_type: string;
  status: string;
  org_id: string;
  created_at: string;
  updated_at?: string;
}

export interface ShipListResponse {
  ships: Ship[];
  total: number;
  page: number;
  page_size: number;
}

export const getShips = async (params?: {
  search?: string;
  vessel_type?: string;
  fuel_type?: string;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ShipListResponse> => {
  const { data } = await axiosInstance.get<ShipListResponse>('/fleet/ships', { params });
  return data;
};

export const getShipById = async (id: string): Promise<{ ship: Ship }> => {
  const { data } = await axiosInstance.get<{ ship: Ship }>(`/fleet/ships/${id}`);
  return data;
};

export const createShip = async (shipData: Omit<Ship, 'id' | 'org_id' | 'created_at' | 'updated_at'>): Promise<{ ship: Ship }> => {
  const { data } = await axiosInstance.post<{ ship: Ship }>('/fleet/ships', shipData);
  return data;
};

export const updateShip = async (id: string, shipData: Partial<Ship>): Promise<{ ship: Ship }> => {
  const { data } = await axiosInstance.put<{ ship: Ship }>(`/fleet/ships/${id}`, shipData);
  return data;
};

export const deleteShip = async (id: string): Promise<{ message: string }> => {
  const { data } = await axiosInstance.delete<{ message: string }>(`/fleet/ships/${id}`);
  return data;
};
