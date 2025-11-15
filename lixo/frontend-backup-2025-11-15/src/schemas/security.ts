/**
 * Security-related Zod schemas
 *
 * DOUTRINA VÉRTICE - GAP #4 (P1)
 * Type-safe validation for security-sensitive inputs
 *
 * Following Boris Cherny's principle: "Security cannot be an afterthought"
 */

import { z } from "zod";

// ============================================================================
// REGEX PATTERNS
// ============================================================================

const CVE_PATTERN = /^CVE-\d{4}-\d{4,}$/i;
const SAFE_NMAP_ARGS_PATTERN = /^[\w\s\-\.,:/]*$/;
const COMMAND_INJECTION_PATTERNS = [
  /&&/,
  /\|\|/,
  /;/,
  /\$\(/,
  /`/,
  /\|/,
  /</,
  />/,
  /\0/,
];

// ============================================================================
// CVE SCHEMA
// ============================================================================

/**
 * CVE identifier schema
 *
 * Validates CVE identifiers (e.g., CVE-2021-44228)
 */
export const CVESchema = z
  .string()
  .trim()
  .toUpperCase()
  .min(1, "CVE ID is required")
  .refine((val) => CVE_PATTERN.test(val), {
    message: "Invalid CVE format. Use: CVE-YYYY-NNNNN (e.g., CVE-2021-44228)",
  });

export type CVE = z.infer<typeof CVESchema>;

// ============================================================================
// NMAP ARGUMENTS SCHEMA
// ============================================================================

/**
 * Nmap custom arguments schema
 *
 * CRITICAL SECURITY: Prevents command injection
 * Only allows safe characters: alphanumeric, spaces, hyphens, dots, commas, colons, slashes
 */
export const NmapArgsSchema = z
  .string()
  .trim()
  .max(500, "Arguments too long (max 500 characters)")
  .refine(
    (val) => {
      // Empty is valid (no custom args)
      if (!val) return true;

      // Check for dangerous patterns
      return !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val));
    },
    {
      message:
        "Dangerous characters detected. Only alphanumeric, spaces, hyphens, dots, commas, colons, and slashes allowed",
    },
  )
  .refine(
    (val) => {
      // Empty is valid
      if (!val) return true;

      // Must match safe pattern
      return SAFE_NMAP_ARGS_PATTERN.test(val);
    },
    {
      message:
        "Invalid characters in arguments. Only alphanumeric, spaces, hyphens, dots, commas, colons, and slashes allowed",
    },
  );

export type NmapArgs = z.infer<typeof NmapArgsSchema>;

// ============================================================================
// PASSWORD SCHEMA
// ============================================================================

/**
 * Password schema
 *
 * Enforces:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one number
 * - At least one special character
 */
export const PasswordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password too long (max 128 characters)")
  .refine((val) => /[A-Z]/.test(val), {
    message: "Password must contain at least one uppercase letter",
  })
  .refine((val) => /[a-z]/.test(val), {
    message: "Password must contain at least one lowercase letter",
  })
  .refine((val) => /[0-9]/.test(val), {
    message: "Password must contain at least one number",
  })
  .refine((val) => /[^A-Za-z0-9]/.test(val), {
    message: "Password must contain at least one special character",
  });

export type Password = z.infer<typeof PasswordSchema>;

// ============================================================================
// API KEY SCHEMA
// ============================================================================

/**
 * API key schema
 *
 * Validates API keys (typically hex or base64)
 */
export const APIKeySchema = z
  .string()
  .trim()
  .min(32, "API key too short (minimum 32 characters)")
  .max(256, "API key too long (maximum 256 characters)")
  .refine((val) => /^[A-Za-z0-9_\-]+$/.test(val), {
    message: "API key contains invalid characters",
  });

export type APIKey = z.infer<typeof APIKeySchema>;

// ============================================================================
// JWT TOKEN SCHEMA
// ============================================================================

/**
 * JWT token schema
 *
 * Validates JWT format (header.payload.signature)
 */
export const JWTSchema = z
  .string()
  .trim()
  .min(1, "JWT token is required")
  .refine(
    (val) => {
      const parts = val.split(".");
      return parts.length === 3 && parts.every((p) => p.length > 0);
    },
    {
      message: "Invalid JWT format. Expected: header.payload.signature",
    },
  );

export type JWT = z.infer<typeof JWTSchema>;
