/**
 * TypeScript interfaces for API communication
 */

export interface AgentRequest {
  prompt: string;
}

export interface AgentResponse {
  answer: string;
}

export interface ErrorResponse {
  error: string;
  code?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  llm_configured: boolean;
}

export type LoadingState = 'idle' | 'loading' | 'success' | 'error' | 'timeout';
