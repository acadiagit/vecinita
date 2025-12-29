import { render, screen } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import MessageBubble from './MessageBubble.jsx'

describe('MessageBubble', () => {
  test('renders assistant message with string sources', () => {
    render(<MessageBubble role="assistant" content="Answer" sources={["https://example.com/a", "https://example.com/b"]} />)
    expect(screen.getByText('Resources')).toBeInTheDocument()
    // anchors should exist for both
    expect(screen.getByText('https://example.com/a')).toBeInTheDocument()
    expect(screen.getByText('https://example.com/b')).toBeInTheDocument()
  })

  test('renders assistant message with object sources', () => {
    const sources = [
      { title: 'Doc A', url: 'https://example.com/a' },
      { title: 'Doc B', url: 'https://example.com/b', isDownload: true }
    ]
    render(<MessageBubble role="assistant" content="Answer" sources={sources} />)
    expect(screen.getByText('Resources')).toBeInTheDocument()
    expect(screen.getByText('Doc A')).toBeInTheDocument()
    expect(screen.getByText('Doc B')).toBeInTheDocument()
    // Download link should exist
    expect(screen.getAllByText('Download').length).toBeGreaterThanOrEqual(1)
  })

  test('does not render resources for user messages', () => {
    render(<MessageBubble role="user" content="Question" sources={["https://example.com/a"]} />)
    expect(screen.queryByText('Resources')).not.toBeInTheDocument()
  })
})
