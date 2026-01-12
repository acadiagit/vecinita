import React, { useState, useRef, useEffect } from 'react';
import { Send, Home, MessageSquare, Settings, ChevronDown } from 'lucide-react';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { AccessibilityProvider } from './context/AccessibilityContext';
import { ChatMessage, Message } from './components/ChatMessage';
import { ThemeToggle } from './components/ThemeToggle';
import { LanguageSelector } from './components/LanguageSelector';
import { AccessibilityPanel } from './components/AccessibilityPanel';
import { Source } from './components/SourceCard';
import { fetchConfig, streamQuestion, getOrCreateThreadId, ConfigResponse, StreamEvent } from '../api/client';

function ChatInterface() {
  const { t, language } = useLanguage();
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAccessibilityOpen, setIsAccessibilityOpen] = useState(false);
  const [thinkingMessageIndex, setThinkingMessageIndex] = useState(0);
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  // Load thread ID and config on mount
  useEffect(() => {
    setThreadId(getOrCreateThreadId());
    
    const loadConfig = async () => {
      try {
        setIsLoadingConfig(true);
        setConfigError(null);
        const configData = await fetchConfig();
        setConfig(configData);
        
        // Set default provider and model
        if (configData.providers.length > 0 && configData.models.length > 0) {
          const defaultProvider = configData.providers[0].id;
          const defaultModel = configData.models.find((m) => m.provider === defaultProvider)?.id || configData.models[0].id;
          setSelectedProvider(defaultProvider);
          setSelectedModel(defaultModel);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to load configuration';
        console.error('Config loading error:', message);
        setConfigError(message);
      } finally {
        setIsLoadingConfig(false);
      }
    };
    
    loadConfig();
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add or update welcome message when language changes
    if (messages.length === 0) {
      setMessages([
        {
          id: '0',
          role: 'assistant',
          content: t('welcomeMessage'),
          timestamp: new Date(),
        },
      ]);
    } else {
      // Update the welcome message if it's the first message
      setMessages((prev) => {
        if (prev.length > 0 && prev[0].id === '0') {
          return [
            {
              ...prev[0],
              content: t('welcomeMessage'),
            },
            ...prev.slice(1),
          ];
        }
        return prev;
      });
    }
  }, [language]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedProvider || !selectedModel || !threadId) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Create placeholder for assistant response
    const assistantId = (Date.now() + 1).toString();
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      sources: [],
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      let responseContent = '';
      let responseSources: Source[] = [];

      await streamQuestion(
        input,
        language,
        selectedProvider,
        selectedModel,
        threadId,
        (event: StreamEvent) => {
          if (event.type === 'thinking') {
            // Thinking events are transient, don't add to message
            console.log('Thinking:', event.data);
          } else if (event.type === 'complete') {
            // Parse JSON response with content and sources
            try {
              const data = JSON.parse(event.data);
              responseContent = data.answer || '';
              responseSources = data.sources || [];
              
              // Update the assistant message with response
              setMessages((prev) => {
                const updated = [...prev];
                const lastIndex = updated.length - 1;
                if (lastIndex >= 0 && updated[lastIndex].id === assistantId) {
                  updated[lastIndex] = {
                    ...updated[lastIndex],
                    content: responseContent,
                    sources: responseSources,
                  };
                }
                return updated;
              });
            } catch (parseError) {
              console.warn('Failed to parse complete event:', parseError);
              responseContent = event.data;
            }
          } else if (event.type === 'clarification') {
            // Handle clarification requests
            console.log('Clarification needed:', event.data);
            responseContent = event.data;
            setMessages((prev) => {
              const updated = [...prev];
              const lastIndex = updated.length - 1;
              if (lastIndex >= 0 && updated[lastIndex].id === assistantId) {
                updated[lastIndex] = {
                  ...updated[lastIndex],
                  content: responseContent,
                };
              }
              return updated;
            });
          } else if (event.type === 'error') {
            throw new Error(event.data);
          }
        }
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to get response';
      console.error('Stream error:', errorMessage);
      
      // Update message with error
      setMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        if (lastIndex >= 0 && updated[lastIndex].id === assistantId) {
          updated[lastIndex] = {
            ...updated[lastIndex],
            content: `Error: ${errorMessage}`,
          };
        }
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([
      {
        id: '0',
        role: 'assistant',
        content: t('welcomeMessage'),
        timestamp: new Date(),
      },
    ]);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Handle ESC key to close accessibility panel
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isAccessibilityOpen) {
        setIsAccessibilityOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isAccessibilityOpen]);

  // Cycle through thinking messages
  useEffect(() => {
    if (!isLoading) {
      setThinkingMessageIndex(0);
      return;
    }

    const thinkingMessages = t('thinkingMessages').split('|');
    const interval = setInterval(() => {
      setThinkingMessageIndex((prev) => (prev + 1) % thinkingMessages.length);
    }, 800);

    return () => clearInterval(interval);
  }, [isLoading, language]);

  const getThinkingMessage = () => {
    const thinkingMessages = t('thinkingMessages').split('|');
    return thinkingMessages[thinkingMessageIndex] || thinkingMessages[0];
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-2 sm:px-4 py-2 sm:py-3">
          <div className="flex items-center justify-between gap-1 sm:gap-2 mb-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-primary rounded-lg flex items-center justify-center shrink-0">
                <Home className="w-4 h-4 sm:w-6 sm:h-6 text-primary-foreground" aria-hidden="true" />
              </div>
              <div className="min-w-0">
                <h1 className="text-base sm:text-xl text-foreground truncate">{t('appTitle')}</h1>
                <p className="text-xs sm:text-sm text-muted-foreground hidden sm:block">
                  {t('appSubtitle')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1 sm:gap-2 shrink-0">
              <button
                onClick={handleNewChat}
                className="p-2 sm:px-3 sm:py-2 rounded-lg hover:bg-accent transition-colors flex items-center gap-2"
                aria-label={t('newChat')}
                title={t('newChat')}
              >
                <MessageSquare className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
                <span className="hidden md:inline text-foreground">{t('newChat')}</span>
              </button>
              <button
                onClick={() => setIsAccessibilityOpen(true)}
                className="p-2 rounded-lg hover:bg-accent transition-colors"
                aria-label={t('accessibility')}
                title={t('accessibility')}
              >
                <Settings className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
              </button>
              <LanguageSelector />
              <ThemeToggle theme={theme} setTheme={setTheme} />
            </div>
          </div>
          
          {/* Provider/Model Selection */}
          {!isLoadingConfig && config && (
            <div className="flex flex-wrap gap-2 text-sm">
              {/* Provider Dropdown */}
              <div className="flex items-center gap-2">
                <label htmlFor="provider-select" className="text-muted-foreground">
                  Provider:
                </label>
                <select
                  id="provider-select"
                  value={selectedProvider}
                  onChange={(e) => {
                    setSelectedProvider(e.target.value);
                    // Reset model to first available for this provider
                    const firstModel = config.models.find((m) => m.provider === e.target.value);
                    if (firstModel) {
                      setSelectedModel(firstModel.id);
                    }
                  }}
                  className="px-2 py-1 rounded border border-border bg-background text-foreground text-xs"
                >
                  {config.providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Model Dropdown */}
              <div className="flex items-center gap-2">
                <label htmlFor="model-select" className="text-muted-foreground">
                  Model:
                </label>
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="px-2 py-1 rounded border border-border bg-background text-foreground text-xs"
                >
                  {config.models
                    .filter((m) => m.provider === selectedProvider)
                    .map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                </select>
              </div>
            </div>
          )}
          
          {isLoadingConfig && (
            <p className="text-xs text-muted-foreground">Loading provider configuration...</p>
          )}
          
          {configError && (
            <p className="text-xs text-red-500">Config error: {configError}</p>
          )}
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto" role="main">
        <div className="container mx-auto max-w-4xl px-0 sm:px-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="flex gap-2 sm:gap-3 p-3 sm:p-4 bg-muted/30" role="status" aria-live="polite">
              <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                <div className="w-4 h-4 sm:w-5 sm:h-5 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" aria-hidden="true" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm sm:text-base text-muted-foreground break-words">{getThinkingMessage()}</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input */}
      <footer className="border-t border-border bg-card">
        <div className="container mx-auto max-w-4xl p-2 sm:p-4">
          <form onSubmit={handleSubmit} className="flex gap-1.5 sm:gap-2">
            <label htmlFor="message-input" className="sr-only">
              {t('typePlaceholder')}
            </label>
            <textarea
              ref={inputRef}
              id="message-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('typePlaceholder')}
              className="flex-1 px-3 py-2 sm:px-4 sm:py-3 rounded-lg border border-border bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary text-sm sm:text-base"
              rows={1}
              disabled={isLoading}
              aria-label={t('typePlaceholder')}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 sm:px-6 sm:py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              aria-label={t('sendMessage')}
            >
              <Send className="w-4 h-4 sm:w-5 sm:h-5" aria-hidden="true" />
            </button>
          </form>
          <p className="text-[10px] sm:text-xs text-muted-foreground text-center mt-1.5 sm:mt-2 px-2">
            {language === 'es'
              ? configError 
                ? 'Error de conexión con el backend. Verifica que esté corriendo en ' + (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000')
                : isLoading ? 'Conectando con el backend...' : 'Conectado a la base de datos vectorial'
              : configError 
              ? 'Backend connection error. Check that it\'s running at ' + (import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000')
              : isLoading ? 'Connecting to backend...' : 'Connected to vector database'}
          </p>
        </div>
      </footer>

      {/* Accessibility Panel */}
      <AccessibilityPanel
        isOpen={isAccessibilityOpen}
        onClose={() => setIsAccessibilityOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <ChatInterface />
      </AccessibilityProvider>
    </LanguageProvider>
  );
}