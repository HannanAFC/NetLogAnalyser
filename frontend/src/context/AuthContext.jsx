import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authApi } from '../api/auth.js';
import { setAccessToken, clearAccessToken } from '../api/client.js';

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const AuthContext = createContext(null);

// ---------------------------------------------------------------------------
// Provider
// Wrap the app in this once at the top level. It:
//   1. On mount, attempts a silent refresh to restore the session if the user
//      has a valid refresh token cookie from a previous visit.
//   2. Exposes login / logout helpers that keep the in-memory access token
//      and the user object in sync.
//   3. Schedules a proactive token refresh 1 minute before the access token
//      expires so the user never sees an unexpected 401 mid-session.
// ---------------------------------------------------------------------------
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // true while we're checking for an existing session on first load
  const [isLoading, setIsLoading] = useState(true);
  // holds the setTimeout id for the proactive refresh
  const [refreshTimer, setRefreshTimer] = useState(null);

  // -------------------------------------------------------------------------
  // scheduleRefresh — given a JWT, decode the expiry and queue a refresh
  // 60 seconds before it expires.
  // -------------------------------------------------------------------------
  const scheduleRefresh = useCallback((token) => {
    if (refreshTimer) clearTimeout(refreshTimer);

    try {
      // Decode the payload without verifying (verification happens server-side).
      const payload = JSON.parse(atob(token.split('.')[1]));
      const expiresInMs = payload.exp * 1000 - Date.now() - 60_000;

      if (expiresInMs <= 0) return; // already expiring, don't bother

      const id = setTimeout(async () => {
        try {
          const { access_token } = await authApi.refresh();
          setAccessToken(access_token);
          scheduleRefresh(access_token);
        } catch {
          // Refresh failed — session is over, clear state.
          handleLogout();
        }
      }, expiresInMs);

      setRefreshTimer(id);
    } catch {
      // Malformed token — ignore and let the next 401 handle it.
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // Restore session on mount.
  // If the browser has a valid refresh cookie the backend will issue a new
  // access token. If not (first visit / expired) this fails silently and the
  // user is treated as logged out.
  // -------------------------------------------------------------------------
  useEffect(() => {
    (async () => {
      try {
        const { access_token, user: me } = await authApi.refresh();
        setAccessToken(access_token);
        setUser(me);
        scheduleRefresh(access_token);
      } catch {
        // No valid session — that's fine, stay logged out.
      } finally {
        setIsLoading(false);
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // login
  // -------------------------------------------------------------------------
  const login = useCallback(async (email, password) => {
    const { access_token, user: me } = await authApi.login({ email, password });
    setAccessToken(access_token);
    setUser(me);
    scheduleRefresh(access_token);
    return me;
  }, [scheduleRefresh]);

  // -------------------------------------------------------------------------
  // logout
  // -------------------------------------------------------------------------
  const handleLogout = useCallback(async () => {
    if (refreshTimer) clearTimeout(refreshTimer);
    try {
      await authApi.logout();
    } catch {
      // Best effort — clear client state regardless.
    }
    clearAccessToken();
    setUser(null);
  }, [refreshTimer]);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout: handleLogout }}>
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}