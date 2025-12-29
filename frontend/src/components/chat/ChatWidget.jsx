import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Slider } from '../ui/slider'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog'
import MessageBubble from './MessageBubble'
import { PROVIDERS, MODELS } from '../../lib/utils'

// Simple i18n strings
const STRINGS = {
  en: {
    title: 'VECINA Assistant',
    placeholder: 'Ask about local resources…',
    send: 'Send',
    welcome:
      'Hi! I can help you find environmental and community resources nearby. Ask me anything.',
    languageLabel: 'Language',
    languageAuto: 'Auto',
    modeLabel: 'Mode',
    modeChat: 'Chat',
    modeQna: 'Q&A',
    answerLabel: 'Answer',
    minimizedLabel: 'English'
  },
  es: {
    title: 'Asistente VECINA',
    placeholder: 'Pregunta sobre recursos locales…',
    send: 'Enviar',
    welcome:
      '¡Hola! Puedo ayudarte a encontrar recursos ambientales y comunitarios cercanos. Pregúntame lo que quieras.',
    languageLabel: 'Idioma',
    languageAuto: 'Automático',
    modeLabel: 'Modo',
    modeChat: 'Chat',
    modeQna: 'Preguntas y respuestas',
    answerLabel: 'Respuesta',
    minimizedLabel: 'Español'
  }
}

export default function ChatWidget({ backendUrl, embedded = false, initialOpen = false, hideMinimizedBar = false, className = '', fontScale = 1.1, setFontScale = null }) {
  const [open, setOpen] = useState(initialOpen || embedded)
  const [lang, setLang] = useState('auto')
  const [provider, setProvider] = useState('llama')
  const [model, setModel] = useState(MODELS['llama'][0])
  const [mode, setMode] = useState('chat') // 'chat' | 'qna'
  const [messages, setMessages] = useState([
    { role: 'assistant', content: STRINGS.es.welcome, sources: [] }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef(null)
  const threadIdRef = useRef(null)
  const [providersOptions, setProvidersOptions] = useState(PROVIDERS)
  const [modelOptionsMap, setModelOptionsMap] = useState(MODELS)

  // Generate a stable thread ID per widget session to enable backend memory
  if (!threadIdRef.current) {
    try {
      const stored = typeof localStorage !== 'undefined' ? localStorage.getItem('vecinita_thread_id') : null
      const newId = stored || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `thread-${Date.now()}-${Math.floor(Math.random()*1e6)}`)
      threadIdRef.current = newId
      if (typeof localStorage !== 'undefined' && !stored) {
        localStorage.setItem('vecinita_thread_id', newId)
      }
    } catch (_) {
      const newId = `thread-${Date.now()}-${Math.floor(Math.random()*1e6)}`
      threadIdRef.current = newId
      try { if (typeof localStorage !== 'undefined') localStorage.setItem('vecinita_thread_id', newId) } catch (_) {}
    }
  }

  const t = useMemo(() => STRINGS[lang] || STRINGS.en, [lang])

  useEffect(() => {
    // auto scroll to bottom on new messages (jsdom-safe)
    const el = listRef.current
    if (!el) return
    try {
      if (typeof el.scrollTo === 'function') {
        el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
      } else {
        el.scrollTop = el.scrollHeight
      }
    } catch (_) {
      // no-op in test environment
    }
  }, [messages])

  // Keep the initial welcome message in sync with the selected language
  useEffect(() => {
    setMessages((m) => {
      if (m.length === 1 && m[0]?.role === 'assistant' && (m[0]?.sources?.length ?? 0) === 0) {
        return [{ ...m[0], content: t.welcome }]
      }
      return m
    })
  }, [t.welcome])

  useEffect(() => {
    // ensure model resets when provider changes
    const first = (modelOptionsMap[provider] || MODELS[provider])?.[0]
    if (first) setModel(first)
  }, [provider, modelOptionsMap])

  // Try to load providers/models from backend /config for dynamic options and auto-select priority
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const base = backendUrl || '/api'
        if (typeof fetch !== 'function') return
        const res = await fetch(`${base}/config`)
        if (!res?.ok) return
        const data = await res.json()
        const providers = Array.isArray(data?.providers) ? data.providers : null
        const models = typeof data?.models === 'object' && data.models ? data.models : null
        if (providers && models) {
          setProvidersOptions(providers)
          setModelOptionsMap(models)
          // Auto-select provider with fallback priority: deepseek > llama > openai
          const priority = ['deepseek', 'llama', 'openai']
          let selectedProvider = priority.find(p => providers.some(prov => prov.key === p))
          if (!selectedProvider && providers.length) {
            selectedProvider = providers[0].key
          }
          if (selectedProvider) {
            setProvider(selectedProvider)
            const firstModel = (models[selectedProvider] || [])?.[0]
            if (firstModel) setModel(firstModel)
          }
        }
      } catch (_) {
        // ignore
      }
    }
    loadConfig()
  }, [backendUrl])

  const startNewChat = () => {
    // Reset messages to single welcome message and generate new thread
    setMessages([{ role: 'assistant', content: (STRINGS[lang] || STRINGS.en).welcome, sources: [] }])
    try {
      const newId = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : `thread-${Date.now()}-${Math.floor(Math.random()*1e6)}`
      threadIdRef.current = newId
      if (typeof localStorage !== 'undefined') localStorage.setItem('vecinita_thread_id', newId)
    } catch (_) {}
  }

  const sendMessage = async () => {
    const q = input.trim()
    if (!q) return
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setLoading(true)
    try {
      const urlBase = backendUrl || '/api'
      // Chat-only: always use persistent thread id for conversational memory
      const thread = threadIdRef.current
      const langParam = lang === 'auto' ? '' : `&lang=${lang}`
      const url = `${urlBase}/ask?query=${encodeURIComponent(q)}${langParam}&provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}&thread_id=${encodeURIComponent(thread)}`
      const res = await fetch(url)
      if (!res.ok) throw new Error(`Backend error: ${res.status}`)
      const data = await res.json()
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: data?.answer || 'No response provided.',
          sources: data?.sources || []
        }
      ])
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: `Error: ${err.message}` }
      ])
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Embedded mode: render only the chat content block, no floating/minimized bar
  if (embedded) {
    return (
      <div className={className || 'grid w-full max-w-lg gap-4 border bg-background shadow-lg sm:rounded-lg w-[360px] max-w-[90vw] p-0 flex flex-col max-h-[600px] overflow-hidden'}>
        <h2 className="sr-only">{t.title}</h2>
        <p className="sr-only">Chat with the Vecinita assistant to find local resources</p>
        <div className="px-4 pt-3 pb-2 border-b flex flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-primary flex items-center justify-center">
              <span className="text-xs font-bold text-primary-foreground">V</span>
            </div>
            <div className="font-semibold">{t.title}</div>
          </div>
          <div className="flex items-center gap-1">
            <select
              className="h-8 rounded-md border border-input bg-background px-2 text-sm"
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label={t.languageLabel}
            >
              <option value="es">Español</option>
              <option value="en">English</option>
              <option value="auto">{t.languageAuto}</option>
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={startNewChat}
              className="text-xs px-2 h-8"
            >
              New Chat
            </Button>
          </div>
        </div>

        <div className="px-4 py-2 border-b flex items-center gap-2">
          <span className="text-xs">A</span>
          <Slider
            min={0.8}
            max={1.4}
            step={0.05}
            value={[fontScale]}
            onValueChange={(val) => setFontScale && setFontScale(val[0])}
            className="flex-1"
          />
          <span className="text-xs">A</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFontScale && setFontScale(1.1)}
            className="text-xs px-2 h-8"
          >
            Reset
          </Button>
        </div>

        <div ref={listRef} className="flex-1 chat-messages p-3 bg-muted/30 min-w-0">
          {messages.map((m, i) => (
            <MessageBubble
              key={i}
              role={m.role}
              content={m.content}
              sources={m.sources}
            />
          ))}
        </div>

        <div className="px-4 py-3 border-t">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={t.placeholder}
            />
            <Button onClick={sendMessage} disabled={loading}>
              {loading ? '…' : t.send}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ fontSize: `${Math.round(14 * fontScale)}px` }} className="fixed bottom-4 right-4 z-50">
      {/* Minimized bar */}
      {!open && !hideMinimizedBar && (
        <div className="flex items-center gap-2">
          <select
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            aria-label={t.languageLabel}
          >
            <option value="es">Español</option>
            <option value="en">English</option>
            <option value="auto">{t.languageAuto}</option>
          </select>
          <Button variant="default" onClick={() => setOpen(true)}>
            Chat
          </Button>
        </div>
      )}

      {/* Chat window using Dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="w-[360px] max-w-[90vw] sm:rounded-lg p-0 flex flex-col max-h-[600px] overflow-hidden">
          <DialogTitle className="sr-only">{t.title}</DialogTitle>
          <DialogDescription className="sr-only">
            Chat with the Vecinita assistant to find local resources
          </DialogDescription>
          <DialogHeader className="px-4 pt-3 pb-2 border-b flex flex-row items-center justify-between space-y-0">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-primary flex items-center justify-center">
                <span className="text-xs font-bold text-primary-foreground">V</span>
              </div>
              <div className="font-semibold">{t.title}</div>
            </div>
            <div className="flex items-center gap-1">
              <select
                className="h-8 rounded-md border border-input bg-background px-2 text-sm"
                value={lang}
                onChange={(e) => setLang(e.target.value)}
                aria-label={t.languageLabel}
              >
                <option value="es">Español</option>
                <option value="en">English</option>
                <option value="auto">{t.languageAuto}</option>
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={startNewChat}
                className="text-xs px-2 h-8"
              >
                New Chat
              </Button>
            </div>
          </DialogHeader>

          {/* Font size slider */}
          <div className="px-4 py-2 border-b flex items-center gap-2">
            <span className="text-xs">A</span>
            <Slider
              min={0.8}
              max={1.4}
              step={0.05}
              value={[fontScale]}
              onValueChange={(val) => setFontScale(val[0])}
              className="flex-1"
            />
            <span className="text-xs">A</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFontScale(1)}
              className="text-xs px-2 h-8"
            >
              Reset
            </Button>
          </div>

          {/* Messages area with custom scrollbar */}
          <div ref={listRef} className="flex-1 chat-messages p-3 bg-muted/30 min-w-0 flex flex-col overflow-y-auto">
            {messages.map((m, i) => (
              <MessageBubble
                key={i}
                role={m.role}
                content={m.content}
                sources={m.sources}
              />
            ))}
          </div>

          {/* Input area */}
          <div className="px-4 py-3 border-t">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder={t.placeholder}
              />
              <Button onClick={sendMessage} disabled={loading}>
                {loading ? '…' : t.send}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
