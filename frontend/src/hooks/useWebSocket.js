import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * WebSocket hook for SCADA real-time streaming.
 *
 * @param {string} url  WebSocket URL (e.g. "/ws/scada?stations=ST-001,ST-002")
 * @param {object} opts Options: { enabled, onMessage }
 */
export function useWebSocket(url, { enabled = true, onMessage } = {}) {
  const wsRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [lastData, setLastData] = useState(null);

  const connect = useCallback(() => {
    if (!enabled) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const fullUrl = `${protocol}://${window.location.host}${url}`;
    const ws = new WebSocket(fullUrl);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // Auto-reconnect after 3s
      setTimeout(() => connect(), 3000);
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
  }, [url, enabled, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect on unmount
        wsRef.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof msg === 'string' ? msg : JSON.stringify(msg));
    }
  }, []);

  return { connected, lastData, send };
}

export default useWebSocket;
