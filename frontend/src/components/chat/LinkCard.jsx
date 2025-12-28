import React from 'react'
import { Card, CardContent } from '../ui/card'

export default function LinkCard({ title, url, isDownload }) {
  const hostname = (() => {
    try {
      return new URL(url).hostname
    } catch {
      return ''
    }
  })()

  return (
    <Card className="shadow-sm">
      <CardContent className="p-3">
        <div className="text-sm font-medium mb-1 line-clamp-2">{title || url}</div>
        {hostname && <div className="text-xs text-muted-foreground mb-2">{hostname}</div>}
        <div className="flex gap-2">
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="text-xs underline text-primary hover:text-primary/80"
          >
            Open
          </a>
          {isDownload && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="text-xs underline text-primary hover:text-primary/80"
            >
              Download
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
