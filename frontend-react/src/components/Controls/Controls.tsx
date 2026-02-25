import React, { useState, useCallback } from 'react';
import { useVoice } from '../../hooks/useVoice';
import styles from './Controls.module.css';

interface ControlsProps {
  isSharing: boolean;
  onShareScreen: () => void;
  onStopSharing: () => void;
  onCapture: () => void;
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  sessionId: string | null;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}

export function Controls({
  isSharing,
  onShareScreen,
  onStopSharing,
  onCapture,
  onSendMessage,
  isLoading,
  sessionId,
  voiceEnabled,
  onToggleVoice,
}: ControlsProps) {
  const [message, setMessage] = useState('');
  const { isRecording, isProcessing, error: voiceError, startRecording, stopRecording } = useVoice(
    sessionId,
    (transcript) => onSendMessage(transcript)
  );

  const handleSend = useCallback(() => {
    const text = message.trim();
    if (text && !isLoading) {
      onSendMessage(text);
      setMessage('');
    }
  }, [message, isLoading, onSendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoiceClick = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      void startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const voiceText = isRecording ? 'Click to Stop' : isProcessing ? 'Processing...' : 'Click to Speak';
  const voiceStatus = voiceError ? voiceError : isRecording ? 'Listening...' : isProcessing ? 'Processing...' : '';

  return (
    <div className={styles.controls}>
      {/* Screen Share Controls */}
      <div className={styles.controlGroup}>
        {!isSharing ? (
          <button className={styles.btnScreen} onClick={onShareScreen}>
            Share Screen
          </button>
        ) : (
          <>
            <button className={styles.btnDanger} onClick={onStopSharing}>
              Stop Sharing
            </button>
            <button className={styles.btnSecondary} onClick={onCapture}>
              Capture
            </button>
          </>
        )}
      </div>

      {/* Voice Controls */}
      <div className={styles.controlGroup}>
        <button
          className={`${styles.btnVoice} ${isRecording ? styles.recording : ''}`}
          onClick={handleVoiceClick}
          disabled={isProcessing}
        >
          {voiceText}
        </button>
        <button
          className={`${styles.btnVoiceToggle} ${voiceEnabled ? styles.voiceOn : ''}`}
          onClick={onToggleVoice}
          title={voiceEnabled ? 'Voice responses on' : 'Voice responses off'}
        >
          {voiceEnabled ? '🔊 Voice On' : '🔇 Voice Off'}
        </button>
        {voiceStatus && (
          <span className={styles.statusText}>{voiceStatus}</span>
        )}
      </div>

      {/* Text Input */}
      <div className={styles.inputGroup}>
        <input
          type="text"
          className={styles.messageInput}
          placeholder="Type your message here..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <button
          className={styles.btnPrimary}
          onClick={handleSend}
          disabled={isLoading || !message.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}
