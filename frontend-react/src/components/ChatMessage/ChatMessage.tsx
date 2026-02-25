import React from 'react';
import { Message } from '../../types';
import styles from './ChatMessage.module.css';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`${styles.message} ${isUser ? styles.user : styles.assistant}`}
      role="article"
      aria-label={`${isUser ? 'You' : 'Akai'} said`}
    >
      <div className={styles.messageContent}>
        {message.content}
      </div>
    </div>
  );
}
