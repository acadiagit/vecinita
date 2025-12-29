import { useState } from 'react'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import ChatWidget from './components/chat/ChatWidget'

const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default function App() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const ask = async (e) => {
    e?.preventDefault?.()
    setLoading(true)
    setError('')
    setAnswer('')
    setSources([])
    try {
      const res = await fetch(`${backendUrl}/ask?query=${encodeURIComponent(query)}`)
      if (!res.ok) throw new Error(`Backend error: ${res.status}`)
      const data = await res.json()
      setAnswer(data?.answer || '')
      setSources(data?.sources || [])
    } catch (err) {
      setError(err.message || 'Failed to fetch answer')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container py-10">
        <h1 className="text-3xl font-semibold mb-6">Vecinita Q&A</h1>
        <form onSubmit={ask} className="flex gap-3">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question…"
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Searching…' : 'Ask'}
          </Button>
        </form>

        {error && (
          <div className="mt-4 text-red-600">{error}</div>
        )}

        {answer && (
          <div className="mt-8">
            <h2 className="text-xl font-medium mb-2">Answer</h2>
            <p className="leading-relaxed">{answer}</p>

            {!!sources?.length && (
              <div className="mt-6">
                <h3 className="text-lg font-medium mb-2">Sources</h3>
                <ul className="list-disc pl-6 space-y-1">
                  {sources.map((src, i) => {
                    const item = typeof src === 'string' ? { title: src, url: src } : src
                    const label = item.title || item.url
                    return (
                      <li key={i} className="flex items-center gap-2">
                        <a href={item.url} target="_blank" rel="noreferrer" className="text-primary underline">
                          {label}
                        </a>
                        {item?.isDownload && (
                          <a href={item.url} download target="_blank" rel="noreferrer" className="text-xs underline text-primary hover:text-primary/80">
                            Download
                          </a>
                        )}
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Floating chat widget */}
      <ChatWidget backendUrl={backendUrl} />
    </div>
  )
}
