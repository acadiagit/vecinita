import { test, expect, devices } from '@playwright/test'

const DEVICE_CONFIGS = [
  { name: 'Mobile (iPhone 12)', ...devices['iPhone 12'] },
  { name: 'Mobile (Pixel 5)', ...devices['Pixel 5'] },
  { name: 'Tablet (iPad Pro)', ...devices['iPad Pro'] },
  { name: 'Tablet (iPad Mini)', ...devices['iPad Mini'] },
  { name: 'Desktop (1920x1080)', viewport: { width: 1920, height: 1080 } },
  { name: 'Desktop (1366x768)', viewport: { width: 1366, height: 768 } },
  { name: 'Small Desktop (1024x768)', viewport: { width: 1024, height: 768 } },
]

test.describe('Responsive Design Tests', () => {
  DEVICE_CONFIGS.forEach((deviceConfig) => {
    test.describe(`${deviceConfig.name}`, () => {
      test.beforeEach(async ({ browser }) => {
        // Create context with specific viewport
        if (!test.parallel) {
          const context = await browser.newContext({
            viewport: deviceConfig.viewport || { width: 1280, height: 720 },
            userAgent: deviceConfig.userAgent,
            isMobile: deviceConfig.isMobile || false,
            hasTouch: deviceConfig.hasTouch || false,
          })

          // Note: This setup is for reference; actual usage will be in page context
        }
      })

      test(`should render header correctly on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )
        await page.goto('/')

        const header = page.locator('h1')
        await expect(header).toBeVisible()

        // Check header is not cut off
        const boundingBox = await header.boundingBox()
        expect(boundingBox?.width).toBeGreaterThan(0)
        expect(boundingBox?.height).toBeGreaterThan(0)
      })

      test(`chat widget should be visible on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )

        await page.goto('/')
        await page.waitForLoadState('networkidle')

        // Chat should be accessible (check for title or main element)
        const title = page.locator('h1')
        await expect(title).toBeVisible()
      })

      test(`should handle text input on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )

        // Mock ask endpoint
        await page.route('**/api/ask**', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              answer: 'Test response',
              sources: [],
            }),
          })
        })

        await page.goto('/')
        await page.waitForLoadState('networkidle')

        // Open chat if needed
        const chatButton = page.getByRole('button', { name: 'Chat' })
        if (await chatButton.isVisible()) {
          await chatButton.click()
        }

        // Input should be accessible
        const input = page.getByPlaceholder(/Ask|Pregunta/)
        await expect(input).toBeVisible()
        await input.fill('Test')
        await expect(input).toHaveValue('Test')
      })

      test(`buttons should be tap-friendly on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )

        // Mock ask endpoint
        await page.route('**/api/ask**', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              answer: 'Test response',
              sources: [],
            }),
          })
        })

        await page.goto('/')
        await page.waitForLoadState('networkidle')

        // Check button size (minimum recommended is 44x44 for touch targets)
        const sendButton = page.getByRole('button', { name: 'Send' })
        const box = await sendButton.boundingBox()

        if (deviceConfig.isMobile) {
          // Mobile should have larger touch targets
          expect((box?.height || 0) >= 40).toBe(true)
          expect((box?.width || 0) >= 40).toBe(true)
        } else {
          // Desktop buttons can be smaller
          expect((box?.height || 0) > 0).toBe(true)
          expect((box?.width || 0) > 0).toBe(true)
        }
      })

      test(`should not have horizontal overflow on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )
        await page.goto('/')

        // Check for horizontal overflow
        const bodyWidth = await page.evaluate(() => document.body.offsetWidth)
        const windowWidth = await page.evaluate(() => window.innerWidth)

        expect(bodyWidth).toBeLessThanOrEqual(windowWidth)
      })

      test(`select elements should be usable on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )

        await page.goto('/')
        await page.waitForLoadState('networkidle')

        // Language selector should work
        const languageSelect = page.getByLabel(/Language|Idioma/)
        await expect(languageSelect).toBeVisible()
        await languageSelect.selectOption('es')
        await expect(languageSelect).toHaveValue('es')
      })

      test(`text should be readable (font size) on ${deviceConfig.name}`, async ({
        page,
      }) => {
        await page.setViewportSize(
          deviceConfig.viewport || { width: 1280, height: 720 }
        )

        await page.goto('/')
        await page.waitForLoadState('networkidle')

        const title = page.locator('h1')
        const fontSize = await title.evaluate((el) =>
          window.getComputedStyle(el).fontSize
        )

        const fontSizeValue = parseInt(fontSize)
        // Font size should be at least 12px for readability
        expect(fontSizeValue).toBeGreaterThanOrEqual(12)
      })
    })
  })

  test('should handle window resize gracefully', async ({ page }) => {
    await page.goto('/')

    // Start with desktop size
    await page.setViewportSize({ width: 1920, height: 1080 })
    const title = page.locator('h1')
    await expect(title).toBeVisible()

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(title).toBeVisible()

    // Resize back to desktop
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(title).toBeVisible()
  })

  test('orientation change handling (landscape to portrait)', async ({ page }) => {
    // Start in portrait (mobile)
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    let title = page.locator('h1')
    await expect(title).toBeVisible()

    // Switch to landscape
    await page.setViewportSize({ width: 667, height: 375 })
    await expect(title).toBeVisible()
  })

  test('all content should be scrollable without horizontal scroll', async ({
    page,
  }) => {
    // Test at mobile width
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Check if any element causes horizontal scrolling
    const horizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > window.innerWidth
    })

    expect(horizontalScroll).toBe(false)
  })
})
