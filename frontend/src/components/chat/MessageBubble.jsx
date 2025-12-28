import React from 'react'
import LinkCard from './LinkCard'

export default function MessageBubble({ role = 'assistant', content, sources = [] }) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 min-w-0`}>
      <div
        className={`max-w-[75%] rounded-lg px-3 py-2 text-sm leading-relaxed shadow-sm overflow-hidden ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
        }`}
      >
        <div>{content}</div>
        {!isUser && !!sources?.length && (
          <div className="mt-3 min-w-0">
            <div className="text-xs font-semibold mb-2 opacity-80">Resources</div>
            <div className="grid grid-cols-1 gap-2 min-w-0">
              {sources.map((s, i) => {
                const item = typeof s === 'string' ? { title: s, url: s } : s
                return <LinkCard key={i} title={item.title} url={item.url} isDownload={item.isDownload} />
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
