/**
 * Vitest Setup File
 *
 * Global test configuration and mocks
 */

// Ensure NODE_ENV is set to test
process.env.NODE_ENV = "test";

import { expect, afterEach, beforeAll, afterAll, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  toReceiveMessage,
  toHaveReceivedMessages,
} from "vitest-websocket-mock";

// Add custom WebSocket matchers
expect.extend({ toReceiveMessage, toHaveReceivedMessages });

// Cleanup after each test
afterEach(async () => {
  cleanup();
  // Wait for any pending promises to resolve
  await new Promise((resolve) => setTimeout(resolve, 0));
});

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Fix jsdom offset properties for virtualized lists
Object.defineProperty(HTMLElement.prototype, "offsetHeight", {
  configurable: true,
  value: 600,
});
Object.defineProperty(HTMLElement.prototype, "offsetWidth", {
  configurable: true,
  value: 800,
});

// WebSocket mock removed - using vitest-websocket-mock for scientific testing
// Note: vitest-websocket-mock provides a real WebSocket protocol mock via mock-socket
// This gives us behavioral testing instead of implementation mocking

// Mock fetch globally
global.fetch = vi.fn();

// Mock logger globally
vi.mock("@/utils/logger", () => ({
  default: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    group: vi.fn(),
    table: vi.fn(),
    setLevel: vi.fn(),
  },
}));

// Mock i18next globally to fix NO_I18NEXT_INSTANCE errors
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key, options) => {
      // Support interpolation for realistic translations
      if (options && typeof options === "object") {
        let result = key;
        Object.keys(options).forEach((optKey) => {
          result = result.replace(`{{${optKey}}}`, options[optKey]);
        });
        return result;
      }
      return key;
    },
    i18n: {
      changeLanguage: vi.fn(),
      language: "en",
      languages: ["en", "pt"],
      exists: vi.fn(() => true),
    },
  }),
  Trans: ({ children, i18nKey }) => children || i18nKey,
  Translation: ({ children }) => children((key) => key),
  I18nextProvider: ({ children }) => children,
  initReactI18next: {
    type: "3rdParty",
    init: vi.fn(),
  },
}));

// Console spy setup (to catch errors in tests)
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    // Filter out React warnings we don't care about in tests
    if (
      typeof args[0] === "string" &&
      args[0].includes("Warning: ReactDOM.render")
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
