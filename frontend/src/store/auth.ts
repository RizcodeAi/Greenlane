import { create } from 'zustand';
import { User, Organization, AuthState } from '../types';
import { getMe, logout as apiLogout } from '../services/api';

export const useAuth = create<AuthState>()((set, get) => ({
  user: null,
  organization: null,
  isAuthenticated: false,
  accessToken: null,

  login: (accessToken: string, user: User, organization: Organization) => {
    set({ user, organization, isAuthenticated: true, accessToken });
  },

  logout: async () => {
    try { await apiLogout(); } catch {}
    set({ user: null, organization: null, isAuthenticated: false, accessToken: null });
  },

  fetchUser: async () => {
    try {
      const res = await getMe();
      set({ user: res.data.user, organization: res.data.organization, isAuthenticated: true });
    } catch { set({ isAuthenticated: false }); }
  },
}));
