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

describe('ChatWidget chat-only behavior', () => {
  test('Uses persistent thread_id and no mode param', async () => {
    render(<ChatWidget embedded initialOpen hideMinimizedBar backendUrl="/api" />)

    // Ensure no Q&A toggle is present
    const qnaButton = screen.queryByRole('button', { name: /Q&A|Preguntas y respuestas/i })
    expect(qnaButton).toBeNull()

    const input = screen.getByPlaceholderText(/Ask|Pregunta/i)
    fireEvent.change(input, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByText(/Send|Enviar/i))

    fireEvent.change(input, { target: { value: 'Again' } })
    await waitFor(() => expect(screen.getByText(/Send|Enviar/i)).toBeInTheDocument())
    fireEvent.click(screen.getByText(/Send|Enviar/i))

    const getAskCalls = () => global.fetch.mock.calls.filter(c => String(c[0]).includes('/ask'))
    await waitFor(() => expect(getAskCalls().length).toBe(2))

    const calls = getAskCalls()
    const url1 = String(calls[calls.length - 2][0])
    const url2 = String(calls[calls.length - 1][0])

    const getParam = (url, key) => new URL(url, 'http://localhost').searchParams.get(key)
    const t1 = getParam(url1, 'thread_id')
    const t2 = getParam(url2, 'thread_id')
    expect(t1).toBeTruthy()
    expect(t2).toBeTruthy()
    expect(t1).toEqual(t2)

    // Ensure mode param is not present
    expect(getParam(url1, 'mode')).toBeNull()
    expect(getParam(url2, 'mode')).toBeNull()
  })
})
