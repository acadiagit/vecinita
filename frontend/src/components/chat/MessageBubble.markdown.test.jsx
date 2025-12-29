import { render, screen } from '@testing-library/react'
import { describe, test, expect } from 'vitest'
import MessageBubble from './MessageBubble.jsx'

/**
 * Verifies Markdown rendering for assistant messages: bold, ordered lists, and links.
 */

describe('MessageBubble Markdown rendering', () => {
  test('renders ordered list and bold inside assistant bubble', () => {
    const markdown = [
      'No pude encontrar una respuesta definitiva en los documentos proporcionados.',
      '',
      '1. **Red de profesionales**: Busca médicos que hablen tu idioma.',
      '2. **Bases de datos médicas**: Revisa fuentes oficiales.',
      '3. **Redes sociales**: Consulta perfiles y comunidades.',
      '4. **Asociaciones de profesionales**: Contacta colegios médicos.',
      '',
      '(Fuente: https://www.who.int/es/news-room/fact-sheets/detail/migrant-health)'
    ].join('\n')

    render(<MessageBubble role="assistant" content={markdown} sources={[]} />)

    // Ordered list exists with at least 4 items
    const ol = screen.getByRole('list')
    const items = screen.getAllByRole('listitem')
    expect(ol).toBeInTheDocument()
    expect(items.length).toBeGreaterThanOrEqual(4)

    // Bold text appears
    expect(screen.getByText(/Red de profesionales/i)).toBeInTheDocument()

    // Link is rendered
    const link = screen.getByRole('link', { name: /migrant-health/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', expect.stringContaining('who.int'))
  })
})
