import axios from 'axios';

// ---------------------------------------------------------------------------
// Base client
// All API calls go through this instance. The base URL reads from the Vite
// env variable so it works both locally (via the Vite proxy) and in production.
// ---------------------------------------------------------------------------
const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: { 'Content-Type': 'application/json' },
  // Allow the browser to send/receive the httpOnly refresh token cookie.
  withCredentials: true,
});

// ---------------------------------------------------------------------------
// Request interceptor — attach the access token to every request.
// The token is kept in module-level memory (NOT localStorage) to reduce XSS
// exposure. It survives re-renders but not full page refreshes; see the
// AuthContext for how the initial token is restored via /auth/refresh on load.
// ---------------------------------------------------------------------------
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function clearAccessToken() {
  accessToken = null;
}

client.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — silent token refresh on 401.
// If a request fails with 401 and we haven't already tried to refresh, call
// /auth/refresh (which reads the httpOnly cookie) to get a new access token,
// then replay the original request. If refresh also fails the user is logged
// out.
// ---------------------------------------------------------------------------
let isRefreshing = false;
// Queue of requests that arrived while a refresh was already in flight.
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  failedQueue = [];
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // Only attempt refresh on 401s we haven't already retried.
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Another refresh is already in flight — queue this request.
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return client(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL ?? '/api'}/auth/refresh`,
        {},
        { withCredentials: true },
      );
      const newToken = data.access_token;
      setAccessToken(newToken);
      processQueue(null, newToken);
      original.headers.Authorization = `Bearer ${newToken}`;
      return client(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearAccessToken();
      // Redirect to login — the AuthContext will also clear user state.
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default client;