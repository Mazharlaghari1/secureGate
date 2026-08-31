import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
});

let authToken = '';
let onUnauthorizedCallback = () => {};

export const setAuthToken = (token) => {
  authToken = token;
};

export const registerUnauthorizedHandler = (callback) => {
  onUnauthorizedCallback = callback;
};

api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || '';
    const isAuthEndpoint = url.includes('/api/auth/login') || url.includes('/api/auth/register');

    if (error.response && error.response.status === 401 && !isAuthEndpoint) {
      onUnauthorizedCallback();
    }
    return Promise.reject(error);
  }
);

export default api;
