export function cn(...classes) {
  return classes.filter(Boolean).join(' ')
}

// Provider and model options for the chat UI
export const PROVIDERS = [
  { key: 'openai', label: 'OpenAI' },
  { key: 'llama', label: 'Llama' },
  { key: 'deepseek', label: 'DeepSeek' }
]

export const MODELS = {
  openai: [
    // Restrict to commonly available OpenAI chat model
    'gpt-4o-mini',
  ],
  llama: [
    // Default local Llama model from .env (OLLAMA_MODEL)
    'llama3.2',
  ],
  deepseek: [
    // DeepSeek OpenAI-compatible API models
    'deepseek-chat',
    'deepseek-reasoner',
  ],
}
