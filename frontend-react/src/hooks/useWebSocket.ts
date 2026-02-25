import { useRef, useCallback, useEffect } from 'react';
import { WSMessage, ConnectionStatus } from '../types';

const RECONNECT_DELAY = 3000;

interface UseWebSocketOptions {
  onMessage: (data: WSMessage) => void;
  onStatusChange: (status: ConnectionStatus) => void;
}

export function useWebSocket({ onMessage, onStatusChange }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const shouldReconnectRef = useRef(false);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

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

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const wsUrl = `${protocol}//${host}:8000/ws/${sessionId}`;

    onStatusChange('connecting');

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      onStatusChange('connected');
    };

    ws.onclose = () => {
      onStatusChange('disconnected');
      wsRef.current = null;

      if (shouldReconnectRef.current && sessionIdRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          if (shouldReconnectRef.current && sessionIdRef.current) {
            connect(sessionIdRef.current);
          }
        }, RECONNECT_DELAY);
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
  }, [cleanup, onMessage, onStatusChange]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    cleanup();
    sessionIdRef.current = null;
    onStatusChange('disconnected');
  }, [cleanup, onStatusChange]);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return { connect, send, disconnect };
}
