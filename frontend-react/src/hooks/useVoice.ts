import { useState, useCallback, useRef, useEffect } from 'react';

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

interface UseVoiceReturn {
  isRecording: boolean;
  isProcessing: boolean;
  error: string | null;
  startRecording: () => void;
  stopRecording: () => void;
}

export function useVoice(
  sessionId: string | null,
  onTranscript: (text: string) => void
): UseVoiceReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Keep the mic stream alive across recordings — no delay on press
  const streamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;

  // Warm up the mic on first mount so it's ready instantly
  const acquireStream = useCallback(async (): Promise<MediaStream | null> => {
    if (streamRef.current?.active) return streamRef.current;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      return stream;
    } catch (err) {
      console.error('[Voice] getUserMedia error:', err);
      if (err instanceof Error && err.name === 'NotAllowedError') {
        setError('Microphone permission denied');
      } else if (err instanceof Error && err.name === 'NotFoundError') {
        setError('No microphone found');
      } else {
        setError(err instanceof Error ? err.message : 'Could not access microphone');
      }
      return null;
    }
  }, []);

  // Pre-warm mic on mount so first press has zero delay
  useEffect(() => {
    acquireStream();
    return () => {
      // Release mic when component unmounts
      streamRef.current?.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    };
  }, [acquireStream]);

  const startRecording = useCallback(async () => {
    if (mediaRecorderRef.current?.state === 'recording') return;
    setError(null);

    const stream = await acquireStream();
    if (!stream) return;

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/webm')
      ? 'audio/webm'
      : '';

    const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      if (audioChunksRef.current.length === 0 || !sessionId) return;

      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      setIsProcessing(true);

      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('session_id', sessionId);

        const response = await fetch(`${API_BASE}/api/voice/transcribe`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error('Transcription failed');

        const data = await response.json();
        if (data.transcript) {
          onTranscriptRef.current(data.transcript);
        }
      } catch (err) {
        console.error('[Voice] Transcription error:', err);
        setError(err instanceof Error ? err.message : 'Transcription failed');
      } finally {
        setIsProcessing(false);
      }
    };

    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    setIsRecording(true);
  }, [sessionId, acquireStream]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === 'recording') {
      setIsRecording(false);
      mediaRecorderRef.current.stop();
    }
  }, []);

  return { isRecording, isProcessing, error, startRecording, stopRecording };
}
