import { useState } from 'react'
import ChatWidget from './components/chat/ChatWidget'

const backendUrl = import.meta.env.VITE_BACKEND_URL || '/api'

export default function App() {
  const [fontScale, setFontScale] = useState(1.1)

  return (
    <div
      style={{ '--font-scale': fontScale }}
      className="min-h-screen bg-background text-foreground [&_*]:text-[calc(1rem*var(--font-scale))] flex flex-col"
    >
      <div className="w-full flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-3xl flex flex-col">
          <h1 className="text-2xl font-semibold mb-4 text-center">Vecinita Assistant</h1>
          {/* Full-page embedded chat */}
          <ChatWidget
            backendUrl={backendUrl}
            embedded
            fontScale={fontScale}
            setFontScale={setFontScale}
            className="w-full bg-background border rounded-lg shadow-sm p-0 flex flex-col min-h-[60vh]"
          />
        </div>
      </div>
    </div>
  )
}
