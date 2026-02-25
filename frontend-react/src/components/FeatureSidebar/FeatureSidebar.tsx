import React from 'react';
import { KBSolution, TaskPlan, TaskTemplate } from '../../types';
import { KBPanel } from '../KBPanel/KBPanel';
import { TaskPanel } from '../TaskPanel/TaskPanel';
import { TemplatePanel } from '../TemplatePanel/TemplatePanel';
import styles from './FeatureSidebar.module.css';

interface FeatureSidebarProps {
  // KB
  showKBPanel: boolean;
  kbSolutions: KBSolution[];
  onCloseKB: () => void;

  // Task
  showTaskPanel: boolean;
  activePlan: TaskPlan | null;
  onCloseTask: () => void;
  onCompleteStep: (planId: string, stepId: string) => void;
  onSkipStep: (planId: string, stepId: string) => void;

  // Template
  showTemplatePanel: boolean;
  suggestedTemplate: TaskTemplate | null;
  onCloseTemplate: () => void;
  onStartGuidedFix: (templateId: string) => void;
}

export function FeatureSidebar({
  showKBPanel,
  kbSolutions,
  onCloseKB,
  showTaskPanel,
  activePlan,
  onCloseTask,
  onCompleteStep,
  onSkipStep,
  showTemplatePanel,
  suggestedTemplate,
  onCloseTemplate,
  onStartGuidedFix,
}: FeatureSidebarProps) {
  const hasContent = showKBPanel || showTaskPanel || showTemplatePanel;
  if (!hasContent) return null;

  return (
    <div className={styles.sidebar}>
      {showKBPanel && kbSolutions.length > 0 && (
        <KBPanel solutions={kbSolutions} onClose={onCloseKB} />
      )}

      {showTaskPanel && activePlan && (
        <TaskPanel
          plan={activePlan}
          onClose={onCloseTask}
          onCompleteStep={onCompleteStep}
          onSkipStep={onSkipStep}
        />
      )}

      {showTemplatePanel && suggestedTemplate && (
        <TemplatePanel
          template={suggestedTemplate}
          onClose={onCloseTemplate}
          onStartGuidedFix={onStartGuidedFix}
        />
      )}
    </div>
  );
}
