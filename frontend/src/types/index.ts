export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  org_id: string;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  industry: string;
  created_at: string;
}

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

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  organization: Organization | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  login: (accessToken: string, user: User, organization: Organization) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
}
