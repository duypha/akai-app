import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { KBSolution, TaskPlan, TaskTemplate } from '../types';

interface SupportContextType {
  // KB Solutions
  kbSolutions: KBSolution[];
  showKBPanel: boolean;

  // Task Plan
  activePlan: TaskPlan | null;
  showTaskPanel: boolean;

  // Template
  suggestedTemplate: TaskTemplate | null;
  showTemplatePanel: boolean;

  // Sidebar visibility (any panel showing)
  isSidebarVisible: boolean;

  // Actions
  setKBSolutions: (solutions: KBSolution[]) => void;
  setActivePlan: (plan: TaskPlan | null) => void;
  setSuggestedTemplate: (template: TaskTemplate | null) => void;
  closeKBPanel: () => void;
  closeTaskPanel: () => void;
  closeTemplatePanel: () => void;
}

const SupportContext = createContext<SupportContextType | undefined>(undefined);

export function SupportProvider({ children }: { children: ReactNode }) {
  const [kbSolutions, setKBSolutionsState] = useState<KBSolution[]>([]);
  const [showKBPanel, setShowKBPanel] = useState(false);
  const [activePlan, setActivePlanState] = useState<TaskPlan | null>(null);
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [suggestedTemplate, setSuggestedTemplateState] = useState<TaskTemplate | null>(null);
  const [showTemplatePanel, setShowTemplatePanel] = useState(false);

  const setKBSolutions = useCallback((solutions: KBSolution[]) => {
    setKBSolutionsState(solutions);
    if (solutions.length > 0) {
      setShowKBPanel(true);
    }
  }, []);

  const setActivePlan = useCallback((plan: TaskPlan | null) => {
    setActivePlanState(plan);
    if (plan) {
      setShowTaskPanel(true);
      setShowTemplatePanel(false);
      setShowKBPanel(false);
    }
  }, []);

  const setSuggestedTemplate = useCallback((template: TaskTemplate | null) => {
    setSuggestedTemplateState(template);
    if (template) {
      setShowTemplatePanel(true);
    }
  }, []);

  const closeKBPanel = useCallback(() => {
    setShowKBPanel(false);
  }, []);

  const closeTaskPanel = useCallback(() => {
    setShowTaskPanel(false);
  }, []);

  const closeTemplatePanel = useCallback(() => {
    setShowTemplatePanel(false);
  }, []);

  const isSidebarVisible = showKBPanel || showTaskPanel || showTemplatePanel;

  return (
    <SupportContext.Provider value={{
      kbSolutions,
      showKBPanel,
      activePlan,
      showTaskPanel,
      suggestedTemplate,
      showTemplatePanel,
      isSidebarVisible,
      setKBSolutions,
      setActivePlan,
      setSuggestedTemplate,
      closeKBPanel,
      closeTaskPanel,
      closeTemplatePanel,
    }}>
      {children}
    </SupportContext.Provider>
  );
}

export function useSupport() {
  const context = useContext(SupportContext);
  if (!context) {
    throw new Error('useSupport must be used within a SupportProvider');
  }
  return context;
}
