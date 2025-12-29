import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import ChatWidget from './ChatWidget.jsx'

// Mock fetch
let originalFetch
beforeEach(() => {
  originalFetch = global.fetch
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ answer: 'Hi', sources: [] }) })
})
afterEach(() => {
  global.fetch = originalFetch
})

describe('ChatWidget', () => {
  test('renders embedded chat and sends provider/model in request', async () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)

    // Switch language to English for stable placeholders/button text
    const langSelect = screen.getByLabelText(/Idioma|Language/i)
    fireEvent.change(langSelect, { target: { value: 'en' } })

    // Select provider and model
    const providerSelect = screen.getByLabelText('Model Provider')
    fireEvent.change(providerSelect, { target: { value: 'openai' } })

    const modelSelect = screen.getByLabelText('Model')
    fireEvent.change(modelSelect, { target: { value: 'gpt-4o-mini' } })

    // Type a message and send
    const input = screen.getByPlaceholderText(/Ask/i)
    fireEvent.change(input, { target: { value: 'Hello' } })
    const sendButton = screen.getByText(/Send/i)
    fireEvent.click(sendButton)

    await waitFor(() => expect(global.fetch).toHaveBeenCalled())

    // Verify provider/model appear in URL
    const calledUrl = global.fetch.mock.calls[0][0]
    expect(calledUrl).toContain('provider=openai')
    expect(calledUrl).toContain('model=gpt-4o-mini')
  })

  test('applies chat-messages class for scrollable area', () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)
    const messagesArea = document.querySelector('.chat-messages')
    expect(messagesArea).toBeInTheDocument()
  })
})
