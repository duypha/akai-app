import React, { useState } from 'react';
import { KBSolution } from '../../types';
import styles from './KBPanel.module.css';

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;

interface KBPanelProps {
  solutions: KBSolution[];
  onClose: () => void;
}

export function KBPanel({ solutions, onClose }: KBPanelProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggleSolution = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const handleFeedback = async (solutionId: string, success: boolean) => {
    try {
      const formData = new FormData();
      formData.append('success', String(success));

      await fetch(`${API_BASE}/api/knowledge/solutions/${solutionId}/feedback`, {
        method: 'POST',
        body: formData,
      });
    } catch (err) {
      console.error('Feedback error:', err);
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span>Quick Solutions</span>
        <button className={styles.btnClose} onClick={onClose}>{'\u00D7'}</button>
      </div>
      <div className={styles.panelContent}>
        {solutions.slice(0, 3).map((sol) => {
          const isExpanded = expandedId === sol.id;
          const successRate = Math.round((sol.success_rate || 0) * 100);

          return (
            <div
              key={sol.id}
              className={`${styles.solutionCard} ${isExpanded ? styles.expanded : ''}`}
              onClick={() => toggleSolution(sol.id)}
            >
              <div className={styles.solutionTitle}>{sol.title}</div>
              <div className={styles.solutionMeta}>
                {sol.problem_title || ''}
                {successRate > 0 ? ` \u2022 ${successRate}% success` : ''}
              </div>

              {isExpanded && (
                <div className={styles.solutionSteps}>
                  {sol.steps.map((step, i) => (
                    <div key={i} className={styles.solutionStep} data-step={`${i + 1}.`}>
                      {step}
                    </div>
                  ))}
                  <div className={styles.feedbackButtons}>
                    <button
                      className={`${styles.btnStep} ${styles.done}`}
                      onClick={(e) => { e.stopPropagation(); handleFeedback(sol.id, true); }}
                    >
                      Worked
                    </button>
                    <button
                      className={`${styles.btnStep} ${styles.skip}`}
                      onClick={(e) => { e.stopPropagation(); handleFeedback(sol.id, false); }}
                    >
                      Didn't work
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
