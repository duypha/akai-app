import { useRef, useCallback, useEffect } from 'react';
import { WSMessage, ConnectionStatus } from '../types';

const MAX_RETRIES = 5;
const BASE_DELAY_MS = 1000;

interface UseWebSocketOptions {
  onMessage: (data: WSMessage) => void;
  onStatusChange: (status: ConnectionStatus) => void;
}

export function useWebSocket({ onMessage, onStatusChange }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const shouldReconnectRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);

  const cleanup = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback((sessionId: string) => {
    cleanup();
    sessionIdRef.current = sessionId;
    shouldReconnectRef.current = true;
    retryCountRef.current = 0;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // includes port if non-standard
    const wsUrl = `${protocol}//${host}/ws/${sessionId}`;

    onStatusChange('connecting');

    const doConnect = (url: string) => {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        retryCountRef.current = 0;
        onStatusChange('connected');
      };

      ws.onclose = () => {
        onStatusChange('disconnected');
        wsRef.current = null;

        if (shouldReconnectRef.current && sessionIdRef.current) {
          const attempt = retryCountRef.current;
          if (attempt >= MAX_RETRIES) {
            console.warn('[WS] Max reconnect attempts reached, giving up.');
            shouldReconnectRef.current = false;
            return;
          }

          const delay = BASE_DELAY_MS * Math.pow(2, attempt);
          retryCountRef.current = attempt + 1;
          console.log(`[WS] Reconnecting in ${delay}ms (attempt ${attempt + 1}/${MAX_RETRIES})...`);

          reconnectTimerRef.current = setTimeout(() => {
            if (shouldReconnectRef.current && sessionIdRef.current) {
              doConnect(`${protocol}//${sessionIdRef.current ? host : ''}/ws/${sessionIdRef.current}`);
            }
          }, delay);
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessage;
          onMessage(data);
        } catch (e) {
          console.error('[WS] Failed to parse message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('[WS] Error:', error);
      };
    };

    doConnect(wsUrl);
  }, [cleanup, onMessage, onStatusChange]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    cleanup();
    sessionIdRef.current = null;
    retryCountRef.current = 0;
    onStatusChange('disconnected');
  }, [cleanup, onStatusChange]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return { connect, send, disconnect };
}
