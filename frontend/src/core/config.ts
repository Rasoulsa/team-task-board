const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8010';

export const config = {
  apiBaseUrl,
  apiUrl: import.meta.env.VITE_API_URL ?? `${apiBaseUrl}/api/v1`,
  wsUrl: import.meta.env.VITE_WS_URL ?? 'ws://localhost:8010/api/v1/ws',
};
