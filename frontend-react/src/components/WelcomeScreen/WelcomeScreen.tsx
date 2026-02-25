import React, { useState } from 'react';
import styles from './WelcomeScreen.module.css';

interface WelcomeScreenProps {
  onStartSession: () => void;
  onJoinSession: (code: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function WelcomeScreen({ onStartSession, onJoinSession, isLoading, error }: WelcomeScreenProps) {
  const [sessionCode, setSessionCode] = useState('');

  const handleJoin = () => {
    const code = sessionCode.trim();
    if (code.length === 4) {
      onJoinSession(code);
    }
  };

  const handleCodeKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleJoin();
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>Akai</h1>
        <p className={styles.subtitle}>Your mindful AI companion</p>
      </header>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Start Support Session</h2>

        <div className={styles.sessionOptions}>
          <button
            className={styles.btnPrimary}
            onClick={onStartSession}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className={styles.spinner} />
                Creating...
              </>
            ) : (
              'Start New Session'
            )}
          </button>

          <div className={styles.divider}>or</div>

          <div className={styles.codeEntry}>
            <label htmlFor="session-code" className={styles.codeLabel}>
              Enter Session Code:
            </label>
            <input
              id="session-code"
              type="text"
              className={styles.codeInput}
              placeholder="1234"
              maxLength={4}
              value={sessionCode}
              onChange={(e) => setSessionCode(e.target.value.replace(/\D/g, ''))}
              onKeyPress={handleCodeKeyPress}
              disabled={isLoading}
            />
            <button
              className={styles.btnSecondary}
              onClick={handleJoin}
              disabled={isLoading || sessionCode.length !== 4}
            >
              Join
            </button>
          </div>

          {error && (
            <p className={styles.error}>{error}</p>
          )}
        </div>
      </div>
    </div>
  );
}
