import { test, expect } from '@playwright/test'

test.describe('ChatWidget E2E', () => {
  test('sends messages and shows back-and-forth with thread_id', async ({ page }) => {
    // Intercept backend ask endpoint
    await page.route('**/api/ask**', async (route) => {
      const url = new URL(route.request().url())
      const query = url.searchParams
      
      // Basic param checks
      expect(query.get('query')).toBeTruthy()
      expect(query.get('lang')).toBeTruthy()
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

    // Wait for the page to load and chat to be ready
    await page.waitForLoadState('networkidle')

    // Switch to English for stable strings (if language selector exists)
    const languageSelector = page.getByLabel(/Idioma|Language/i)
    if (await languageSelector.isVisible({ timeout: 2000 }).catch(() => false)) {
      await languageSelector.selectOption('en')
    }

    // First turn - send a message
    const messageInput = page.getByPlaceholder(/Ask about local resources|Pregunta sobre recursos locales/i)
    await messageInput.fill('Hello')
    
    const sendButton = page.getByRole('button', { name: /Send|Enviar/i })
    const requestPromise = page.waitForRequest('**/api/ask**')
    await sendButton.click()
    await requestPromise

    // Wait for and verify the response
    await expect(page.getByText('Hi there!')).toBeVisible({ timeout: 5000 })

    // Second turn - send another message
    await messageInput.fill('How are you?')
    const requestPromise2 = page.waitForRequest('**/api/ask**')
    await sendButton.click()
    await requestPromise2

    // Verify both assistant messages are visible
    await expect(page.getByText('Hi there!').first()).toBeVisible()
    
    // Check that multiple assistant messages exist (welcome + 2 answers)
    // Use a more specific selector to target only message bubbles, not containers
    const assistantMessages = page.locator('.rounded-lg.bg-muted')
    await expect(assistantMessages).toHaveCount(3, { timeout: 5000 })
  })
})
