import React from 'react';
import { TaskTemplate } from '../../types';
import styles from './TemplatePanel.module.css';

interface TemplatePanelProps {
  template: TaskTemplate;
  onClose: () => void;
  onStartGuidedFix: (templateId: string) => void;
}

export function TemplatePanel({ template, onClose, onStartGuidedFix }: TemplatePanelProps) {
  return (
    <div className={styles.panel}>
      <div className={styles.panelHeader}>
        <span>Want a guided fix?</span>
        <button className={styles.btnClose} onClick={onClose}>{'\u00D7'}</button>
      </div>
      <div className={styles.panelContent}>
        <div className={styles.templateCard}>
          <div className={styles.templateName}>{template.name}</div>
          <div className={styles.templateDesc}>
            {template.steps.length} steps to fix this
          </div>
          <button
            className={styles.btnStartPlan}
            onClick={() => onStartGuidedFix(template.id)}
          >
            Start Guided Fix
          </button>
        </div>
      </div>
    </div>
  );
}
