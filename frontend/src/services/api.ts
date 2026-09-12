import axios from 'axios';
import { useAuth } from '../store/auth';

const API_URL = (import.meta as ImportMeta & { env: Record<string, string> }).env.VITE_API_URL || 'http://localhost:8000';

export const axiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true,
});

axiosInstance.interceptors.request.use((config) => {
  const token = useAuth.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        await refreshToken();
        const newToken = useAuth.getState().accessToken;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axiosInstance(originalRequest);
      } catch {
        useAuth.getState().logout();
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export const login = (credentials: { email: string; password: string }) =>
  axiosInstance.post('/auth/login', credentials);

export const register = (data: { email: string; password: string; full_name: string; org_name: string; industry: string; invite_emails?: string[] }) =>
  axiosInstance.post('/auth/register', data);

export const logout = () => axiosInstance.post('/auth/logout');

export const refreshToken = () => axiosInstance.post('/auth/refresh');

export const getMe = () => axiosInstance.get('/auth/me');

export const invite = (emails: string[], role: string) =>
  axiosInstance.post('/auth/invite', { emails, role });
