import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { config } from '../config';
import type { AuthResponse } from '../../features/auth/domain/types';
import { useAuthStore } from '../../features/auth/store/authStore';

export const apiClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

const refreshClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((requestConfig: InternalAxiosRequestConfig) => {
  const accessToken = useAuthStore.getState().accessToken;

  if (accessToken) {
    requestConfig.headers.Authorization = `Bearer ${accessToken}`;
  }

  return requestConfig;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    const refreshToken = useAuthStore.getState().refreshToken;

    if (!refreshToken) {
      useAuthStore.getState().clearSession();
      return Promise.reject(error);
    }

    try {
      const response = await refreshClient.post<AuthResponse>('/auth/refresh', {
        refresh_token: refreshToken,
      });

      const data = response.data;

      useAuthStore.getState().setSession({
        user: data.user,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });

      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;

      return apiClient(originalRequest);
    } catch (refreshError) {
      useAuthStore.getState().clearSession();
      return Promise.reject(refreshError);
    }
  },
);