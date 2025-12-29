import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import ChatWidget from './ChatWidget.jsx'

describe('ChatWidget language welcome sync', () => {
  test('updates initial assistant welcome when language changes', () => {
    render(<ChatWidget embedded={true} initialOpen={true} />)

    // Default language is Spanish
    const esWelcome = '¡Hola! Puedo ayudarte a encontrar recursos ambientales y comunitarios cercanos. Pregúntame lo que quieras.'
    expect(screen.getByText(esWelcome)).toBeInTheDocument()

    // Change language to English via the language selector
    const langSelect = screen.getByLabelText(/Idioma|Language/i)
    fireEvent.change(langSelect, { target: { value: 'en' } })

    const enWelcome = 'Hi! I can help you find environmental and community resources nearby. Ask me anything.'
    expect(screen.getByText(enWelcome)).toBeInTheDocument()
    expect(screen.queryByText(esWelcome)).toBeNull()
  })
})
