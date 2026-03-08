import React, { createContext, useContext, useState, useCallback, useRef, ReactNode } from 'react';
import { Message, Session, ConnectionStatus, WSMessage } from '../types';
import { useWebSocket } from '../hooks/useWebSocket';

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

interface ChatContextType {
  session: Session | null;
  messages: Message[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  isSharing: boolean;
  connectionStatus: ConnectionStatus;
  screenStream: MediaStream | null;
  createSession: () => Promise<void>;
  joinSession: (code: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  addMessage: (message: Message) => void;
  clearError: () => void;
  startScreenShare: () => Promise<boolean>;
  stopScreenShare: () => void;
  captureScreenshot: () => Promise<Blob | null>;
  sendWSMessage: (data: Record<string, unknown>) => void;
  onWSMessage: ((data: WSMessage) => void) | null;
  setOnWSMessage: (handler: ((data: WSMessage) => void) | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [screenStream, setScreenStream] = useState<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const externalWSHandlerRef = useRef<((data: WSMessage) => void) | null>(null);

  const handleWSMessage = useCallback((data: WSMessage) => {
    // Handle chat-related messages internally
    switch (data.type) {
      case 'ai_response':
        setIsLoading(false);
        const responseChunks = data.response.split(/\n\n+/).filter((chunk: string) => chunk.trim());
        responseChunks.forEach((chunk: string, index: number) => {
          setTimeout(() => {
            const assistantMessage: Message = {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: chunk.trim(),
              timestamp: new Date(),
              status: 'sent'
            };
            setMessages(prev => [...prev, assistantMessage]);
          }, index * 150);
        });
        break;

      case 'transcript': {
        const userMsg: Message = {
          id: crypto.randomUUID(),
          role: 'user',
          content: data.text,
          timestamp: new Date(),
          status: 'sent'
        };
        setMessages(prev => [...prev, userMsg]);
        break;
      }

      case 'error': {
        setIsLoading(false);
        const errorMsg: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.message || 'Something went wrong. Please try again.',
          timestamp: new Date(),
          status: 'error'
        };
        setMessages(prev => [...prev, errorMsg]);
        break;
      }

      case 'pong':
        break;

      default:
        break;
    }

    // Forward all messages to external handler (SupportContext bridge)
    if (externalWSHandlerRef.current) {
      externalWSHandlerRef.current(data);
    }
  }, []);

  const handleStatusChange = useCallback((status: ConnectionStatus) => {
    setConnectionStatus(status);
  }, []);

  const { connect: wsConnect, send: wsSend, disconnect: wsDisconnect } = useWebSocket({
    onMessage: handleWSMessage,
    onStatusChange: handleStatusChange,
  });

  const initSession = useCallback((sessionId: string, code: string) => {
    setSession({
      id: sessionId,
      code: code,
      createdAt: new Date(),
      messages: []
    });

    const welcomeMessage: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: 'Hello, I\'m Akai.\n\nHow can I help you today?',
      timestamp: new Date(),
      status: 'sent'
    };
    setMessages([welcomeMessage]);
    setIsConnected(true);

    // Connect WebSocket
    wsConnect(sessionId);
  }, [wsConnect]);

  const createSession = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE}/api/session/create`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to create session');

      const data = await response.json();
      initSession(data.session_id, data.code);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setIsLoading(false);
    }
  }, [initSession]);

  const joinSession = useCallback(async (code: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const formData = new FormData();
      formData.append('code', code);

      const response = await fetch(`${API_BASE}/api/session/join`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Invalid session code');

      const data = await response.json();
      initSession(data.session_id, code);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join session');
    } finally {
      setIsLoading(false);
    }
  }, [initSession]);

  const captureScreenshot = useCallback(async (): Promise<Blob | null> => {
    const stream = screenStreamRef.current;
    if (!stream) return null;

    const track = stream.getVideoTracks()[0];
    if (!track || track.readyState !== 'live') return null;

    // Try ImageCapture API first (Chrome/Edge)
    const win = window as any;
    if (typeof win.ImageCapture !== 'undefined') {
      try {
        const capture = new win.ImageCapture(track);
        const bitmap = await capture.grabFrame();
        const canvas = document.createElement('canvas');
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
        const ctx = canvas.getContext('2d')!;
        ctx.drawImage(bitmap, 0, 0);
        bitmap.close();
        return new Promise<Blob | null>(resolve => {
          canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.75);
        });
      } catch (e) {
        console.log('[Screen] ImageCapture failed, trying video fallback:', e);
      }
    }

    // Fallback: create temporary video element
    const video = document.createElement('video');
    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    video.style.position = 'fixed';
    video.style.top = '-9999px';
    document.body.appendChild(video);

    try {
      await video.play();
      await new Promise<void>(resolve => {
        if (video.videoWidth > 0) {
          resolve();
        } else {
          video.onloadeddata = () => resolve();
          setTimeout(resolve, 1000);
        }
      });

      if (video.videoWidth === 0) return null;

      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d')!;
      ctx.drawImage(video, 0, 0);

      return new Promise<Blob | null>(resolve => {
        canvas.toBlob(blob => resolve(blob), 'image/jpeg', 0.75);
      });
    } finally {
      video.pause();
      video.srcObject = null;
      document.body.removeChild(video);
    }
  }, []);

  const applyStream = useCallback((stream: MediaStream) => {
    screenStreamRef.current = stream;
    setScreenStream(stream);
    setIsSharing(true);

    stream.getVideoTracks()[0].onended = () => {
      screenStreamRef.current = null;
      setScreenStream(null);
      setIsSharing(false);
    };
  }, []);

  const startScreenShare = useCallback(async (): Promise<boolean> => {
    try {
      const electronAPI = (window as any).electronAPI;

      // Electron: use desktopCapturer via IPC
      if (electronAPI?.isElectron) {
        const sources = await electronAPI.getScreenSources();
        if (!sources || sources.length === 0) {
          alert('No screen sources available');
          return false;
        }
        // Use the first full screen source, or first available
        const source = sources.find((s: any) => s.name === 'Entire Screen' || s.name.includes('Screen')) || sources[0];

        const stream = await navigator.mediaDevices.getUserMedia({
          audio: false,
          video: {
            mandatory: {
              chromeMediaSource: 'desktop',
              chromeMediaSourceId: source.id,
              maxWidth: 1280,
              maxHeight: 720,
              maxFrameRate: 5,
            },
          } as any,
        });
        applyStream(stream);
        return true;
      }

      // Browser: use getDisplayMedia
      if (!navigator.mediaDevices?.getDisplayMedia) {
        alert('Screen sharing is not supported in this browser');
        return false;
      }
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: false,
      });
      applyStream(stream);
      return true;
    } catch (err: any) {
      if (err?.name !== 'NotAllowedError') {
        alert('Screen share error: ' + (err?.message || err));
      }
      return false;
    }
  }, [applyStream]);

  const stopScreenShare = useCallback(() => {
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach(t => t.stop());
      screenStreamRef.current = null;
    }
    setScreenStream(null);
    setIsSharing(false);
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!session || !content.trim()) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      status: 'sent'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const stream = screenStreamRef.current;
    if (stream && stream.active) {
      try {
        const screenshot = await captureScreenshot();
        if (screenshot && screenshot.size > 0) {
          // Convert blob to base64 and send as screen_share via WebSocket
          const reader = new FileReader();
          const base64 = await new Promise<string>((resolve, reject) => {
            reader.onload = () => {
              const result = reader.result as string;
              resolve(result.split(',')[1]); // Strip data:image/jpeg;base64, prefix
            };
            reader.onerror = reject;
            reader.readAsDataURL(screenshot);
          });
          wsSend({ type: 'screen_share', frame: base64, message: content.trim() });
          return;
        }
      } catch (e) {
        console.warn('[Screen] Capture error:', e);
      }
    }

    wsSend({ type: 'chat', message: content.trim() });
  }, [session, captureScreenshot, wsSend]);

  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const sendWSMessage = useCallback((data: Record<string, unknown>) => {
    wsSend(data);
  }, [wsSend]);

  const setOnWSMessage = useCallback((handler: ((data: WSMessage) => void) | null) => {
    externalWSHandlerRef.current = handler;
  }, []);

  return (
    <ChatContext.Provider value={{
      session,
      messages,
      isConnected,
      isLoading,
      error,
      isSharing,
      connectionStatus,
      screenStream,
      createSession,
      joinSession,
      sendMessage,
      addMessage,
      clearError,
      startScreenShare,
      stopScreenShare,
      captureScreenshot,
      sendWSMessage,
      onWSMessage: externalWSHandlerRef.current,
      setOnWSMessage,
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
