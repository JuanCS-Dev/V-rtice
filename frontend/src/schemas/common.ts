/**
 * Common validation schemas
 *
 * DOUTRINA VÉRTICE - GAP #4 (P1)
 * General-purpose type-safe validation schemas
 *
 * Following Boris Cherny's principle: "Consistency reduces cognitive load"
 */

import { z } from 'zod';

// ============================================================================
// REGEX PATTERNS
// ============================================================================

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_PATTERN = /^[\d\s\-\+\(\)]{7,20}$/;
const USERNAME_PATTERN = /^[a-zA-Z0-9_\-\.]{1,30}$/;
const NUMERIC_CSV_PATTERN = /^[\d\s,.\-]+$/;
const SQL_INJECTION_PATTERNS = [/(\bor\b|\band\b).*?=/i, /union.*?select/i, /insert.*?into/i, /delete.*?from/i];

// ============================================================================
// EMAIL SCHEMA
// ============================================================================

/**
 * Email address schema
 *
 * Validates email addresses with SQL injection prevention
 */
export const EmailSchema = z
  .string()
  .trim()
  .toLowerCase()
  .min(1, 'Email is required')
  .max(500, 'Email too long (max 500 characters)')
  .refine((val) => !SQL_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: 'Invalid characters in email',
  })
  .refine((val) => EMAIL_PATTERN.test(val), {
    message: 'Invalid email format',
  });

export type Email = z.infer<typeof EmailSchema>;

/**
 * Email list schema (comma-separated)
 *
 * Validates multiple email addresses
 */
export const EmailListSchema = z
  .string()
  .trim()
  .min(1, 'Email list is required')
  .transform((val) => val.split(',').map((e) => e.trim()))
  .pipe(
    z.array(EmailSchema).min(1, 'At least one email is required')
  );

export type EmailList = z.infer<typeof EmailListSchema>;

// ============================================================================
// PHONE SCHEMA
// ============================================================================

/**
 * Phone number schema
 *
 * Validates phone numbers with various formats
 */
export const PhoneSchema = z
  .string()
  .trim()
  .min(1, 'Phone number is required')
  .refine((val) => PHONE_PATTERN.test(val), {
    message: 'Invalid phone number format',
  });

export type Phone = z.infer<typeof PhoneSchema>;

// ============================================================================
// USERNAME SCHEMA
// ============================================================================

/**
 * Username schema (social media, etc.)
 *
 * Validates usernames with alphanumeric, underscores, hyphens, and dots
 */
export const UsernameSchema = z
  .string()
  .trim()
  .min(3, 'Username too short (min 3 characters)')
  .max(100, 'Username too long (max 100 characters)')
  .refine((val) => USERNAME_PATTERN.test(val), {
    message: 'Invalid username. Only letters, numbers, underscores, hyphens, and dots allowed',
  });

export type Username = z.infer<typeof UsernameSchema>;

// ============================================================================
// TEXT SCHEMAS
// ============================================================================

/**
 * Short text schema (max 100 characters)
 *
 * For brief inputs like names, titles, etc.
 */
export const ShortTextSchema = z
  .string()
  .trim()
  .min(1, 'This field cannot be empty')
  .max(100, 'Text too long (max 100 characters)')
  .refine((val) => !/\0/.test(val), {
    message: 'Invalid characters in text',
  })
  .refine((val) => !/\u202E/.test(val), {
    message: 'Invalid unicode characters in text',
  });

export type ShortText = z.infer<typeof ShortTextSchema>;

/**
 * Medium text schema (max 500 characters)
 *
 * For descriptions, comments, etc.
 */
export const MediumTextSchema = z
  .string()
  .trim()
  .min(1, 'This field cannot be empty')
  .max(500, 'Text too long (max 500 characters)')
  .refine((val) => !/\0/.test(val), {
    message: 'Invalid characters in text',
  })
  .refine((val) => !/\u202E/.test(val), {
    message: 'Invalid unicode characters in text',
  });

export type MediumText = z.infer<typeof MediumTextSchema>;

/**
 * Long text schema (max 1000 characters)
 *
 * For longer content like notes, reports, etc.
 */
export const LongTextSchema = z
  .string()
  .trim()
  .min(1, 'This field cannot be empty')
  .max(1000, 'Text too long (max 1000 characters)')
  .refine((val) => !/\0/.test(val), {
    message: 'Invalid characters in text',
  })
  .refine((val) => !/\u202E/.test(val), {
    message: 'Invalid unicode characters in text',
  });

export type LongText = z.infer<typeof LongTextSchema>;

/**
 * Very long text schema (max 5000 characters)
 *
 * For very long content like documentation, logs, etc.
 */
export const VeryLongTextSchema = z
  .string()
  .trim()
  .min(1, 'This field cannot be empty')
  .max(5000, 'Text too long (max 5000 characters)')
  .refine((val) => !/\0/.test(val), {
    message: 'Invalid characters in text',
  })
  .refine((val) => !/\u202E/.test(val), {
    message: 'Invalid unicode characters in text',
  });

export type VeryLongText = z.infer<typeof VeryLongTextSchema>;

// ============================================================================
// SELECT SCHEMA
// ============================================================================

/**
 * Creates a select/dropdown schema with allowed options
 *
 * @param options - Array of allowed values
 * @param errorMessage - Custom error message
 */
export const createSelectSchema = <T extends string>(
  options: readonly [T, ...T[]],
  errorMessage = 'Invalid option selected'
) => {
  return z.enum(options, { errorMap: () => ({ message: errorMessage }) });
};

// ============================================================================
// NUMERIC CSV SCHEMA
// ============================================================================

/**
 * Numeric CSV schema
 *
 * Validates comma-separated numeric data
 */
export const NumericCSVSchema = z
  .string()
  .trim()
  .min(1, 'CSV data is required')
  .max(5000, 'CSV data too long (max 5000 characters)')
  .refine((val) => NUMERIC_CSV_PATTERN.test(val), {
    message: 'Invalid CSV format. Only numbers, spaces, commas, dots, and hyphens allowed',
  });

export type NumericCSV = z.infer<typeof NumericCSVSchema>;

// ============================================================================
// SEARCH QUERY SCHEMA
// ============================================================================

/**
 * Search query schema
 *
 * Validates search queries with minimum length
 */
export const SearchQuerySchema = z
  .string()
  .trim()
  .min(2, 'Search query too short (min 2 characters)')
  .max(500, 'Search query too long (max 500 characters)')
  .refine((val) => !/\0/.test(val), {
    message: 'Invalid characters in search query',
  });

export type SearchQuery = z.infer<typeof SearchQuerySchema>;

// ============================================================================
// ID SCHEMAS
// ============================================================================

/**
 * UUID schema
 *
 * Validates UUID v4 format
 */
export const UUIDSchema = z
  .string()
  .uuid('Invalid UUID format');

export type UUID = z.infer<typeof UUIDSchema>;

/**
 * Positive integer ID schema
 *
 * For database IDs, etc.
 */
export const IDSchema = z
  .number()
  .int('ID must be an integer')
  .positive('ID must be positive');

export type ID = z.infer<typeof IDSchema>;
