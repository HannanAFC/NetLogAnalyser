import { useCallback, useEffect, useRef, useState } from 'react';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? 'ws://localhost:8000';
const RECONNECT_DELAY_MS = 3000;
const MAX_BUFFER = 200; // keep at most this many events in memory

/**
 * useLiveStream
 *
 * Opens a WebSocket to /ws/live and streams incoming log entries into a
 * local buffer. The token is passed as a query param because browsers do
 * not support custom headers on WebSocket connections.
 *
 * @param {string|null} accessToken  The current JWT access token.
 * @param {{ enabled?: boolean }} options
 * @returns {{
 *   events: object[],    // newest-first buffer of incoming log entries
 *   status: 'connecting'|'open'|'closed'|'error',
 *   clear: () => void,   // empty the buffer manually
 * }}
 */
export function useLiveStream(accessToken, { enabled = true } = {}) {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('closed');
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!accessToken || !enabled) return;

    setStatus('connecting');
    const url = `${WS_BASE}/ws/live?token=${encodeURIComponent(accessToken)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setStatus('open');
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
      try {
        const entry = JSON.parse(event.data);
        setEvents((prev) => [entry, ...prev].slice(0, MAX_BUFFER));
      } catch {
        // Malformed frame — skip.
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus('error');
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus('closed');
      // Automatically reconnect after a short delay unless the component
      // has unmounted or we deliberately closed the socket.
      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current && enabled) connect();
      }, RECONNECT_DELAY_MS);
    };
  }, [accessToken, enabled]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const clear = useCallback(() => setEvents([]), []);

  return { events, status, clear };
}