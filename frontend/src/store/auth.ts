import { create } from 'zustand';
import { User, Organization, AuthState } from '../types';
import { getMe, logout as apiLogout, refreshToken as apiRefreshToken } from '../services/api';

export const useAuth = create<AuthState>()((set) => ({
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
      const storedToken = localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
      set({ user: res.data.user, organization: res.data.organization, isAuthenticated: true, accessToken: storedToken });
    } catch { set({ isAuthenticated: false }); }
  },

  setAccessToken: (token: string | null) => {
    set({ accessToken: token });
  },

  refreshSession: async () => {
    try {
      const newToken = await apiRefreshToken();
      return newToken;
    } catch {
      set({ user: null, organization: null, isAuthenticated: false, accessToken: null });
      return null;
    }
  },
}));
