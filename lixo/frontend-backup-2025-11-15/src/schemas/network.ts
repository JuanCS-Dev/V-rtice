/**
 * Network-related Zod schemas
 *
 * DOUTRINA VÉRTICE - GAP #4 (P1)
 * Type-safe validation schemas using Zod
 *
 * Following Boris Cherny's principle: "If it doesn't have types, it's not production"
 */

import { z } from "zod";

// ============================================================================
// REGEX PATTERNS
// ============================================================================

const IPV4_PATTERN =
  /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

const IPV6_PATTERN =
  /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/;

const DOMAIN_PATTERN =
  /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;

const URL_PATTERN =
  /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;

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
// IP ADDRESS SCHEMAS
// ============================================================================

/**
 * IPv4 address schema
 *
 * Validates IPv4 addresses (e.g., 192.168.1.1)
 */
export const IPv4Schema = z
  .string()
  .trim()
  .min(1, "IPv4 address is required")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in IPv4 address",
  })
  .refine((val) => IPV4_PATTERN.test(val), {
    message: "Invalid IPv4 format. Use: xxx.xxx.xxx.xxx",
  });

/**
 * IPv6 address schema
 *
 * Validates IPv6 addresses
 */
export const IPv6Schema = z
  .string()
  .trim()
  .min(1, "IPv6 address is required")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in IPv6 address",
  })
  .refine((val) => IPV6_PATTERN.test(val), {
    message: "Invalid IPv6 format",
  });

/**
 * IP address schema (IPv4 or IPv6)
 *
 * Accepts both IPv4 and IPv6 addresses
 */
export const IPSchema = z
  .string()
  .trim()
  .min(1, "IP address is required")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in IP address",
  })
  .refine((val) => IPV4_PATTERN.test(val) || IPV6_PATTERN.test(val), {
    message: "Invalid IP address. Use IPv4 (e.g., 192.168.1.1) or IPv6",
  });

export type IPAddress = z.infer<typeof IPSchema>;

// ============================================================================
// PORT SCHEMAS
// ============================================================================

/**
 * Single port number schema
 *
 * Validates port numbers (1-65535)
 */
export const PortSchema = z
  .number()
  .int("Port must be an integer")
  .min(1, "Port must be at least 1")
  .max(65535, "Port must be at most 65535");

/**
 * Port range schema (e.g., "80-443" or "8000,8080,9000")
 *
 * Validates port ranges and comma-separated lists
 */
export const PortRangeSchema = z
  .string()
  .trim()
  .min(1, "Ports are required")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in port specification",
  })
  .refine(
    (val) => {
      const parts = val.split(",").map((p) => p.trim());

      for (const part of parts) {
        if (part.includes("-")) {
          // Port range
          const [start, end] = part.split("-").map((p) => p.trim());
          const startNum = parseInt(start, 10);
          const endNum = parseInt(end, 10);

          if (isNaN(startNum) || isNaN(endNum)) return false;
          if (startNum < 1 || endNum > 65535) return false;
          if (startNum > endNum) return false;
        } else {
          // Single port
          const portNum = parseInt(part, 10);
          if (isNaN(portNum)) return false;
          if (portNum < 1 || portNum > 65535) return false;
        }
      }

      return true;
    },
    {
      message:
        "Invalid port range. Use single ports (80), ranges (80-443), or comma-separated (80,443,8080)",
    },
  );

export type PortRange = z.infer<typeof PortRangeSchema>;

// ============================================================================
// DOMAIN SCHEMA
// ============================================================================

/**
 * Domain name schema
 *
 * Validates domain names (e.g., example.com)
 */
export const DomainSchema = z
  .string()
  .trim()
  .toLowerCase()
  .min(1, "Domain is required")
  .max(500, "Domain too long (max 500 characters)")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in domain",
  })
  .refine((val) => DOMAIN_PATTERN.test(val), {
    message: "Invalid domain format",
  });

export type Domain = z.infer<typeof DomainSchema>;

// ============================================================================
// URL SCHEMA
// ============================================================================

const UNSAFE_URL_SCHEMES = [
  /^javascript:/i,
  /^data:/i,
  /^file:/i,
  /^vbscript:/i,
];

/**
 * URL schema
 *
 * Validates HTTP/HTTPS URLs only (prevents javascript:, data:, file://)
 */
export const URLSchema = z
  .string()
  .trim()
  .min(1, "URL is required")
  .max(1000, "URL too long (max 1000 characters)")
  .refine((val) => !UNSAFE_URL_SCHEMES.some((p) => p.test(val)), {
    message: "Unsafe URL scheme. Only http:// and https:// allowed",
  })
  .refine((val) => URL_PATTERN.test(val), {
    message: "Invalid URL format. Must start with http:// or https://",
  });

export type URL = z.infer<typeof URLSchema>;

// ============================================================================
// IP OR DOMAIN SCHEMA
// ============================================================================

/**
 * IP address or domain name schema
 *
 * Accepts either IP addresses or domain names
 * Useful for target fields in scanning forms
 */
export const IPOrDomainSchema = z
  .string()
  .trim()
  .min(1, "Target is required")
  .refine((val) => !COMMAND_INJECTION_PATTERNS.some((p) => p.test(val)), {
    message: "Invalid characters in target",
  })
  .refine(
    (val) => {
      const isIP = IPV4_PATTERN.test(val) || IPV6_PATTERN.test(val);
      const isDomain = DOMAIN_PATTERN.test(val);
      return isIP || isDomain;
    },
    {
      message: "Must be a valid IP address or domain name",
    },
  );

export type IPOrDomain = z.infer<typeof IPOrDomainSchema>;
