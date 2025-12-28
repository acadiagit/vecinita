import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Slider } from '../ui/slider'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog'
import MessageBubble from './MessageBubble'

// Simple i18n strings
const STRINGS = {
  en: {
    title: 'VECINA Assistant',
    placeholder: 'Ask about local resources…',
    send: 'Send',
    welcome:
      'Hi! I can help you find environmental and community resources nearby. Ask me anything.',
    languageLabel: 'Language',
    minimizedLabel: 'English'
  },
  es: {
    title: 'Asistente VECINA',
    placeholder: 'Pregunta sobre recursos locales…',
    send: 'Enviar',
    welcome:
      '¡Hola! Puedo ayudarte a encontrar recursos ambientales y comunitarios cercanos. Pregúntame lo que quieras.',
    languageLabel: 'Idioma',
    minimizedLabel: 'Español'
  }
}

export default function ChatWidget({ backendUrl }) {
  const [open, setOpen] = useState(false)
  const [lang, setLang] = useState('es')
  const [fontScale, setFontScale] = useState(1)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: STRINGS.es.welcome, sources: [] }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const listRef = useRef(null)

  const t = useMemo(() => STRINGS[lang] || STRINGS.en, [lang])

  useEffect(() => {
    // auto scroll to bottom on new messages
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    const q = input.trim()
    if (!q) return
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setLoading(true)
    try {
      const urlBase = backendUrl || '/api'
      const url = `${urlBase}/ask?query=${encodeURIComponent(q)}&lang=${lang}`
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

  return (
    <div style={{ fontSize: `${Math.round(14 * fontScale)}px` }} className="fixed bottom-4 right-4 z-50">
      {/* Minimized bar */}
      {!open && (
        <div className="flex items-center gap-2">
          <select
            className="h-9 rounded-md border border-input bg-background px-2 text-sm"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            aria-label={t.languageLabel}
          >
            <option value="es">Español</option>
            <option value="en">English</option>
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
              </select>
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

          {/* Messages area */}
          <div ref={listRef} className="flex-1 overflow-y-auto p-3 bg-muted/30 min-w-0">
            {messages.map((m, i) => (
              <MessageBubble key={i} role={m.role} content={m.content} sources={m.sources} />
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
