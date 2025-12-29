import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import ChatWidget from './ChatWidget.jsx'

// Mock fetch
let originalFetch
beforeEach(() => {
  originalFetch = global.fetch
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ answer: 'Test response', sources: [] }) })
})
afterEach(() => {
  global.fetch = originalFetch
})

describe('ChatWidget - Font Scaling Props', () => {
  test('accepts fontScale and setFontScale as props', () => {
    const mockSetFontScale = vi.fn()
    const { container } = render(
      <ChatWidget
        embedded
        fontScale={1.2}
        setFontScale={mockSetFontScale}
        backendUrl="/api"
      />
    )
    
    // Component should render without errors
    expect(container.querySelector('.chat-messages')).toBeInTheDocument()
  })

  test('reset button calls setFontScale with 1.1', () => {
    const mockSetFontScale = vi.fn()
    render(
      <ChatWidget
        embedded
        fontScale={1.3}
        setFontScale={mockSetFontScale}
        backendUrl="/api"
      />
    )
    
    const resetButton = screen.getByText('Reset')
    fireEvent.click(resetButton)
    
    expect(mockSetFontScale).toHaveBeenCalledWith(1.1)
  })

  test('handles null setFontScale prop gracefully', () => {
    const { container } = render(
      <ChatWidget
        embedded
        fontScale={1.1}
        setFontScale={null}
        backendUrl="/api"
      />
    )
    
    // Component should render even without setFontScale
    expect(container.querySelector('.chat-messages')).toBeInTheDocument()
  })

  test('renders font scale controls in embedded mode', () => {
    render(
      <ChatWidget
        embedded
        fontScale={1.1}
        setFontScale={vi.fn()}
        backendUrl="/api"
      />
    )
    
    // Verify font scale UI elements are present
    expect(screen.getByText('Reset')).toBeInTheDocument()
    
    // Look for A labels (small/large indicators)
    const labels = screen.queryAllByText('A')
    expect(labels.length).toBeGreaterThanOrEqual(2)
  })

  test('accepts different fontScale values as props', () => {
    const { rerender, container } = render(
      <ChatWidget
        embedded
        fontScale={0.9}
        setFontScale={vi.fn()}
        backendUrl="/api"
      />
    )
    
    // Should render with any fontScale value
    expect(container.querySelector('.chat-messages')).toBeInTheDocument()
    
    // Rerender with different value
    rerender(
      <ChatWidget
        embedded
        fontScale={1.35}
        setFontScale={vi.fn()}
        backendUrl="/api"
      />
    )
    
    // Should still render
    expect(container.querySelector('.chat-messages')).toBeInTheDocument()
  })

  test('reset button is functional regardless of fontScale prop', () => {
    const mockSetFontScale = vi.fn()
    render(
      <ChatWidget
        embedded
        fontScale={1.4}
        setFontScale={mockSetFontScale}
        backendUrl="/api"
      />
    )
    
    const resetButton = screen.getByText('Reset')
    expect(resetButton).toBeInTheDocument()
    fireEvent.click(resetButton)
    
    expect(mockSetFontScale).toHaveBeenCalled()
  })
})
