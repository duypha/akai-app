// Message types
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
}

// Session types
export interface Session {
  id: string;
  code: string;
  createdAt: Date;
  messages: Message[];
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Voice state
export interface VoiceState {
  isRecording: boolean;
  isProcessing: boolean;
  error?: string;
}

// Screen sharing state
export interface ScreenState {
  isSharing: boolean;
  stream?: MediaStream;
}

// Chat input state
export interface ChatInputState {
  message: string;
  isLoading: boolean;
}

// Settings
export interface Settings {
  theme: Theme;
  voiceEnabled: boolean;
  soundEnabled: boolean;
  fontSize: 'small' | 'medium' | 'large';
}

// API Response types
export interface SessionResponse {
  session_id: string;
  code: string;
  created_at: string;
  message: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface TranscribeResponse {
  transcript: string;
  session_id: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  name: string;
  capabilities: string[];
}

// Knowledge Base types
export interface KBSolution {
  id: string;
  title: string;
  problem_title?: string;
  success_rate?: number;
  steps: string[];
}

// Task Plan types
export interface TaskStep {
  id: string;
  title: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
}

export interface TaskPlan {
  id: string;
  title: string;
  status: 'created' | 'in_progress' | 'completed';
  steps: TaskStep[];
  progress: {
    completed: number;
    total: number;
    percent: number;
  };
}

// Template types
export interface TaskTemplate {
  id: string;
  name: string;
  steps: { title: string }[];
}

// WebSocket message types
export type WSMessage =
  | { type: 'ai_response'; response: string }
  | { type: 'transcript'; text: string }
  | { type: 'kb_match'; problems: string[]; top_solutions: KBSolution[] }
  | { type: 'template_detected'; template: TaskTemplate }
  | { type: 'task_created'; plan: TaskPlan }
  | { type: 'task_started'; plan: TaskPlan }
  | { type: 'step_completed'; plan: TaskPlan; next_step: TaskStep | null; is_complete: boolean }
  | { type: 'step_failed'; plan: TaskPlan; failed_step: TaskStep; error_message: string }
  | { type: 'pong' };

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';
