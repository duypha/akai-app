import React, { useRef, useEffect } from 'react';
import styles from './ScreenPreview.module.css';

interface ScreenPreviewProps {
  stream: MediaStream | null;
  isSharing: boolean;
}

export function ScreenPreview({ stream, isSharing }: ScreenPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  if (!isSharing || !stream) return null;

  return (
    <div className={styles.screenPreview}>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className={styles.video}
      />
    </div>
  );
}
