/**
 * Security Configuration
 *
 * Centralized security settings for the application
 */

/**
 * Content Security Policy Configuration
 *
 * Adjust these values based on your needs
 */
export const CSP_CONFIG = {
  // Allow scripts from self and inline (required for Vite dev)
  'script-src': [
    "'self'",
    process.env.NODE_ENV === 'development' ? "'unsafe-inline'" : "",
    process.env.NODE_ENV === 'development' ? "'unsafe-eval'" : ""
  ].filter(Boolean),

  // Allow styles from self and inline
  'style-src': [
    "'self'",
    "'unsafe-inline'", // Required for CSS-in-JS
    'https://fonts.googleapis.com'
  ],

  // Allow images from multiple sources
  'img-src': [
    "'self'",
    'data:',
    'blob:',
    'https:',
    '*.tile.openstreetmap.org' // Leaflet maps
  ],

  // Allow fonts
  'font-src': [
    "'self'",
    'data:',
    'https://fonts.gstatic.com'
  ],

  // Allow connections to APIs and WebSockets
  'connect-src': [
    "'self'",
    'http://localhost:*',  // Development
    'ws://localhost:*',    // WebSocket development
    'wss://localhost:*',
    'https://api.gemini.com', // Gemini API (if needed)
    process.env.VITE_API_URL || ''
  ].filter(Boolean),

  // Default source
  'default-src': ["'self'"],

  // Frame ancestors (prevent clickjacking)
  'frame-ancestors': ["'none'"],

  // Base URI
  'base-uri': ["'self'"],

  // Form actions
  'form-action': ["'self'"],

  // Object sources (Flash, Java, etc.)
  'object-src': ["'none'"],

  // Media sources
  'media-src': ["'self'"],

  // Worker sources
  'worker-src': ["'self'", 'blob:'],

  // Manifest sources
  'manifest-src': ["'self'"]
};

/**
 * Rate Limiting Configuration
 *
 * Limits for different types of actions
 */
export const RATE_LIMITS = {
  // API calls
  API_CALL: {
    maxRequests: 60,
    windowMs: 60000 // 60 requests per minute
  },

  // Authentication
  LOGIN: {
    maxRequests: 5,
    windowMs: 300000 // 5 attempts per 5 minutes
  },

  // Search operations
  SEARCH: {
    maxRequests: 30,
    windowMs: 60000 // 30 searches per minute
  },

  // File uploads
  UPLOAD: {
    maxRequests: 10,
    windowMs: 600000 // 10 uploads per 10 minutes
  },

  // Maximus AI queries
  AI_QUERY: {
    maxRequests: 20,
    windowMs: 60000 // 20 queries per minute
  },

  // WebSocket connections
  WEBSOCKET: {
    maxRequests: 10,
    windowMs: 60000 // 10 connections per minute
  }
};

/**
 * Input Validation Rules
 *
 * Validation constraints for different input types
 */
export const VALIDATION_RULES = {
  // CVE ID
  CVE_ID: {
    pattern: /^CVE-\d{4}-\d{4,}$/i,
    maxLength: 20
  },

  // IP Address
  IP_ADDRESS: {
    pattern: /^(\d{1,3}\.){3}\d{1,3}$/,
    maxLength: 15
  },

  // Domain
  DOMAIN: {
    pattern: /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/,
    maxLength: 253
  },

  // Email
  EMAIL: {
    pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    maxLength: 254
  },

  // Username
  USERNAME: {
    pattern: /^[a-zA-Z0-9_-]{3,32}$/,
    minLength: 3,
    maxLength: 32
  },

  // Search query
  SEARCH_QUERY: {
    minLength: 2,
    maxLength: 500
  },

  // File name
  FILENAME: {
    pattern: /^[a-zA-Z0-9._-]+$/,
    maxLength: 255
  }
};

/**
 * Security Headers
 *
 * Headers to be sent with all requests
 */
export const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': [
    'geolocation=()',
    'microphone=()',
    'camera=()',
    'payment=()',
    'usb=()'
  ].join(', ')
};

/**
 * CORS Configuration
 *
 * Allowed origins for CORS
 */
export const CORS_CONFIG = {
  allowedOrigins: [
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:3000',
    process.env.VITE_APP_URL
  ].filter(Boolean),

  allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],

  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-CSRF-Token',
    'X-Requested-With'
  ],

  credentials: true,
  maxAge: 86400 // 24 hours
};

/**
 * Session Configuration
 */
export const SESSION_CONFIG = {
  // Session timeout (30 minutes)
  timeout: 30 * 60 * 1000,

  // CSRF token validity (1 hour)
  csrfTokenValidity: 60 * 60 * 1000,

  // Remember me duration (7 days)
  rememberMeDuration: 7 * 24 * 60 * 60 * 1000
};

/**
 * File Upload Security
 */
export const UPLOAD_CONFIG = {
  // Allowed file types
  allowedTypes: [
    'application/json',
    'text/plain',
    'text/csv',
    'application/pdf'
  ],

  // Allowed extensions
  allowedExtensions: [
    '.json',
    '.txt',
    '.csv',
    '.pdf',
    '.log'
  ],

  // Max file size (10MB)
  maxSize: 10 * 1024 * 1024,

  // Scan for malware
  scanForMalware: true
};

/**
 * API Security Configuration
 */
export const API_SECURITY = {
  // Request timeout (30 seconds)
  timeout: 30000,

  // Max retries
  maxRetries: 3,

  // Retry delay (exponential backoff)
  retryDelay: (attempt) => Math.min(1000 * Math.pow(2, attempt), 30000),

  // Headers to include in all requests
  defaultHeaders: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  }
};

/**
 * XSS Protection Patterns
 *
 * Patterns to detect and prevent XSS attacks
 */
export const XSS_PATTERNS = [
  /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
  /javascript:/gi,
  /on\w+\s*=/gi, // Event handlers (onclick, onload, etc.)
  /<iframe/gi,
  /<object/gi,
  /<embed/gi,
  /eval\(/gi,
  /expression\(/gi
];

/**
 * SQL Injection Patterns
 *
 * Patterns to detect SQL injection attempts
 */
export const SQL_INJECTION_PATTERNS = [
  /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)/gi,
  /(UNION\s+SELECT)/gi,
  /--/g,
  /\/\*/g,
  /xp_/gi,
  /sp_/gi
];

/**
 * Security Event Logging
 */
export const SECURITY_EVENTS = {
  RATE_LIMIT_EXCEEDED: 'rate_limit_exceeded',
  INVALID_INPUT: 'invalid_input',
  XSS_ATTEMPT: 'xss_attempt',
  SQL_INJECTION_ATTEMPT: 'sql_injection_attempt',
  CSRF_TOKEN_MISMATCH: 'csrf_token_mismatch',
  UNAUTHORIZED_ACCESS: 'unauthorized_access',
  SUSPICIOUS_ACTIVITY: 'suspicious_activity'
};

/**
 * Log security event
 *
 * @param {string} eventType - Type of security event
 * @param {Object} details - Event details
 */
export const logSecurityEvent = (eventType, details = {}) => {
  const event = {
    type: eventType,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
    ...details
  };

  // Log to console in development
  if (process.env.NODE_ENV === 'development') {
    console.warn('[Security Event]', event);
  }

  // Send to security logging endpoint
  try {
    fetch('/api/security/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event)
    }).catch(() => {
      // Fail silently
    });
  } catch {
    // Fail silently
  }
};
