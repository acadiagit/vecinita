import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import ChatWidget from './ChatWidget.jsx'

let originalFetch
beforeEach(() => {
  originalFetch = global.fetch
  global.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ answer: 'Hi', sources: [] }) })
})
afterEach(() => {
  global.fetch = originalFetch
})

describe('ChatWidget auto language behavior', () => {
  test('omits lang param when Auto is selected', async () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)

    // Switch to Auto language
    const langSelect = screen.getByLabelText(/Idioma|Language/i)
    fireEvent.change(langSelect, { target: { value: 'auto' } })

    // Send a message in English; backend should detect language
    const input = screen.getByPlaceholderText(/Ask|Pregunta/i)
    fireEvent.change(input, { target: { value: 'How do I get help?' } })
    fireEvent.click(screen.getByText(/Send|Enviar/i))

    const getAskCalls = () => global.fetch.mock.calls.filter(c => String(c[0]).includes('/ask'))
    await waitFor(() => expect(getAskCalls().length).toBeGreaterThanOrEqual(1))

    const calledUrl = String(getAskCalls().pop()[0])
    expect(calledUrl).not.toMatch(/[?&]lang=/)
  })
})
