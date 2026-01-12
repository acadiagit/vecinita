/**
 * API Configuration and Utilities
 * Handles communication with the Vecinita backend server
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: Source[];
}

export interface Source {
  title: string;
  url: string;
  snippet: string;
}

export interface ConfigResponse {
  providers: Provider[];
  models: Model[];
}

export interface Provider {
  id: string;
  name: string;
  description?: string;
}

export interface Model {
  id: string;
  provider: string;
  name: string;
  description?: string;
}

export interface StreamEvent {
  type: 'thinking' | 'complete' | 'clarification' | 'error';
  data: string;
}

const getBackendUrl = (): string => {
  // Use VITE_BACKEND_URL from environment, otherwise fallback to localhost
  return import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
};

/**
 * Fetch available providers and models from backend
 */
export const fetchConfig = async (): Promise<ConfigResponse> => {
  const url = `${getBackendUrl()}/config`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch config: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data as ConfigResponse;
  } catch (error) {
    console.error('Error fetching config:', error);
    throw error;
  }
};

/**
 * Stream a question to the backend and handle SSE responses
 * @param query The user's question
 * @param language Language code (e.g., 'en', 'es')
 * @param provider Selected provider name
 * @param model Selected model name
 * @param threadId Optional thread ID for conversation continuity
 * @param onStream Callback for each stream event
 * @param onError Callback for errors
 */
export const streamQuestion = async (
  query: string,
  language: string,
  provider: string,
  model: string,
  threadId?: string,
  onStream?: (event: StreamEvent) => void,
  onError?: (error: Error) => void
): Promise<void> => {
  const backendUrl = getBackendUrl();
  const url = new URL('/ask-stream', backendUrl);
  
  // Add query parameters
  url.searchParams.append('query', query);
  url.searchParams.append('lang', language);
  url.searchParams.append('provider', provider);
  url.searchParams.append('model', model);
  
  if (threadId) {
    url.searchParams.append('thread_id', threadId);
  }
  
  try {
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error(`Failed to stream question: ${response.status} ${response.statusText}`);
    }
    
    if (!response.body) {
      throw new Error('Response body is empty');
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        // Decode the chunk and split by newlines
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.substring(6); // Remove 'data: ' prefix
            
            try {
              const event = JSON.parse(jsonStr) as StreamEvent;
              
              if (onStream) {
                onStream(event);
              }
              
              // Stop on error
              if (event.type === 'error') {
                throw new Error(event.data);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE event:', parseError);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    const err = error instanceof Error ? error : new Error(String(error));
    if (onError) {
      onError(err);
    } else {
      throw err;
    }
  }
};

/**
 * Generate a unique thread ID for conversation persistence
 */
export const generateThreadId = (): string => {
  return `thread_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Get or create a thread ID from localStorage
 */
export const getOrCreateThreadId = (): string => {
  const key = 'vecinita_thread_id';
  let threadId = localStorage.getItem(key);
  
  if (!threadId) {
    threadId = generateThreadId();
    localStorage.setItem(key, threadId);
  }
  
  return threadId;
};
