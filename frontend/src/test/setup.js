import { expect, afterEach } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'
import { cleanup } from '@testing-library/react'
expect.extend(matchers)

// Ensure DOM is cleaned between tests to avoid duplicate queries
afterEach(() => {
	cleanup()
})

// Mock ResizeObserver used by Radix UI components
class MockResizeObserver {
	observe() {}
	unobserve() {}
	disconnect() {}
}
// eslint-disable-next-line no-undef
global.ResizeObserver = global.ResizeObserver || MockResizeObserver
