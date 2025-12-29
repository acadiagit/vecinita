import { test, expect } from '@playwright/test'

test.describe('ChatWidget E2E', () => {
  test('sends messages and shows back-and-forth with thread_id', async ({ page }) => {
    // Intercept backend endpoints
    await page.route('**/api/config', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          providers: [
            { key: 'openai', label: 'OpenAI' },
            { key: 'llama', label: 'Llama' },
          ],
          models: {
            openai: ['gpt-4o-mini'],
            llama: ['llama3.2'],
          },
        }),
      })
    })

    await page.route('**/api/ask**', async (route) => {
      const url = new URL(route.request().url())
      const query = url.searchParams
      // Basic param checks
      expect(query.get('query')).toBeTruthy()
      expect(query.get('lang')).toBeTruthy()
      expect(query.get('provider')).toBeTruthy()
      expect(query.get('model')).toBeTruthy()
      expect(query.get('thread_id')).toBeTruthy()
      // Respond with a simple answer
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ answer: 'Hi there!', sources: [] }),
      })
    })

    // Go to app
    await page.goto('/')

    // Open chat if minimized
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Switch to English for stable strings
    await page.getByLabel(/Idioma|Language/i).selectOption('en')
    await page.getByLabel('Model Provider').selectOption('openai')
    await page.getByLabel('Model', { exact: true }).selectOption('gpt-4o-mini')

    // First turn
    await page.getByPlaceholder('Ask about local resources…').fill('Hello')
    const req1 = page.waitForRequest('**/api/ask**')
    await page.getByRole('button', { name: 'Send' }).click()
    await req1
    await expect(page.getByText('Hi there!')).toBeVisible()

    // Second turn
    await page.getByPlaceholder('Ask about local resources…').fill('How are you?')
    const req2 = page.waitForRequest('**/api/ask**')
    await page.getByRole('button', { name: 'Send' }).click()
    await req2

    // Both assistant messages visible
    const assistantMessages = page.locator('.bg-muted')
    await expect(assistantMessages).toHaveCount(3) // welcome + 2 answers
  })
})
