import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || '';

export const api = axios.create({
  baseURL: `${baseURL}/api/v1`,
});

export const mediaUrl = (path) => {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${baseURL}${path}`;
};

function getTokens() {
  try {
    return JSON.parse(localStorage.getItem('retinascan_tokens') || 'null');
  } catch {
    return null;
  }
}

export function setTokens(tokens) {
  if (tokens) {
    localStorage.setItem('retinascan_tokens', JSON.stringify(tokens));
  } else {
    localStorage.removeItem('retinascan_tokens');
  }
}

api.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access_token) {
    config.headers.Authorization = `Bearer ${tokens.access_token}`;
  }
  return config;
});

let isRefreshing = false;
let queue = [];

function processQueue(error, token = null) {
  queue.forEach((p) => (error ? p.reject(error) : p.resolve(token)));
  queue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/auth/')) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(Promise.reject);
      }

      originalRequest._retry = true;
      isRefreshing = true;
      const tokens = getTokens();

      try {
        if (!tokens?.refresh_token) throw new Error('No refresh token');
        const { data } = await axios.post(`${baseURL}/api/v1/auth/refresh`, {
          refresh_token: tokens.refresh_token,
        });
        setTokens(data);
        processQueue(null, data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setTokens(null);
        localStorage.removeItem('retinascan_user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export function extractErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  return error?.response?.data?.detail || error?.message || fallback;
}
