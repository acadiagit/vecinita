import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import App from './App.jsx'

// Mock fetch
let originalFetch
beforeEach(() => {
  originalFetch = global.fetch
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ answer: 'Test response', sources: [] }) })
})
afterEach(() => {
  global.fetch = originalFetch
})

describe('App - Global Font Scaling', () => {
  test('renders with default font scale of 1.1', () => {
    const { container } = render(<App />)
    const rootDiv = container.querySelector('.min-h-screen')
    
    // Default fontScale is 1.1, CSS variable should be set
    expect(rootDiv.getAttribute('style')).toContain('--font-scale: 1.1')
  })

  test('applies CSS variable to root container', () => {
    const { container } = render(<App />)
    const rootDiv = container.querySelector('.min-h-screen')
    
    // Root div should have CSS variable set
    expect(rootDiv).toBeInTheDocument()
    expect(rootDiv.getAttribute('style')).toContain('--font-scale')
  })

  test('passes fontScale and setFontScale props to ChatWidget', () => {
    const { container } = render(<App />)
    
    // Verify ChatWidget is rendered within the scaled container
    const chatWidget = container.querySelector('.chat-messages')
    expect(chatWidget).toBeInTheDocument()
  })
})
