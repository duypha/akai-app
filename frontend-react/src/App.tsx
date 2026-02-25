import React, { useCallback, useEffect, useRef, useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { ChatProvider, useChat } from './contexts/ChatContext';
import { SupportProvider, useSupport } from './contexts/SupportContext';
import {
  ChatArea,
  WelcomeScreen,
  SessionBar,
  Controls,
  ScreenPreview,
  FeatureSidebar,
} from './components';
import { WSMessage } from './types';
import { useSpeech } from './hooks/useSpeech';
import './styles/global.css';

function ChatApp() {
  const {
    session,
    messages,
    isConnected,
    isLoading,
    isSharing,
    connectionStatus,
    error,
    screenStream,
    createSession,
    joinSession,
    sendMessage,
    startScreenShare,
    stopScreenShare,
    captureScreenshot,
    sendWSMessage,
    setOnWSMessage,
  } = useChat();

  const {
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
  } = useSupport();

  // Bridge WS messages from ChatContext to SupportContext
  useEffect(() => {
    const handler = (data: WSMessage) => {
      switch (data.type) {
        case 'kb_match':
          setKBSolutions(data.top_solutions);
          break;
        case 'template_detected':
          setSuggestedTemplate(data.template);
          break;
        case 'task_created':
        case 'task_started':
          setActivePlan(data.plan);
          // Auto-start if created
          if (data.plan.status === 'created') {
            sendWSMessage({
              type: 'task_action',
              action: 'start_plan',
              plan_id: data.plan.id,
            });
          }
          break;
        case 'step_completed':
          setActivePlan(data.plan);
          if (data.is_complete) {
            setTimeout(() => closeTaskPanel(), 2000);
          }
          break;
        case 'step_failed':
          setActivePlan(data.plan);
          break;
      }
    };

    setOnWSMessage(handler);
    return () => setOnWSMessage(null);
  }, [setOnWSMessage, setKBSolutions, setActivePlan, setSuggestedTemplate, closeTaskPanel, sendWSMessage]);

  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const { speak, stop } = useSpeech();
  const lastSpokenIdRef = useRef<string | null>(null);

  // Auto-speak new assistant messages when voice is enabled
  useEffect(() => {
    if (!voiceEnabled || messages.length === 0) return;
    const last = messages[messages.length - 1];
    if (last.role === 'assistant' && last.id !== lastSpokenIdRef.current) {
      lastSpokenIdRef.current = last.id;
      speak(last.content);
    }
  }, [messages, voiceEnabled, speak]);

  // Stop speaking when voice is turned off
  useEffect(() => {
    if (!voiceEnabled) stop();
  }, [voiceEnabled, stop]);

  const handleShareScreen = useCallback(async () => {
    await startScreenShare();
  }, [startScreenShare]);

  const handleCapture = useCallback(async () => {
    const screenshot = await captureScreenshot();
    if (screenshot) {
      sendMessage('[Shared screenshot]');
    }
  }, [captureScreenshot, sendMessage]);

  const handleCompleteStep = useCallback((planId: string, stepId: string) => {
    sendWSMessage({
      type: 'task_action',
      action: 'complete_step',
      plan_id: planId,
      step_id: stepId,
    });
  }, [sendWSMessage]);

  const handleSkipStep = useCallback((planId: string, stepId: string) => {
    sendWSMessage({
      type: 'task_action',
      action: 'skip_step',
      plan_id: planId,
      step_id: stepId,
    });
  }, [sendWSMessage]);

  const handleStartGuidedFix = useCallback((templateId: string) => {
    closeTemplatePanel();
    sendWSMessage({
      type: 'task_action',
      action: 'create_from_template',
      template_id: templateId,
    });
  }, [closeTemplatePanel, sendWSMessage]);

  if (!isConnected) {
    return (
      <WelcomeScreen
        onStartSession={createSession}
        onJoinSession={joinSession}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  return (
    <div className="container">
      <SessionBar
        sessionCode={session?.code || '----'}
        connectionStatus={connectionStatus}
      />

      <div className="mainLayout">
        <ChatArea
          messages={messages}
          isLoading={isLoading}
        />

        {isSidebarVisible && (
          <FeatureSidebar
            showKBPanel={showKBPanel}
            kbSolutions={kbSolutions}
            onCloseKB={closeKBPanel}
            showTaskPanel={showTaskPanel}
            activePlan={activePlan}
            onCloseTask={closeTaskPanel}
            onCompleteStep={handleCompleteStep}
            onSkipStep={handleSkipStep}
            showTemplatePanel={showTemplatePanel}
            suggestedTemplate={suggestedTemplate}
            onCloseTemplate={closeTemplatePanel}
            onStartGuidedFix={handleStartGuidedFix}
          />
        )}
      </div>

      <Controls
        isSharing={isSharing}
        onShareScreen={handleShareScreen}
        onStopSharing={stopScreenShare}
        onCapture={handleCapture}
        onSendMessage={sendMessage}
        isLoading={isLoading}
        sessionId={session?.id || null}
        voiceEnabled={voiceEnabled}
        onToggleVoice={() => setVoiceEnabled(v => !v)}
      />

      <ScreenPreview
        stream={screenStream}
        isSharing={isSharing}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <ChatProvider>
        <SupportProvider>
          <ChatApp />
        </SupportProvider>
      </ChatProvider>
    </ThemeProvider>
  );
}
