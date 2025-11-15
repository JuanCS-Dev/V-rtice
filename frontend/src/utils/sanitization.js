/**
 * Input Sanitization Utilities
 * Boris Cherny Standard - XSS Prevention, HTML Injection Protection
 *
 * Addresses Air Gap #9 - ZERO Input Sanitization
 */

import DOMPurify from 'dompurify';

// ============================================================================
// SANITIZATION CONFIGURATION
// ============================================================================

/**
 * DOMPurify config for plain text (no HTML allowed)
 */
const PLAIN_TEXT_CONFIG = {
  ALLOWED_TAGS: [],
  ALLOWED_ATTR: [],
  KEEP_CONTENT: true,
};

/**
 * DOMPurify config for rich text (limited safe HTML)
 */
const RICH_TEXT_CONFIG = {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
  ALLOWED_ATTR: ['href'],
  ALLOWED_URI_REGEXP: /^https?:\/\//,
};

/**
 * DOMPurify config for complete removal (paranoid mode)
 */
const PARANOID_CONFIG = {
  ALLOWED_TAGS: [],
  ALLOWED_ATTR: [],
  KEEP_CONTENT: false,
};

// ============================================================================
// CORE SANITIZATION FUNCTIONS
// ============================================================================

/**
 * Sanitizes input to plain text - removes ALL HTML/scripts
 * Use this for: search queries, usernames, IPs, emails, etc.
 *
 * @param {string} input - Raw user input
 * @returns {string} - Sanitized plain text
 *
 * @example
 * sanitizePlainText('<script>alert("XSS")</script>Hello')
 * // Returns: 'Hello'
 */
export function sanitizePlainText(input) {
  if (typeof input !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(input, PLAIN_TEXT_CONFIG);
}

/**
 * Sanitizes input for rich text (preserves safe HTML only)
 * Use this for: descriptions, comments where formatting is needed
 *
 * @param {string} input - Raw user input with HTML
 * @returns {string} - Sanitized HTML
 *
 * @example
 * sanitizeRichText('<script>alert("XSS")</script><b>Bold</b>')
 * // Returns: '<b>Bold</b>'
 */
export function sanitizeRichText(input) {
  if (typeof input !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(input, RICH_TEXT_CONFIG);
}

/**
 * Paranoid sanitization - removes everything including content
 * Use this for: extremely sensitive inputs
 *
 * @param {string} input - Raw user input
 * @returns {string} - Completely stripped text
 */
export function sanitizeParanoid(input) {
  if (typeof input !== 'string') {
    return '';
  }

  return DOMPurify.sanitize(input, PARANOID_CONFIG);
}

/**
 * Sanitizes HTML attributes (for dynamic attribute values)
 * Prevents attribute-based XSS
 *
 * @param {string} value - Attribute value
 * @returns {string} - Safe attribute value
 */
export function sanitizeAttribute(value) {
  if (typeof value !== 'string') {
    return '';
  }

  // Remove quotes, angle brackets, and other dangerous characters
  return value
    .replace(/[<>"'`]/g, '')
    .replace(/javascript:/gi, '')
    .replace(/on\w+=/gi, '');
}

/**
 * Sanitizes URL to prevent javascript:, data:, vbscript: schemes
 *
 * @param {string} url - URL to sanitize
 * @returns {string} - Safe URL or empty string
 */
export function sanitizeURL(url) {
  if (typeof url !== 'string') {
    return '';
  }

  const trimmed = url.trim().toLowerCase();

  // Block dangerous schemes
  const dangerousSchemes = ['javascript:', 'data:', 'vbscript:', 'file:'];
  for (const scheme of dangerousSchemes) {
    if (trimmed.startsWith(scheme)) {
      return '';
    }
  }

  // Only allow http(s) and relative URLs
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('/')) {
    return url.trim();
  }

  // Default: block
  return '';
}

/**
 * Sanitizes JSON input before parsing
 * Prevents prototype pollution and injection
 *
 * @param {string} jsonString - JSON string
 * @returns {Object|null} - Parsed object or null if invalid
 */
export function sanitizeJSON(jsonString) {
  if (typeof jsonString !== 'string') {
    return null;
  }

  try {
    const parsed = JSON.parse(jsonString);

    // Prevent __proto__ pollution
    if (parsed && typeof parsed === 'object') {
      delete parsed.__proto__;
      delete parsed.constructor;
      delete parsed.prototype;
    }

    return parsed;
  } catch (error) {
    return null;
  }
}

/**
 * Sanitizes file names to prevent path traversal
 *
 * @param {string} filename - Original filename
 * @returns {string} - Safe filename
 */
export function sanitizeFilename(filename) {
  if (typeof filename !== 'string') {
    return 'file';
  }

  // Remove path traversal attempts
  let safe = filename
    .replace(/\.\./g, '')
    .replace(/[\/\\]/g, '')
    .replace(/[<>:"|?*\x00-\x1f]/g, '');

  // Ensure not empty
  if (!safe.trim()) {
    return 'file';
  }

  return safe;
}

/**
 * Sanitizes command-line arguments (extremely strict)
 * Use for: nmap args, shell commands, etc.
 *
 * @param {string} args - Command arguments
 * @returns {string} - Sanitized args
 */
export function sanitizeCommandArgs(args) {
  if (typeof args !== 'string') {
    return '';
  }

  // Only allow alphanumeric, spaces, hyphens, dots, commas, colons, slashes
  return args.replace(/[^\w\s\-\.,:/]/g, '');
}

/**
 * Batch sanitizes an object's string values
 *
 * @param {Object} obj - Object with string values
 * @param {Function} sanitizer - Sanitization function to use (default: sanitizePlainText)
 * @returns {Object} - Object with sanitized values
 */
export function sanitizeObject(obj, sanitizer = sanitizePlainText) {
  if (!obj || typeof obj !== 'object') {
    return {};
  }

  const sanitized = {};

  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'string') {
      sanitized[key] = sanitizer(value);
    } else if (Array.isArray(value)) {
      sanitized[key] = value.map(item =>
        typeof item === 'string' ? sanitizer(item) : item
      );
    } else if (value && typeof value === 'object') {
      sanitized[key] = sanitizeObject(value, sanitizer);
    } else {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

// ============================================================================
// SPECIALIZED SANITIZERS
// ============================================================================

/**
 * Sanitizes IP address input
 */
export function sanitizeIP(ip) {
  if (typeof ip !== 'string') {
    return '';
  }

  // Only allow IP-valid characters
  return ip.trim().replace(/[^0-9a-fA-F.:]/g, '');
}

/**
 * Sanitizes email input
 */
export function sanitizeEmail(email) {
  if (typeof email !== 'string') {
    return '';
  }

  // Remove dangerous characters, keep email-valid ones
  return email.trim().toLowerCase().replace(/[^a-z0-9@._\-+]/g, '');
}

/**
 * Sanitizes port input
 */
export function sanitizePort(port) {
  if (typeof port !== 'string') {
    return '';
  }

  // Only numbers, commas, hyphens
  return port.trim().replace(/[^0-9,\-]/g, '');
}

/**
 * Sanitizes domain input
 */
export function sanitizeDomain(domain) {
  if (typeof domain !== 'string') {
    return '';
  }

  // Only domain-valid characters
  return domain.trim().toLowerCase().replace(/[^a-z0-9.\-]/g, '');
}

/**
 * Sanitizes search query
 */
export function sanitizeSearchQuery(query) {
  if (typeof query !== 'string') {
    return '';
  }

  // Remove script tags and dangerous patterns
  let safe = sanitizePlainText(query);

  // Limit length
  if (safe.length > 1000) {
    safe = safe.substring(0, 1000);
  }

  return safe.trim();
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Core
  sanitizePlainText,
  sanitizeRichText,
  sanitizeParanoid,
  sanitizeAttribute,
  sanitizeURL,
  sanitizeJSON,
  sanitizeFilename,
  sanitizeCommandArgs,
  sanitizeObject,

  // Specialized
  sanitizeIP,
  sanitizeEmail,
  sanitizePort,
  sanitizeDomain,
  sanitizeSearchQuery,
};
