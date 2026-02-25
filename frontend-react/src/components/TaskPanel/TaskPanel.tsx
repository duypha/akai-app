import React from 'react';
import { TaskPlan } from '../../types';
import styles from './TaskPanel.module.css';

interface TaskPanelProps {
  plan: TaskPlan;
  onClose: () => void;
  onCompleteStep: (planId: string, stepId: string) => void;
  onSkipStep: (planId: string, stepId: string) => void;
}

export function TaskPanel({ plan, onClose, onCompleteStep, onSkipStep }: TaskPanelProps) {
  const progress = plan.progress || { completed: 0, total: 0, percent: 0 };

  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span>Guided Fix</span>
        <button className={styles.btnClose} onClick={onClose}>{'\u00D7'}</button>
      </div>
      <div className={styles.panelContent}>
        <div className={styles.taskHeader}>
          <div className={styles.taskTitle}>{plan.title}</div>
          <div className={styles.taskProgress}>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${progress.percent}%` }}
              />
            </div>
            <span className={styles.progressText}>
              {progress.completed}/{progress.total}
            </span>
          </div>
        </div>

        <div className={styles.taskSteps}>
          {plan.steps.map((step) => {
            let stepClass = styles.pending;
            if (step.status === 'completed') stepClass = styles.completed;
            else if (step.status === 'in_progress') stepClass = styles.current;

            return (
              <React.Fragment key={step.id}>
                <div className={`${styles.taskStep} ${stepClass}`}>
                  <span className={styles.stepIcon} />
                  <span>{step.title}</span>
                </div>

                {step.status === 'in_progress' && (
                  <div className={styles.stepActions}>
                    <button
                      className={`${styles.btnStep} ${styles.done}`}
                      onClick={() => onCompleteStep(plan.id, step.id)}
                    >
                      Done
                    </button>
                    <button
                      className={`${styles.btnStep} ${styles.skip}`}
                      onClick={() => onSkipStep(plan.id, step.id)}
                    >
                      Skip
                    </button>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
