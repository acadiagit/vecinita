import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import LinkCard from './LinkCard'

export default function MessageBubble({ role = 'assistant', content, sources = [], headerLabel }) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 min-w-0 w-full`}>
      <div
        className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed shadow-sm overflow-hidden break-words ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground'
        }`}
      >
        {headerLabel && !isUser && (
          <div className="text-xs font-semibold mb-1 opacity-80">{headerLabel}</div>
        )}
        {isUser ? (
          <div>{content}</div>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 leading-relaxed">{children}</p>,
              ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1">{children}</ol>,
              ul: ({ children }) => <ul className="list-disc pl-5 space-y-1">{children}</ul>,
              li: ({ children }) => <li className="leading-relaxed">{children}</li>,
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noreferrer" className="underline">
                  {children}
                </a>
              )
            }}
          >
            {content}
          </ReactMarkdown>
        )}
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
