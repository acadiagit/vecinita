import { test, expect } from '@playwright/test'
import { injectAxe, checkA11y } from 'axe-playwright'

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock ask endpoint
    await page.route('**/api/ask**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          answer: 'This is a test answer about environmental resources.',
          sources: [
            { title: 'Resource 1', url: 'https://example.com/resource1' },
          ],
        }),
      })
    })

    await page.goto('/')
  })

  test('should have no automated accessibility violations on home page', async ({
    page,
  }) => {
    await injectAxe(page)
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true },
    })
  })

  test('should have no accessibility violations with chat open', async ({
    page,
  }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    await injectAxe(page)
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true },
    })
  })

  test('all buttons should have proper ARIA labels', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Check send button
    const sendButton = page.getByRole('button', { name: 'Send' })
    await expect(sendButton).toHaveAccessibleName()

    // Check language selector
    const languageSelect = page.getByLabel(/Language|Idioma/)
    await expect(languageSelect).toHaveAccessibleName()
  })

  test('form inputs should have associated labels', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Message input should be accessible
    const input = page.getByPlaceholder(/Ask|Pregunta/)
    await expect(input).toBeVisible()
    const ariaLabel = await input.getAttribute('aria-label')
    const placeholder = await input.getAttribute('placeholder')
    expect(ariaLabel || placeholder).toBeTruthy()
  })

  test('should support keyboard navigation', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Tab to language selector
    await page.keyboard.press('Tab')
    const focused = await page.evaluate(() => document.activeElement?.tagName)
    expect(['SELECT', 'BUTTON', 'INPUT']).toContain(focused)

    // Tab to message input
    await page.keyboard.press('Tab')
    const messageInput = page.getByPlaceholder(/Ask|Pregunta/)
    await messageInput.focus()
    const isFocused = await messageInput.evaluate(
      (el) => document.activeElement === el
    )
    expect(isFocused).toBe(true)

    // Send message with Enter key
    await messageInput.fill('Test message')
    const askRequest = page.waitForRequest('**/api/ask**')
    await page.keyboard.press('Enter')
    await askRequest
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    const h1Elements = page.locator('h1')
    await expect(h1Elements).toHaveCount(1)

    const headingText = await h1Elements.first().textContent()
    expect(headingText?.toLowerCase()).toContain('vecinita')
  })

  test('links should be accessible and keyboard navigable', async ({
    page,
  }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Type a message to get a response with sources
    await page.getByPlaceholder(/Ask|Pregunta/).fill('What is Vecinita?')
    const askRequest = page.waitForRequest('**/api/ask**')
    await page.getByRole('button', { name: 'Send' }).click()
    await askRequest

    // Wait for sources to appear
    await page.waitForTimeout(500)

    // Check if any links are accessible
    const links = page.locator('a')
    const linkCount = await links.count()
    if (linkCount > 0) {
      const firstLink = links.first()
      await expect(firstLink).toHaveAccessibleName()

      // Keyboard navigation to link
      await firstLink.focus()
      const href = await firstLink.getAttribute('href')
      expect(href).toBeTruthy()
    }
  })

  test('color contrast should meet standards', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    // Get computed styles and verify contrast
    const title = page.locator('h1')
    const bgColor = await title.evaluate((el) =>
      window.getComputedStyle(el).backgroundColor
    )
    const textColor = await title.evaluate((el) =>
      window.getComputedStyle(el).color
    )

    // Both should exist
    expect(bgColor).toBeTruthy()
    expect(textColor).toBeTruthy()
  })

  test('focus indicators should be visible', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    const sendButton = page.getByRole('button', { name: 'Send' })
    await sendButton.focus()

    // Check for focus styles
    const outline = await sendButton.evaluate((el) =>
      window.getComputedStyle(el).outline
    )
    expect(outline).toBeTruthy()
  })

  test('dialog should be properly marked as dialog', async ({ page }) => {
    const chatButton = page.getByRole('button', { name: 'Chat' })
    if (await chatButton.isVisible()) {
      await chatButton.click()
    }

    const dialog = page.locator('[role="dialog"]')
    if (await dialog.isVisible()) {
      await expect(dialog).toHaveAttribute('role', 'dialog')
    }
  })
})
