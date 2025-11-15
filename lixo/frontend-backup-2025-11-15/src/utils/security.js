/**
 * Security Utilities
 *
 * Input validation, sanitization, and security helpers
 *
 * Features:
 * - XSS prevention
 * - SQL injection prevention
 * - Input validation
 * - HTML sanitization
 * - URL validation
 * - CSRF token handling
 */

/**
 * Sanitize HTML to prevent XSS attacks
 *
 * @param {string} html - HTML string to sanitize
 * @returns {string} Sanitized HTML
 */
export const sanitizeHTML = (html) => {
  if (typeof html !== "string") return "";

  const temp = document.createElement("div");
  temp.textContent = html;
  return temp.innerHTML;
};

/**
 * Escape HTML special characters
 *
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
export const escapeHTML = (str) => {
  if (typeof str !== "string") return "";

  const htmlEscapeMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
  };

  return str.replace(/[&<>"'/]/g, (char) => htmlEscapeMap[char]);
};

/**
 * Validate email address
 *
 * @param {string} email - Email to validate
 * @returns {boolean} Valid or not
 */
export const isValidEmail = (email) => {
  if (typeof email !== "string") return false;

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email) && email.length <= 254;
};

/**
 * Validate URL
 *
 * @param {string} url - URL to validate
 * @param {Array<string>} allowedProtocols - Allowed protocols (default: http, https)
 * @returns {boolean} Valid or not
 */
export const isValidURL = (url, allowedProtocols = ["http", "https"]) => {
  if (typeof url !== "string") return false;

  try {
    const parsed = new URL(url);
    return allowedProtocols.includes(parsed.protocol.replace(":", ""));
  } catch {
    return false;
  }
};

/**
 * Validate IP address (IPv4)
 *
 * @param {string} ip - IP address to validate
 * @returns {boolean} Valid or not
 */
export const isValidIPv4 = (ip) => {
  if (typeof ip !== "string") return false;

  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
  if (!ipv4Regex.test(ip)) return false;

  const parts = ip.split(".");
  return parts.every((part) => {
    const num = parseInt(part, 10);
    if (isNaN(num)) return false;
    return num >= 0 && num <= 255;
  });
};

/**
 * Validate domain name
 *
 * @param {string} domain - Domain to validate
 * @returns {boolean} Valid or not
 */
export const isValidDomain = (domain) => {
  if (typeof domain !== "string") return false;

  const domainRegex =
    /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  return domainRegex.test(domain) && domain.length <= 253;
};

/**
 * Sanitize input to prevent SQL injection
 *
 * @param {string} input - Input to sanitize
 * @returns {string} Sanitized input
 */
export const sanitizeSQLInput = (input) => {
  if (typeof input !== "string") return "";

  // Remove common SQL injection patterns
  return input
    .replace(/['";]/g, "")
    .replace(/--/g, "")
    .replace(/\/\*/g, "")
    .replace(/\*\//g, "")
    .replace(/xp_/gi, "")
    .replace(/exec/gi, "")
    .replace(/execute/gi, "")
    .replace(/drop/gi, "")
    .replace(/union/gi, "");
};

/**
 * Validate and sanitize CVE ID
 *
 * @param {string} cveId - CVE ID to validate
 * @returns {string|null} Valid CVE ID or null
 */
export const sanitizeCVEId = (cveId) => {
  if (typeof cveId !== "string") return null;

  const cveRegex = /^CVE-\d{4}-\d{4,}$/i;
  const sanitized = cveId.trim().toUpperCase();

  return cveRegex.test(sanitized) ? sanitized : null;
};

/**
 * Validate input length
 *
 * @param {string} input - Input to validate
 * @param {number} min - Minimum length
 * @param {number} max - Maximum length
 * @returns {boolean} Valid or not
 */
export const isValidLength = (input, min = 0, max = Infinity) => {
  if (typeof input !== "string") return false;
  const length = input.trim().length;
  return length >= min && length <= max;
};

/**
 * Sanitize filename
 *
 * @param {string} filename - Filename to sanitize
 * @returns {string} Sanitized filename
 */
export const sanitizeFilename = (filename) => {
  if (typeof filename !== "string") return "";

  return filename
    .replace(/[^a-zA-Z0-9._-]/g, "_")
    .replace(/\.{2,}/g, ".")
    .substring(0, 255);
};

/**
 * ============================================================================
 * CSRF PROTECTION (Enhanced)
 * ============================================================================
 * Governed by: Constituição Vértice v2.5 - ADR-002 (Security Fixes)
 */

const CSRF_TOKEN_KEY = "vrtc_csrf_token";
const CSRF_TOKEN_EXPIRY = "vrtc_csrf_expiry";
const TOKEN_VALIDITY_MS = 60 * 60 * 1000; // 1 hour

/**
 * Generate CSRF token
 *
 * @returns {string} CSRF token
 */
export const generateCSRFToken = () => {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
};

/**
 * Store CSRF token
 *
 * @param {string} token - Token to store
 */
export const storeCSRFToken = (token) => {
  const now = Date.now();
  sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  sessionStorage.setItem(
    CSRF_TOKEN_EXPIRY,
    (now + TOKEN_VALIDITY_MS).toString(),
  );
};

/**
 * Get CSRF token (auto-generates if expired or missing)
 *
 * @returns {string} CSRF token
 */
export const getCSRFToken = () => {
  const now = Date.now();
  const expiry = parseInt(sessionStorage.getItem(CSRF_TOKEN_EXPIRY) || "0", 10);
  if (isNaN(expiry)) {
    // If expiry is corrupted, generate new token
    const token = generateCSRFToken();
    storeCSRFToken(token);
    return token;
  }

  let token = sessionStorage.getItem(CSRF_TOKEN_KEY);

  // Generate new token if expired or missing
  if (!token || now > expiry) {
    token = generateCSRFToken();
    storeCSRFToken(token);
  }

  return token;
};

/**
 * Validate CSRF token
 *
 * @param {string} token - Token to validate
 * @returns {boolean} Valid or not
 */
export const validateCSRFToken = (token) => {
  const storedToken = sessionStorage.getItem(CSRF_TOKEN_KEY);
  const expiry = parseInt(sessionStorage.getItem(CSRF_TOKEN_EXPIRY) || "0", 10);
  if (isNaN(expiry)) return false;
  const now = Date.now();

  return storedToken !== null && storedToken === token && now < expiry;
};

/**
 * Clear CSRF token (call on logout)
 */
export const clearCSRFToken = () => {
  sessionStorage.removeItem(CSRF_TOKEN_KEY);
  sessionStorage.removeItem(CSRF_TOKEN_EXPIRY);
};

/**
 * ============================================================================
 * RATE LIMITING
 * ============================================================================
 * Governed by: Constituição Vértice v2.5 - ADR-002 (Security Fixes)
 */

const rateLimitStore = new Map();

/**
 * Rate limit configuration per endpoint pattern
 */
const RATE_LIMITS = {
  // Strict limits for mutations
  "/api/scans": { maxRequests: 5, windowMs: 60000 }, // 5 req/min
  "/api/attacks": { maxRequests: 3, windowMs: 60000 }, // 3 req/min
  "/offensive": { maxRequests: 10, windowMs: 60000 }, // 10 req/min

  // Moderate limits for queries
  "/api/metrics": { maxRequests: 30, windowMs: 60000 }, // 30 req/min
  "/api/": { maxRequests: 60, windowMs: 60000 }, // 60 req/min (default)
};

/**
 * Gets rate limit config for an endpoint
 */
function getRateLimitConfig(endpoint) {
  for (const [pattern, config] of Object.entries(RATE_LIMITS)) {
    if (endpoint.includes(pattern)) {
      return config;
    }
  }
  return { maxRequests: 60, windowMs: 60000 };
}

/**
 * Custom error for rate limiting
 */
export class RateLimitError extends Error {
  constructor(message, retryAfter) {
    super(message);
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

/**
 * Checks if a request would exceed rate limit
 * @throws {RateLimitError} If rate limit exceeded
 */
export function checkRateLimit(endpoint) {
  const config = getRateLimitConfig(endpoint);
  const now = Date.now();
  const key = endpoint;

  if (!rateLimitStore.has(key)) {
    rateLimitStore.set(key, []);
  }

  const requests = rateLimitStore.get(key);
  const validRequests = requests.filter(
    (timestamp) => now - timestamp < config.windowMs,
  );

  if (validRequests.length >= config.maxRequests) {
    const oldestRequest = Math.min(...validRequests);
    const retryAfter = Math.ceil(
      (oldestRequest + config.windowMs - now) / 1000,
    );

    throw new RateLimitError(
      `Rate limit exceeded for ${endpoint}. Retry after ${retryAfter}s`,
      retryAfter,
    );
  }

  validRequests.push(now);
  rateLimitStore.set(key, validRequests);
}

/**
 * Clears rate limit history (useful for testing)
 */
export function clearRateLimits() {
  rateLimitStore.clear();
}

/**
 * Rate limit key generator (legacy, kept for compatibility)
 */
export const generateRateLimitKey = (action, identifier) => {
  return `ratelimit:${action}:${identifier}`;
};

/**
 * Content Security Policy generator
 *
 * @param {Object} options - CSP options
 * @returns {string} CSP header value
 */
export const generateCSP = (options = {}) => {
  const defaults = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "https:"],
    "font-src": ["'self'", "data:"],
    "connect-src": ["'self'", "ws:", "wss:"],
    "frame-ancestors": ["'none'"],
    "base-uri": ["'self'"],
    "form-action": ["'self'"],
  };

  const csp = { ...defaults, ...options };

  return Object.entries(csp)
    .map(([directive, sources]) => `${directive} ${sources.join(" ")}`)
    .join("; ");
};

/**
 * Security headers configuration
 *
 * @returns {Object} Security headers
 */
export const getSecurityHeaders = () => {
  return {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": generateCSP(),
  };
};

/**
 * Validate JSON input
 *
 * @param {string} json - JSON string
 * @returns {Object|null} Parsed JSON or null
 */
export const safeJSONParse = (json) => {
  if (typeof json !== "string") return null;

  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
};

/**
 * Check if string contains only alphanumeric characters
 *
 * @param {string} str - String to check
 * @returns {boolean} Alphanumeric or not
 */
export const isAlphanumeric = (str) => {
  if (typeof str !== "string") return false;
  return /^[a-zA-Z0-9]+$/.test(str);
};

/**
 * Remove script tags from HTML
 *
 * @param {string} html - HTML string
 * @returns {string} Cleaned HTML
 */
export const removeScriptTags = (html) => {
  if (typeof html !== "string") return "";
  return html.replace(
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    "",
  );
};

/**
 * OWASP Top 10 validation helpers
 */
export const OWASP = {
  /**
   * A1: Injection Prevention
   */
  preventInjection: (input) => {
    return sanitizeSQLInput(escapeHTML(input));
  },

  /**
   * A3: Sensitive Data Exposure Prevention
   */
  maskSensitiveData: (data, visibleChars = 4) => {
    if (typeof data !== "string") return "";
    const length = data.length;
    if (length <= visibleChars) return "*".repeat(length);
    return "*".repeat(length - visibleChars) + data.slice(-visibleChars);
  },

  /**
   * A7: XSS Prevention
   */
  preventXSS: (html) => {
    return removeScriptTags(escapeHTML(html));
  },

  /**
   * A8: Insecure Deserialization Prevention
   */
  safeDeserialize: (json) => {
    return safeJSONParse(json);
  },
};
