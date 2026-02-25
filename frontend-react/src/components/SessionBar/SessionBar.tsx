import React from 'react';
import { ConnectionStatus } from '../../types';
import styles from './SessionBar.module.css';

interface SessionBarProps {
  sessionCode: string;
  connectionStatus: ConnectionStatus;
}

export function SessionBar({ sessionCode, connectionStatus }: SessionBarProps) {
  const isConnected = connectionStatus === 'connected';
  const statusText = isConnected ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected';

  return (
    <div className={styles.sessionBar}>
      <span className={styles.sessionId}>
        Session: <strong>{sessionCode}</strong>
      </span>
      <span className={isConnected ? styles.statusConnected : styles.statusDisconnected}>
        {'\u25CF'} {statusText}
      </span>
    </div>
  );
}
