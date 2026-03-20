import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket hook for SCADA real-time streaming.
 *
 * @param {string} url  WebSocket URL (e.g. "/ws/scada?stations=ST-001,ST-002")
 * @param {object} opts Options: { enabled, onMessage }
 */
export function useWebSocket(url, { enabled = true, onMessage } = {}) {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const generationRef = useRef(0);
  const [connected, setConnected] = useState(false);
  const [lastData, setLastData] = useState(null);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const connect = useCallback((generation) => {
    if (!enabled || generation !== generationRef.current) return;
    const fullUrl = buildWebSocketUrl(url);
    const ws = new WebSocket(fullUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      if (!enabled || generation !== generationRef.current) return;
      // Auto-reconnect after 3s
      clearReconnectTimer();
      reconnectTimerRef.current = setTimeout(() => connect(generation), 3000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastData(data);
        if (onMessage) onMessage(data);
      } catch {
        // ignore malformed frames
      }
    };

    wsRef.current = ws;
  }, [url, enabled, onMessage, clearReconnectTimer]);

  useEffect(() => {
    generationRef.current += 1;
    const generation = generationRef.current;
    clearReconnectTimer();
    connect(generation);
    return () => {
      generationRef.current += 1;
      clearReconnectTimer();
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on unmount
        wsRef.current.close();
      }
    };
  }, [connect, clearReconnectTimer]);

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  }, []);

  return { connected, lastData, send };
}

export function buildWebSocketUrl(
  url,
  { location = (typeof window !== 'undefined' ? window.location : null), token } = {}
) {
  if (!location) {
    throw new Error('location is required to build websocket url');
  }

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const isAbsolute = url.startsWith('ws://') || url.startsWith('wss://');
  const parsed = isAbsolute ? new URL(url) : new URL(url, `${protocol}://${location.host}`);
  const isSameOrigin = parsed.host === location.host;

  const authToken =
    token ??
    (typeof window !== 'undefined' ? window.localStorage.getItem('hydro_token') : null);
  if (authToken && isSameOrigin && !parsed.searchParams.has('token')) {
    parsed.searchParams.set('token', authToken);
  }

  return parsed.toString();
}

export default useWebSocket;
