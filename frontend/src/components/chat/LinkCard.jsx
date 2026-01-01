import React, { useMemo, useState, useEffect } from 'react'
import { Card, CardContent } from '../ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../ui/dialog'
import { FileText, FileSpreadsheet, FileArchive, FileJson, FileCode, File, Globe, ExternalLink, Copy, Eye, Download, Link as LinkIcon } from 'lucide-react'

export default function LinkCard({ title, url, isDownload, chunkIndex, totalChunks, charStart, charEnd, docIndex, metadata }) {
  // Check if this is an extracted link
  const isExtractedLink = metadata?.type === 'extracted_link'
  
  // For extracted links, the actual target URL is in metadata.link_target
  const actualUrl = isExtractedLink ? metadata?.link_target : url
  
  // For extracted links, show where it was found
  const sourceDisplay = isExtractedLink ? metadata?.link_source : null

  const hostname = (() => {
    try {
      return new URL(actualUrl).hostname
    } catch {
      return ''
    }
  })()

  // Compute position display text (simplified for customers)
  const positionText = useMemo(() => {
    if (totalChunks !== undefined && totalChunks !== null && totalChunks > 1) {
      return `Part ${chunkIndex + 1} of ${totalChunks}`
    }
    return null
  }, [chunkIndex, totalChunks])

  const fileExt = (() => {
    try {
      const u = new URL(actualUrl)
      const path = u.pathname.toLowerCase()
      const m = path.match(/\.([a-z0-9]+)$/)
      return m ? m[1] : ''
    } catch {
      return ''
    }
  })()

  // Clean title - if it starts with scraper metadata, use hostname instead
  const displayTitle = useMemo(() => {
    if (!title || title.startsWith('DOCUMENTS_LOADED:')) {
      return hostname || actualUrl
    }
    return title
  }, [title, hostname, actualUrl])

  const iconMeta = useMemo(() => {
    const ext = fileExt
    const lower = (ext || '').toLowerCase()
    let Icon = File
    let label = 'Document'
    
    // Extracted links have their own icon
    if (isExtractedLink) {
      Icon = LinkIcon
      label = 'Extracted Link'
      return { Icon, label }
    }
    
    switch (lower) {
      case 'pdf':
      case 'txt':
      case 'doc':
      case 'docx':
        Icon = FileText
        label = lower === 'pdf' ? 'PDF' : 'Document'
        break
      case 'csv':
      case 'xls':
      case 'xlsx':
        Icon = FileSpreadsheet
        label = 'Spreadsheet'
        break
      case 'json':
        Icon = FileJson
        label = 'JSON'
        break
      case 'zip':
      case 'tar':
      case 'gz':
        Icon = FileArchive
        label = 'Archive'
        break
      case 'html':
      case 'htm':
        Icon = FileCode
        label = 'Web Page'
        break
      default:
        if (!ext && hostname) {
          Icon = Globe
          label = 'Link'
        } else {
          Icon = File
          label = 'File'
        }
    }
    return { Icon, label }
  }, [fileExt, hostname, isExtractedLink])

  const isInternal = useMemo(() => {
    try {
      const u = new URL(actualUrl, typeof window !== 'undefined' ? window.location.origin : 'http://localhost')
      return u.origin === (typeof window !== 'undefined' ? window.location.origin : 'http://localhost')
    } catch {
      return true
    }
  }, [actualUrl])

  const [previewOpen, setPreviewOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  const downloadUrl = useMemo(() => {
    if (!isDownload) return actualUrl
    try {
      const u = new URL(actualUrl)
      if (u.hostname === 'github.com') {
        const parts = u.pathname.split('/') // ['', owner, repo, 'blob', commit, ...path]
        if (parts.length >= 5 && parts[3] === 'blob') {
          const owner = parts[1]
          const repo = parts[2]
          const commit = parts[4]
          const filePath = parts.slice(5).join('/')
          return `https://raw.githubusercontent.com/${owner}/${repo}/${commit}/${filePath}`
        }
      }
    } catch {}
    return actualUrl
  }, [actualUrl, isDownload])

  useEffect(() => {
    let t
    if (copied) {
      t = setTimeout(() => setCopied(false), 1200)
    }
    return () => { if (t) clearTimeout(t) }
  }, [copied])

  return (
    <Card className={`shadow-sm ${isExtractedLink ? 'border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950' : ''}`}>
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <div className={`w-7 h-7 rounded flex items-center justify-center shrink-0 ${isExtractedLink ? 'bg-blue-200 dark:bg-blue-800' : 'bg-secondary'}`} aria-label={`Type: ${iconMeta.label}`} title={iconMeta.label}>
            <iconMeta.Icon className={`w-4 h-4 ${isExtractedLink ? 'text-blue-700 dark:text-blue-200' : 'text-secondary-foreground'}`} aria-hidden="true" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <div className="text-sm font-medium line-clamp-2">{displayTitle}</div>
              {isExtractedLink && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200 whitespace-nowrap">
                  Link
                </span>
              )}
            </div>
            {sourceDisplay && isExtractedLink ? (
              <div className="text-xs text-muted-foreground mb-1">
                Found in: <span className="font-mono text-xs">{new URL(sourceDisplay).hostname}</span>
              </div>
            ) : hostname && (
              <div className="text-xs text-muted-foreground mb-1">{hostname}</div>
            )}
            {positionText && (
              <div className="text-xs text-muted-foreground">
                {positionText}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2 mt-1">
          <a
            href={actualUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center w-6 h-6 text-primary hover:text-primary/80 hover:bg-muted rounded transition-colors"
            title="Open link"
            aria-label="Open link"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
          {isInternal && !isExtractedLink && (
            <button
              type="button"
              className="inline-flex items-center justify-center w-6 h-6 text-primary hover:text-primary/80 hover:bg-muted rounded transition-colors"
              onClick={() => setPreviewOpen(true)}
              title="Preview document"
              aria-label="Preview document"
            >
              <Eye className="w-4 h-4" />
            </button>
          )}
          {isDownload && !isExtractedLink && (
            <a
              href={downloadUrl}
              download
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center w-6 h-6 text-primary hover:text-primary/80 hover:bg-muted rounded transition-colors"
              title="Download file"
              aria-label="Download file"
            >
              <Download className="w-4 h-4" />
            </a>
          )}
          <button
            type="button"
            className="inline-flex items-center justify-center w-6 h-6 text-primary hover:text-primary/80 hover:bg-muted rounded transition-colors"
            onClick={async () => {
              try {
                if (navigator?.clipboard?.writeText) {
                  await navigator.clipboard.writeText(actualUrl)
                  setCopied(true)
                } else {
                  // Fallback
                  setCopied(true)
                }
              } catch {
                setCopied(true)
              }
            }}
            title={copied ? 'Copied!' : 'Copy link'}
            aria-label={copied ? 'Copied!' : 'Copy link'}
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
      </CardContent>
      {isInternal && !isExtractedLink && (
        <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
          <DialogContent className="max-w-3xl w-[90vw] h-[80vh] p-0">
            <DialogHeader className="px-4 pt-3 pb-2 border-b">
              <DialogTitle className="text-base">{title || 'Preview'}</DialogTitle>
            </DialogHeader>
            <div className="w-full h-full">
              {/* Use iframe for simple same-origin preview */}
              <iframe title={title || 'preview'} src={actualUrl} className="w-full h-full" />
            </div>
          </DialogContent>
        </Dialog>
      )}
    </Card>
  )
}
