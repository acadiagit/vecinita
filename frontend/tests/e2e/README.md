# Frontend Testing Guide

This document describes the E2E testing strategy for the Vecinita frontend.

## Test Files

### 1. **chat.spec.ts** - Core Functionality

Tests the basic chat widget functionality including:

- Message sending and receiving
- Thread ID persistence
- Multi-turn conversations
- Provider and model selection

Run with:

```bash
npm run test:e2e -- chat.spec.ts
```

### 2. **accessibility.spec.ts** - Accessibility Testing

Comprehensive accessibility tests using axe-core through axe-playwright:

#### Tests Included

- **WCAG Compliance**: Automated accessibility violation detection
- **ARIA Labels**: Verifies all buttons and form controls have accessible names
- **Keyboard Navigation**: Tab order and Enter key functionality
- **Heading Hierarchy**: Proper semantic HTML structure
- **Link Accessibility**: Links have accessible names and are keyboard navigable
- **Color Contrast**: Ensures text meets contrast standards
- **Focus Indicators**: Visible focus states for keyboard users
- **Dialog Semantics**: Proper ARIA roles for dialog elements

#### Running Accessibility Tests

```bash
npm run test:e2e -- accessibility.spec.ts
npm run test:e2e -- accessibility.spec.ts --headed  # View browser
```

#### Key Accessibility Standards Met

- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader compatibility
- Color contrast (4.5:1 for text)
- Touch target sizing (44x44px minimum on mobile)

### 3. **responsive.spec.ts** - Responsive Design Testing

Tests layout and usability across multiple device form factors:

#### Device Configurations Tested

**Mobile:**

- iPhone 12 (390x844)
- Pixel 5 (393x851)

**Tablets:**

- iPad Pro (1024x1366)
- iPad Mini (768x1024)

**Desktop:**

- 1920x1080 (Full HD)
- 1366x768 (Common laptop)
- 1024x768 (Small desktop)

#### Tests Include

- **Header Rendering**: Verifies UI doesn't get cut off
- **Widget Visibility**: Chat components accessible on all screen sizes
- **Text Input**: Form inputs usable and properly sized
- **Touch Targets**: Button sizes meet 44x44px minimum on mobile
- **No Horizontal Overflow**: Content doesn't exceed viewport width
- **Form Controls**: Selects and inputs work across devices
- **Typography**: Font sizes readable on all devices
- **Window Resizing**: UI adapts gracefully when viewport changes
- **Orientation Changes**: Landscape/portrait switching handled correctly

#### Running Responsive Tests

```bash
npm run test:e2e -- responsive.spec.ts
npm run test:e2e -- responsive.spec.ts --headed  # View browser
npm run test:e2e -- responsive.spec.ts -g "Mobile"  # Test only mobile
npm run test:e2e -- responsive.spec.ts -g "Tablet"  # Test only tablets
npm run test:e2e -- responsive.spec.ts -g "Desktop" # Test only desktop
```

## Running All Tests

```bash
# Run all E2E tests once
npm run test:e2e

# Run with headed browser (see what's happening)
npm run test:e2e -- --headed

# Run with UI mode (interactive)
npm run test:e2e -- --ui

# Run specific test file
npm run test:e2e -- accessibility.spec.ts

# Run tests matching a pattern
npm run test:e2e -- -g "keyboard"

# Debug mode
npm run test:e2e -- --debug

# Generate HTML report
npm run test:e2e
# Then view: npx playwright show-report
```

## Browser Coverage

The Playwright config tests across multiple browsers and mobile environments:

- **Chromium** (Desktop)
- **Firefox** (Desktop)
- **WebKit** (Desktop Safari)
- **Mobile Chrome** (Pixel 5)
- **Mobile Safari** (iPhone 12)

Run tests on specific browser:

```bash
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project="Mobile Safari"
```

## CI/CD Integration

The tests are configured for CI environments:

- Retries enabled (2x on failure)
- Headless mode by default
- Single worker to prevent flakiness
- HTML and JSON reports generated
- Screenshots captured on failures
- Traces recorded on first retry for debugging

## Debugging Failed Tests

### View HTML Report

```bash
npm run test:e2e
npx playwright show-report
```

### Run Single Test in Debug Mode

```bash
npm run test:e2e -- accessibility.spec.ts -g "keyboard navigation" --debug
```

### Generate Trace for Debugging

Tests automatically capture traces on failures (see `test-results/` directory)

### Check Screenshots

Failed tests automatically capture screenshots in `test-results/`

## Accessibility Checklist

Before shipping features, ensure:

- [ ] All new buttons/controls have accessible names (ARIA labels or visible text)
- [ ] Form inputs have associated labels
- [ ] Color is not the only indicator of state (use text labels too)
- [ ] Focus indicators are visible and clear
- [ ] Keyboard navigation works end-to-end
- [ ] Headings follow proper semantic hierarchy
- [ ] Links are underlined or otherwise distinguishable
- [ ] Touch targets are at least 44x44 on mobile
- [ ] Test passes: `npm run test:e2e -- accessibility.spec.ts`

## Responsive Design Checklist

Before shipping UI changes, ensure:

- [ ] Layout adapts to mobile (375px width)
- [ ] Layout adapts to tablet (768px width)
- [ ] Layout adapts to desktop (1920px width)
- [ ] No horizontal scrolling on any viewport
- [ ] Text remains readable on all devices
- [ ] Buttons are tap-friendly on touch devices
- [ ] Test passes: `npm run test:e2e -- responsive.spec.ts`

## Installation

To install test dependencies:

```bash
npm install
```

This will install:

- `@playwright/test` - E2E testing framework
- `axe-playwright` - Automated accessibility testing

## Troubleshooting

### Tests timeout

Increase timeout in `playwright.config.ts`:

```typescript
timeout: 60 * 1000  // 60 seconds
```

### Can't connect to localhost:5173

Ensure frontend dev server is running:

```bash
npm run dev
```

### axe-playwright not found

Install dependencies:

```bash
npm install
```

### Tests fail with "page is closed"

Add delays for async operations:

```typescript
await page.waitForTimeout(500)  // Explicit wait
await page.waitForSelector(...)  // Wait for element
await page.waitForRequest(...)   // Wait for network
```

## Best Practices

1. **Use semantic selectors** over class names:

   ```typescript
   // Good
   page.getByRole('button', { name: 'Send' })
   
   // Avoid
   page.locator('.send-btn')
   ```

2. **Test user behavior** not implementation:

   ```typescript
   // Good - tests what user does
   await page.getByPlaceholder('Ask...').fill('Hello')
   await page.keyboard.press('Enter')
   
   // Avoid - tests internal state
   expect(page.locator('.state-variable')).toContain('value')
   ```

3. **Mock external APIs** consistently:

   ```typescript
   await page.route('**/api/ask**', async (route) => {
     await route.fulfill({ status: 200, body: '...' })
   })
   ```

4. **Use descriptive test names**:

   ```typescript
   // Good
   test('should handle keyboard Enter key to send message')
   
   // Avoid
   test('test form')
   ```

## Contributing

When adding new features:

1. Add corresponding accessibility tests in `accessibility.spec.ts`
2. Add responsive design tests in `responsive.spec.ts`
3. Ensure all tests pass: `npm run test:e2e`
4. Include tests in PR description

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [axe-playwright Guide](https://github.com/abhinaba-ghosh/axe-playwright)
- [WCAG 2.1 Standards](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Accessibility Tips](https://webaim.org/)
- [Responsive Design Testing](https://web.dev/responsive-web-design-basics/)
