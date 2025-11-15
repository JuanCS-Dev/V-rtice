/**
 * Comprehensive Input Validation Utilities
 * Boris Cherny Standard - Type-safe, secure, production-ready
 *
 * Addresses Air Gaps: #10, #12, #13, #14, #40, #41, #42, #43, #44, #45, #74, #75, #76
 */

// ============================================================================
// REGEX PATTERNS
// ============================================================================

const PATTERNS = {
  // Network
  IPV4: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  IPV6: /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/,
  DOMAIN:
    /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,

  // Security
  CVE: /^CVE-\d{4}-\d{4,}$/i,
  SAFE_NMAP_ARGS: /^[\w\s\-\.,:/]*$/,
  PHONE: /^[\d\s\-\+\(\)]{7,20}$/,

  // Social
  USERNAME: /^[a-zA-Z0-9_\-\.]{1,30}$/,

  // Data formats
  NUMERIC_CSV: /^[\d\s,.\-]+$/,

  // Dangerous patterns
  COMMAND_INJECTION: [/&&/, /\|\|/, /;/, /\$\(/, /`/, /\|/, /</, />/, /\0/],
  XSS_PATTERNS: [
    /<script/i,
    /javascript:/i,
    /onerror=/i,
    /onload=/i,
    /eval\(/i,
  ],
  SQL_INJECTION: [
    /(\bor\b|\band\b).*?=/i,
    /union.*?select/i,
    /insert.*?into/i,
    /delete.*?from/i,
  ],
  UNSAFE_URL_SCHEMES: [/^javascript:/i, /^data:/i, /^file:/i, /^vbscript:/i],
};

// ============================================================================
// VALIDATION LIMITS
// ============================================================================

const LIMITS = {
  // Input lengths
  SHORT_TEXT: 100,
  MEDIUM_TEXT: 500,
  LONG_TEXT: 1000,
  VERY_LONG_TEXT: 5000,

  // Network
  PORT_MIN: 1,
  PORT_MAX: 65535,

  // Minimums
  MIN_PASSWORD: 8,
  MIN_USERNAME: 3,
  MIN_SEARCH: 2,
};

// ============================================================================
// VALIDATION RESULT TYPE
// ============================================================================

/**
 * @typedef {Object} ValidationResult
 * @property {boolean} valid - Whether the input is valid
 * @property {string|null} error - Error message if invalid, null otherwise
 * @property {*} sanitized - Sanitized value (trimmed, normalized)
 */

/**
 * Creates a validation result
 * @param {boolean} valid
 * @param {string|null} error
 * @param {*} sanitized
 * @returns {ValidationResult}
 */
function createResult(valid, error = null, sanitized = null) {
  return { valid, error, sanitized };
}

// ============================================================================
// CORE VALIDATORS
// ============================================================================

/**
 * Validates and sanitizes an IP address (v4 or v6)
 * Addresses GAP #10
 */
export function validateIP(ip) {
  if (typeof ip !== "string") {
    return createResult(false, "IP must be a string");
  }

  const trimmed = ip.trim();

  if (!trimmed) {
    return createResult(false, "IP address is required");
  }

  // Check for command injection patterns
  for (const pattern of PATTERNS.COMMAND_INJECTION) {
    if (pattern.test(trimmed)) {
      return createResult(false, "Invalid characters in IP address");
    }
  }

  // Validate IPv4
  if (PATTERNS.IPV4.test(trimmed)) {
    return createResult(true, null, trimmed);
  }

  // Validate IPv6
  if (PATTERNS.IPV6.test(trimmed)) {
    return createResult(true, null, trimmed);
  }

  return createResult(
    false,
    "Invalid IP address format. Use IPv4 (e.g., 192.168.1.1) or IPv6",
  );
}

/**
 * Validates email address
 * Addresses GAP #12
 */
export function validateEmail(email) {
  if (typeof email !== "string") {
    return createResult(false, "Email must be a string");
  }

  const trimmed = email.trim().toLowerCase();

  if (!trimmed) {
    return createResult(false, "Email is required");
  }

  if (trimmed.length > LIMITS.MEDIUM_TEXT) {
    return createResult(
      false,
      `Email too long (max ${LIMITS.MEDIUM_TEXT} characters)`,
    );
  }

  // Check for SQL injection patterns
  for (const pattern of PATTERNS.SQL_INJECTION) {
    if (pattern.test(trimmed)) {
      return createResult(false, "Invalid characters in email");
    }
  }

  if (!PATTERNS.EMAIL.test(trimmed)) {
    return createResult(false, "Invalid email format");
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates port number or port range
 * Addresses GAP #13
 */
export function validatePorts(ports) {
  if (typeof ports !== "string") {
    return createResult(false, "Ports must be a string");
  }

  const trimmed = ports.trim();

  if (!trimmed) {
    return createResult(false, "Ports are required");
  }

  // Check for command injection
  for (const pattern of PATTERNS.COMMAND_INJECTION) {
    if (pattern.test(trimmed)) {
      return createResult(false, "Invalid characters in port specification");
    }
  }

  // Parse comma-separated ports/ranges
  const parts = trimmed.split(",").map((p) => p.trim());

  for (const part of parts) {
    if (part.includes("-")) {
      // Port range
      const [start, end] = part.split("-").map((p) => p.trim());
      const startNum = parseInt(start, 10);
      const endNum = parseInt(end, 10);

      if (isNaN(startNum) || isNaN(endNum)) {
        return createResult(false, `Invalid port range: ${part}`);
      }

      if (startNum < LIMITS.PORT_MIN || endNum > LIMITS.PORT_MAX) {
        return createResult(
          false,
          `Port range out of bounds: ${part} (valid: ${LIMITS.PORT_MIN}-${LIMITS.PORT_MAX})`,
        );
      }

      if (startNum > endNum) {
        return createResult(false, `Invalid port range: ${part} (start > end)`);
      }
    } else {
      // Single port
      const portNum = parseInt(part, 10);

      if (isNaN(portNum)) {
        return createResult(false, `Invalid port: ${part}`);
      }

      if (portNum < LIMITS.PORT_MIN || portNum > LIMITS.PORT_MAX) {
        return createResult(
          false,
          `Port out of bounds: ${part} (valid: ${LIMITS.PORT_MIN}-${LIMITS.PORT_MAX})`,
        );
      }
    }
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates CVE identifier
 * Addresses GAP #14
 */
export function validateCVE(cveId) {
  if (typeof cveId !== "string") {
    return createResult(false, "CVE ID must be a string");
  }

  const trimmed = cveId.trim().toUpperCase();

  if (!trimmed) {
    return createResult(false, "CVE ID is required");
  }

  if (!PATTERNS.CVE.test(trimmed)) {
    return createResult(
      false,
      "Invalid CVE format. Use: CVE-YYYY-NNNNN (e.g., CVE-2021-44228)",
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates Nmap custom arguments - CRITICAL SECURITY
 * Addresses GAP #11 - Command Injection Prevention
 */
export function validateNmapArgs(args) {
  if (typeof args !== "string") {
    return createResult(false, "Arguments must be a string");
  }

  const trimmed = args.trim();

  // Empty is valid (no custom args)
  if (!trimmed) {
    return createResult(true, null, "");
  }

  if (trimmed.length > LIMITS.MEDIUM_TEXT) {
    return createResult(
      false,
      `Arguments too long (max ${LIMITS.MEDIUM_TEXT} characters)`,
    );
  }

  // Check for dangerous patterns first
  for (const pattern of PATTERNS.COMMAND_INJECTION) {
    if (pattern.test(trimmed)) {
      return createResult(
        false,
        "Dangerous characters detected. Only alphanumeric, spaces, hyphens, dots, commas, colons, and slashes allowed",
      );
    }
  }

  // Must match safe pattern
  if (!PATTERNS.SAFE_NMAP_ARGS.test(trimmed)) {
    return createResult(
      false,
      "Invalid characters in arguments. Only alphanumeric, spaces, hyphens, dots, commas, colons, and slashes allowed",
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates domain name
 * Addresses GAP #41
 */
export function validateDomain(domain) {
  if (typeof domain !== "string") {
    return createResult(false, "Domain must be a string");
  }

  const trimmed = domain.trim().toLowerCase();

  if (!trimmed) {
    return createResult(false, "Domain is required");
  }

  if (trimmed.length > LIMITS.MEDIUM_TEXT) {
    return createResult(
      false,
      `Domain too long (max ${LIMITS.MEDIUM_TEXT} characters)`,
    );
  }

  // Check for command injection
  for (const pattern of PATTERNS.COMMAND_INJECTION) {
    if (pattern.test(trimmed)) {
      return createResult(false, "Invalid characters in domain");
    }
  }

  if (!PATTERNS.DOMAIN.test(trimmed)) {
    return createResult(false, "Invalid domain format");
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates URL - prevents javascript:, data:, file:// schemes
 * Addresses GAP #42
 */
export function validateURL(url) {
  if (typeof url !== "string") {
    return createResult(false, "URL must be a string");
  }

  const trimmed = url.trim();

  if (!trimmed) {
    return createResult(false, "URL is required");
  }

  if (trimmed.length > LIMITS.LONG_TEXT) {
    return createResult(
      false,
      `URL too long (max ${LIMITS.LONG_TEXT} characters)`,
    );
  }

  // Check for dangerous URL schemes
  for (const pattern of PATTERNS.UNSAFE_URL_SCHEMES) {
    if (pattern.test(trimmed)) {
      return createResult(
        false,
        "Unsafe URL scheme. Only http:// and https:// allowed",
      );
    }
  }

  if (!PATTERNS.URL.test(trimmed)) {
    return createResult(
      false,
      "Invalid URL format. Must start with http:// or https://",
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates phone number
 * Addresses GAP #40
 */
export function validatePhone(phone) {
  if (typeof phone !== "string") {
    return createResult(false, "Phone must be a string");
  }

  const trimmed = phone.trim();

  if (!trimmed) {
    return createResult(false, "Phone number is required");
  }

  if (!PATTERNS.PHONE.test(trimmed)) {
    return createResult(false, "Invalid phone number format");
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates username (social media, etc.)
 * Addresses GAP #45
 */
export function validateUsername(username) {
  if (typeof username !== "string") {
    return createResult(false, "Username must be a string");
  }

  const trimmed = username.trim();

  if (!trimmed) {
    return createResult(false, "Username is required");
  }

  if (trimmed.length < LIMITS.MIN_USERNAME) {
    return createResult(
      false,
      `Username too short (min ${LIMITS.MIN_USERNAME} characters)`,
    );
  }

  if (trimmed.length > LIMITS.SHORT_TEXT) {
    return createResult(
      false,
      `Username too long (max ${LIMITS.SHORT_TEXT} characters)`,
    );
  }

  if (!PATTERNS.USERNAME.test(trimmed)) {
    return createResult(
      false,
      "Invalid username. Only letters, numbers, underscores, hyphens, and dots allowed",
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates numeric CSV data
 * Addresses GAP #43
 */
export function validateNumericCSV(csv) {
  if (typeof csv !== "string") {
    return createResult(false, "CSV data must be a string");
  }

  const trimmed = csv.trim();

  if (!trimmed) {
    return createResult(false, "CSV data is required");
  }

  if (trimmed.length > LIMITS.VERY_LONG_TEXT) {
    return createResult(
      false,
      `CSV data too long (max ${LIMITS.VERY_LONG_TEXT} characters)`,
    );
  }

  if (!PATTERNS.NUMERIC_CSV.test(trimmed)) {
    return createResult(
      false,
      "Invalid CSV format. Only numbers, spaces, commas, dots, and hyphens allowed",
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates email list (comma-separated)
 * Addresses GAP #44
 */
export function validateEmailList(emailList) {
  if (typeof emailList !== "string") {
    return createResult(false, "Email list must be a string");
  }

  const trimmed = emailList.trim();

  if (!trimmed) {
    return createResult(false, "Email list is required");
  }

  const emails = trimmed.split(",").map((e) => e.trim());
  const invalidEmails = [];

  for (const email of emails) {
    const result = validateEmail(email);
    if (!result.valid) {
      invalidEmails.push(email);
    }
  }

  if (invalidEmails.length > 0) {
    return createResult(false, `Invalid emails: ${invalidEmails.join(", ")}`);
  }

  return createResult(true, null, emails);
}

/**
 * Validates generic text input with length constraints
 * Addresses GAP #15, #16, #74, #76
 */
export function validateText(text, options = {}) {
  const {
    minLength = 1,
    maxLength = LIMITS.MEDIUM_TEXT,
    allowEmpty = false,
    fieldName = "Input",
  } = options;

  if (typeof text !== "string") {
    return createResult(false, `${fieldName} must be a string`);
  }

  const trimmed = text.trim();

  // Check empty
  if (!allowEmpty && !trimmed) {
    return createResult(
      false,
      `${fieldName} cannot be empty or whitespace-only`,
    );
  }

  // Check minimum length
  if (trimmed.length < minLength) {
    return createResult(
      false,
      `${fieldName} too short (min ${minLength} characters)`,
    );
  }

  // Check maximum length
  if (trimmed.length > maxLength) {
    return createResult(
      false,
      `${fieldName} too long (max ${maxLength} characters)`,
    );
  }

  // Check for null bytes and dangerous characters
  if (/\0/.test(trimmed)) {
    return createResult(false, `${fieldName} contains invalid characters`);
  }

  // Check for text direction override (potential spoofing)
  // U+202E (RIGHT-TO-LEFT OVERRIDE)
  if (/\u202E/.test(trimmed)) {
    return createResult(
      false,
      `${fieldName} contains invalid unicode characters`,
    );
  }

  return createResult(true, null, trimmed);
}

/**
 * Validates select/dropdown value against allowed options
 * Addresses GAP #77
 */
export function validateSelect(value, allowedOptions) {
  if (!Array.isArray(allowedOptions) || allowedOptions.length === 0) {
    return createResult(false, "No options available");
  }

  if (value === null || value === undefined || value === "") {
    return createResult(false, "Please select an option");
  }

  if (!allowedOptions.includes(value)) {
    return createResult(false, "Invalid option selected");
  }

  return createResult(true, null, value);
}

// ============================================================================
// BATCH VALIDATION
// ============================================================================

/**
 * Validates multiple fields at once
 * @param {Object} validations - Map of field names to validation functions
 * @returns {Object} - { valid: boolean, errors: { fieldName: error } }
 */
export function validateFields(validations) {
  const errors = {};
  let isValid = true;

  for (const [fieldName, validationFn] of Object.entries(validations)) {
    const result = validationFn();
    if (!result.valid) {
      errors[fieldName] = result.error;
      isValid = false;
    }
  }

  return { valid: isValid, errors };
}

// ============================================================================
// EXPORTS
// ============================================================================

export const VALIDATION_LIMITS = LIMITS;
export const VALIDATION_PATTERNS = PATTERNS;
