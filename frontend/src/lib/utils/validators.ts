/**
 * Validation utilities
 */

/**
 * Validate email address
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate IPv4 address
 */
export function isValidIPv4(ip: string): boolean {
  const ipv4Regex =
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipv4Regex.test(ip);
}

/**
 * Validate IPv6 address
 */
export function isValidIPv6(ip: string): boolean {
  const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
  return ipv6Regex.test(ip);
}

/**
 * Validate URL
 */
export function isValidURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate domain name
 */
export function isValidDomain(domain: string): boolean {
  const domainRegex =
    /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  return domainRegex.test(domain);
}

/**
 * Validate port number
 */
export function isValidPort(port: number | string): boolean {
  const portNum = typeof port === "string" ? parseInt(port, 10) : port;
  return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
}

/**
 * Validate CIDR notation
 */
export function isValidCIDR(cidr: string): boolean {
  const cidrRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}\/[0-9]{1,2}$/;
  if (!cidrRegex.test(cidr)) return false;

  const [ip, mask] = cidr.split("/");
  const maskNum = parseInt(mask, 10);
  return isValidIPv4(ip) && maskNum >= 0 && maskNum <= 32;
}

/**
 * Validate MAC address
 */
export function isValidMAC(mac: string): boolean {
  const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
  return macRegex.test(mac);
}

/**
 * Validate hash (MD5, SHA1, SHA256, SHA512)
 */
export function isValidHash(
  hash: string,
  type: "md5" | "sha1" | "sha256" | "sha512",
): boolean {
  const lengths = {
    md5: 32,
    sha1: 40,
    sha256: 64,
    sha512: 128,
  };
  const hashRegex = new RegExp(`^[a-fA-F0-9]{${lengths[type]}}$`);
  return hashRegex.test(hash);
}

/**
 * Validate JWT token structure (basic)
 */
export function isValidJWT(token: string): boolean {
  const parts = token.split(".");
  if (parts.length !== 3) return false;

  try {
    // Check if parts are valid base64
    parts.forEach((part) => atob(part.replace(/-/g, "+").replace(/_/g, "/")));
    return true;
  } catch {
    return false;
  }
}

/**
 * Sanitize string for XSS prevention
 */
export function sanitizeString(str: string): string {
  return str
    .replace(/[<>]/g, "")
    .replace(/javascript:/gi, "")
    .replace(/on\w+=/gi, "");
}
