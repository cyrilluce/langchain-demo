/// <reference types="vite/client" />
/**
 * API service for communicating with the FastAPI backend
 */

import { UIMessage } from 'ai';
import type { AgentRequest, AgentResponse, ErrorResponse } from '../types';

// Read API base URL from Vite env with a sensible default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';
const REQUEST_TIMEOUT = 360000; // 6 minutes in milliseconds

export class ApiError extends Error {
  constructor(
    message: string,
    public code?: string,
    public status?: number
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timed out after 6 minutes') {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * Submit a prompt to the agent endpoint with timeout handling
 */
export async function submitPrompt(prompt: string): Promise<string> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}/agent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt } as AgentRequest),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      // Handle HTTP errors
      if (response.status === 503) {
        const errorData: ErrorResponse = await response.json();
        throw new ApiError(
          errorData.error || 'LLM service unavailable',
          errorData.code,
          503
        );
      }

      if (response.status === 422) {
        throw new ApiError('Invalid prompt. Please check your input.', 'VALIDATION_ERROR', 422);
      }

      throw new ApiError(`HTTP ${response.status}: ${response.statusText}`, undefined, response.status);
    }

    const data: AgentResponse = await response.json();
    return data.answer;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new TimeoutError();
      }
      throw new ApiError(`Network error: ${error.message}`);
    }

    throw new ApiError('An unexpected error occurred');
  }
}

/**
 * Check server health status
 */
export async function checkHealth(): Promise<{ status: string; llm_configured: boolean }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new ApiError(`Health check failed: ${response.statusText}`, undefined, response.status);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to check server health');
  }
}

/**
 * Get conversation history for a thread
 */
export async function getHistory(
  threadId: string,
  checkpointId?: string
): Promise<UIMessage[]> {
  try {
    const url = new URL(`${API_BASE_URL}/chat/${threadId}/history`);
    if (checkpointId) {
      url.searchParams.set('checkpoint_id', checkpointId);
    }

    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new ApiError(`Failed to get history: ${response.statusText}`, undefined, response.status);
    }

    const data = await response.json();
    return data.messages || [];
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError('Failed to get conversation history');
  }
}
