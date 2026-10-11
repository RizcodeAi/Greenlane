import { create } from 'zustand';
import { User, Organization, AuthState } from '../types';
import { getMe, logout as apiLogout, refreshToken as apiRefreshToken } from '../services/api';

export const useAuth = create<AuthState>()((set) => ({
  user: null,
  organization: null,
  isAuthenticated: false,

  login: (user: User, organization: Organization) => {
    set({ user, organization, isAuthenticated: true });
  },

  logout: async () => {
    try { await apiLogout(); } catch {}
    set({ user: null, organization: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    try {
      const res = await getMe();
      set({ user: res.data.user, organization: res.data.organization, isAuthenticated: true });
    } catch { set({ isAuthenticated: false }); }
  },

  refreshSession: async () => {
    try {
      await apiRefreshToken();
      return 'ok';
    } catch {
      set({ user: null, organization: null, isAuthenticated: false });
      return null;
    }
  },
}));
