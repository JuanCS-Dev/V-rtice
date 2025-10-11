/**
 * Accessibility Utilities
 *
 * WCAG 2.1 AA Compliance helpers
 *
 * Features:
 * - Screen reader announcements
 * - Focus management
 * - Color contrast validation
 * - ARIA helpers
 */

/**
 * Screen Reader Announcer
 * Creates live region for screen reader announcements
 */
class ScreenReaderAnnouncer {
  constructor() {
    this.liveRegion = null;
    this.init();
  }

  init() {
    // Check if already exists
    if (document.getElementById('sr-announcer')) return;

    // Create live region
    this.liveRegion = document.createElement('div');
    this.liveRegion.id = 'sr-announcer';
    this.liveRegion.setAttribute('role', 'status');
    this.liveRegion.setAttribute('aria-live', 'polite');
    this.liveRegion.setAttribute('aria-atomic', 'true');
    this.liveRegion.className = 'sr-only';

    // Add styles (visually hidden but accessible)
    this.liveRegion.style.cssText = `
      position: absolute;
      left: -10000px;
      width: 1px;
      height: 1px;
      overflow: hidden;
    `;

    document.body.appendChild(this.liveRegion);
  }

  /**
   * Announce message to screen readers
   * @param {string} message - Message to announce
   * @param {string} priority - 'polite' | 'assertive'
   */
  announce(message, priority = 'polite') {
    if (!this.liveRegion) this.init();

    this.liveRegion.setAttribute('aria-live', priority);

    // Clear and set message (force re-announcement)
    this.liveRegion.textContent = '';
    setTimeout(() => {
      this.liveRegion.textContent = message;
    }, 100);

    // Auto-clear after 5 seconds
    setTimeout(() => {
      this.liveRegion.textContent = '';
    }, 5000);
  }

  /**
   * Announce error (assertive)
   */
  announceError(message) {
    this.announce(`Error: ${message}`, 'assertive');
  }

  /**
   * Announce success (polite)
   */
  announceSuccess(message) {
    this.announce(`Success: ${message}`, 'polite');
  }
}

// Singleton instance
export const announcer = new ScreenReaderAnnouncer();

/**
 * Focus Management
 */

/**
 * Move focus to element
 * @param {HTMLElement|string} element - Element or selector
 * @param {boolean} preventScroll - Prevent scroll on focus
 */
export const focusElement = (element, preventScroll = false) => {
  const el = typeof element === 'string'
    ? document.querySelector(element)
    : element;

  if (el && typeof el.focus === 'function') {
    el.focus({ preventScroll });
  }
};

/**
 * Get first focusable element in container
 */
export const getFirstFocusable = (container) => {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(',');

  const el = typeof container === 'string'
    ? document.querySelector(container)
    : container;

  if (!el) return null;

  return el.querySelector(focusableSelectors);
};

/**
 * Trap focus within container (manual version)
 */
export const trapFocus = (container, event) => {
  if (event.key !== 'Tab') return;

  const focusableElements = container.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (event.shiftKey && document.activeElement === firstElement) {
    event.preventDefault();
    lastElement.focus();
  } else if (!event.shiftKey && document.activeElement === lastElement) {
    event.preventDefault();
    firstElement.focus();
  }
};

/**
 * Color Contrast Validation
 * WCAG AA requires 4.5:1 for normal text, 3:1 for large text
 */

/**
 * Calculate relative luminance
 * https://www.w3.org/TR/WCAG20/#relativeluminancedef
 */
const getRelativeLuminance = (rgb) => {
  const [r, g, b] = rgb.map(val => {
    val = val / 255;
    return val <= 0.03928
      ? val / 12.92
      : Math.pow((val + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

/**
 * Parse color string to RGB
 */
const parseColor = (color) => {
  // Create temporary element
  const temp = document.createElement('div');
  temp.style.color = color;
  document.body.appendChild(temp);

  const computed = window.getComputedStyle(temp).color;
  document.body.removeChild(temp);

  const match = computed.match(/\d+/g);
  return match ? match.map(Number) : [0, 0, 0];
};

/**
 * Calculate contrast ratio between two colors
 * @param {string} color1 - Foreground color
 * @param {string} color2 - Background color
 * @returns {number} Contrast ratio
 */
export const getContrastRatio = (color1, color2) => {
  const lum1 = getRelativeLuminance(parseColor(color1));
  const lum2 = getRelativeLuminance(parseColor(color2));

  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);

  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Check if contrast meets WCAG AA standard
 * @param {string} foreground - Foreground color
 * @param {string} background - Background color
 * @param {boolean} isLargeText - Text is >= 18pt or >= 14pt bold
 * @returns {boolean}
 */
export const meetsContrastAA = (foreground, background, isLargeText = false) => {
  const ratio = getContrastRatio(foreground, background);
  const requiredRatio = isLargeText ? 3 : 4.5;
  return ratio >= requiredRatio;
};

/**
 * Check if contrast meets WCAG AAA standard
 */
export const meetsContrastAAA = (foreground, background, isLargeText = false) => {
  const ratio = getContrastRatio(foreground, background);
  const requiredRatio = isLargeText ? 4.5 : 7;
  return ratio >= requiredRatio;
};

/**
 * ARIA Helpers
 */

/**
 * Generate unique ID for ARIA relationships
 */
let idCounter = 0;
export const generateId = (prefix = 'a11y') => {
  return `${prefix}-${++idCounter}-${Date.now()}`;
};

/**
 * Get ARIA label from element
 */
export const getAriaLabel = (element) => {
  return (
    element.getAttribute('aria-label') ||
    element.getAttribute('aria-labelledby') ||
    element.textContent?.trim() ||
    element.getAttribute('title') ||
    ''
  );
};

/**
 * Check if element is hidden from screen readers
 */
export const isAriaHidden = (element) => {
  if (element.getAttribute('aria-hidden') === 'true') return true;
  if (element.hasAttribute('hidden')) return true;
  if (element.style.display === 'none') return true;
  if (element.style.visibility === 'hidden') return true;

  // Check parents
  let parent = element.parentElement;
  while (parent) {
    if (parent.getAttribute('aria-hidden') === 'true') return true;
    if (parent.hasAttribute('hidden')) return true;
    parent = parent.parentElement;
  }

  return false;
};

/**
 * Keyboard Navigation Helpers
 */

/**
 * Check if element is keyboard focusable
 */
export const isFocusable = (element) => {
  if (element.disabled || element.hasAttribute('disabled')) return false;
  if (element.tabIndex < 0) return false;

  const tagName = element.tagName.toLowerCase();
  const focusableTags = ['a', 'button', 'input', 'select', 'textarea'];

  return (
    focusableTags.includes(tagName) ||
    element.hasAttribute('tabindex') ||
    element.hasAttribute('contenteditable')
  );
};

/**
 * Get all focusable elements in container
 */
export const getAllFocusable = (container = document) => {
  const selector = [
    'a[href]',
    'area[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable]'
  ].join(',');

  return Array.from(container.querySelectorAll(selector)).filter(
    el => !isAriaHidden(el)
  );
};

/**
 * Skip to main content (skip links)
 */
export const skipToMain = () => {
  const main = document.querySelector('main, [role="main"], #main-content');
  if (main) {
    main.setAttribute('tabindex', '-1');
    main.focus();
    main.removeAttribute('tabindex');
  }
};

/**
 * Accessibility Validator
 */
export const validateAccessibility = {
  /**
   * Check if page has skip link
   */
  hasSkipLink: () => {
    const skipLink = document.querySelector('a[href^="#"]:first-of-type');
    return skipLink && skipLink.textContent.toLowerCase().includes('skip');
  },

  /**
   * Check if images have alt text
   */
  imagesHaveAlt: () => {
    const images = document.querySelectorAll('img');
    const missing = Array.from(images).filter(img => !img.hasAttribute('alt'));
    return {
      pass: missing.length === 0,
      missing: missing.length,
      total: images.length
    };
  },

  /**
   * Check if form inputs have labels
   */
  inputsHaveLabels: () => {
    const inputs = document.querySelectorAll('input, select, textarea');
    const missing = Array.from(inputs).filter(input => {
      const id = input.id;
      if (!id) return true;

      const label = document.querySelector(`label[for="${id}"]`);
      const ariaLabel = input.getAttribute('aria-label');
      const ariaLabelledBy = input.getAttribute('aria-labelledby');

      return !label && !ariaLabel && !ariaLabelledBy;
    });

    return {
      pass: missing.length === 0,
      missing: missing.length,
      total: inputs.length
    };
  },

  /**
   * Check if page has proper heading structure
   */
  hasProperHeadings: () => {
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    const levels = Array.from(headings).map(h => parseInt(h.tagName[1]));

    const hasH1 = levels.includes(1);
    const h1Count = levels.filter(l => l === 1).length;
    const skipsLevels = levels.some((level, i) => {
      if (i === 0) return false;
      return level - levels[i - 1] > 1;
    });

    return {
      pass: hasH1 && h1Count === 1 && !skipsLevels,
      hasH1,
      h1Count,
      skipsLevels
    };
  },

  /**
   * Run all validations
   */
  runAll: () => {
    return {
      skipLink: validateAccessibility.hasSkipLink(),
      images: validateAccessibility.imagesHaveAlt(),
      inputs: validateAccessibility.inputsHaveLabels(),
      headings: validateAccessibility.hasProperHeadings()
    };
  }
};

export default {
  announcer,
  focusElement,
  getFirstFocusable,
  trapFocus,
  getContrastRatio,
  meetsContrastAA,
  meetsContrastAAA,
  generateId,
  getAriaLabel,
  isAriaHidden,
  isFocusable,
  getAllFocusable,
  skipToMain,
  validateAccessibility
};
