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
  test('renders embedded chat and auto-selects provider via config fallback', async () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)

    // Switch language to English for stable placeholders/button text
    const langSelect = screen.getByLabelText(/Idioma|Language/i)
    fireEvent.change(langSelect, { target: { value: 'en' } })

    // Type a message and send (provider/model auto-selected from config)
    const input = screen.getByPlaceholderText(/Ask/i)
    fireEvent.change(input, { target: { value: 'Hello' } })
    const sendButton = screen.getByText(/Send/i)
    fireEvent.click(sendButton)

    await waitFor(() => expect(global.fetch).toHaveBeenCalled())

    // Verify provider/model are still sent in the /ask URL (auto-selected, not user-controlled)
    const askCall = [...global.fetch.mock.calls].reverse().find(c => String(c[0]).includes('/ask'))
    const calledUrl = askCall ? askCall[0] : ''
    expect(calledUrl).toMatch(/provider=[a-z]+/) // provider is auto-selected
    expect(calledUrl).toMatch(/model=[a-z0-9.-]+/) // model is auto-selected
    expect(calledUrl).toMatch(/thread_id=[A-Za-z0-9-]+/) // contains thread_id
  })

  test('applies chat-messages class for scrollable area', () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)
    const messagesArea = document.querySelector('.chat-messages')
    expect(messagesArea).toBeInTheDocument()
  })
})
