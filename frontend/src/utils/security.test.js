/**
 * Security Utilities Tests
 */

import { describe, it, expect } from 'vitest';
import {
  sanitizeHTML,
  escapeHTML,
  isValidEmail,
  isValidURL,
  isValidIPv4,
  isValidDomain,
  sanitizeCVEId,
  isValidLength,
  sanitizeFilename,
  isAlphanumeric,
  removeScriptTags,
  OWASP
} from './security';

describe('Security Utilities', () => {
  describe('sanitizeHTML', () => {
    it('should convert HTML to text', () => {
      const result = sanitizeHTML('<script>alert("xss")</script>');
      expect(result).not.toContain('<script>');
      expect(result).toContain('&lt;script&gt;');
    });

    it('should handle non-string input', () => {
      expect(sanitizeHTML(null)).toBe('');
      expect(sanitizeHTML(undefined)).toBe('');
      expect(sanitizeHTML(123)).toBe('');
    });
  });

  describe('escapeHTML', () => {
    it('should escape HTML special characters', () => {
      expect(escapeHTML('<div>')).toBe('&lt;div&gt;');
      expect(escapeHTML('"test"')).toBe('&quot;test&quot;');
      expect(escapeHTML("'test'")).toBe('&#x27;test&#x27;');
      expect(escapeHTML('a & b')).toBe('a &amp; b');
    });

    it('should handle non-string input', () => {
      expect(escapeHTML(null)).toBe('');
    });
  });

  describe('isValidEmail', () => {
    it('should validate correct emails', () => {
      expect(isValidEmail('test@example.com')).toBe(true);
      expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
    });

    it('should reject invalid emails', () => {
      expect(isValidEmail('invalid')).toBe(false);
      expect(isValidEmail('test@')).toBe(false);
      expect(isValidEmail('@example.com')).toBe(false);
      expect(isValidEmail('test @example.com')).toBe(false);
    });

    it('should handle non-string input', () => {
      expect(isValidEmail(null)).toBe(false);
    });
  });

  describe('isValidURL', () => {
    it('should validate correct URLs', () => {
      expect(isValidURL('http://example.com')).toBe(true);
      expect(isValidURL('https://example.com/path')).toBe(true);
    });

    it('should reject invalid URLs', () => {
      expect(isValidURL('not a url')).toBe(false);
      expect(isValidURL('javascript:alert(1)')).toBe(false);
      expect(isValidURL('ftp://example.com')).toBe(false);
    });

    it('should allow custom protocols', () => {
      expect(isValidURL('ftp://example.com', ['ftp'])).toBe(true);
    });
  });

  describe('isValidIPv4', () => {
    it('should validate correct IPv4 addresses', () => {
      expect(isValidIPv4('192.168.1.1')).toBe(true);
      expect(isValidIPv4('127.0.0.1')).toBe(true);
      expect(isValidIPv4('255.255.255.255')).toBe(true);
    });

    it('should reject invalid IPv4 addresses', () => {
      expect(isValidIPv4('256.1.1.1')).toBe(false);
      expect(isValidIPv4('192.168.1')).toBe(false);
      expect(isValidIPv4('192.168.1.1.1')).toBe(false);
      expect(isValidIPv4('not.an.ip.address')).toBe(false);
    });
  });

  describe('isValidDomain', () => {
    it('should validate correct domains', () => {
      expect(isValidDomain('example.com')).toBe(true);
      expect(isValidDomain('subdomain.example.com')).toBe(true);
      expect(isValidDomain('example.co.uk')).toBe(true);
    });

    it('should reject invalid domains', () => {
      expect(isValidDomain('invalid')).toBe(false);
      expect(isValidDomain('.example.com')).toBe(false);
      expect(isValidDomain('example..com')).toBe(false);
      expect(isValidDomain('example.com.')).toBe(false);
    });
  });

  describe('sanitizeCVEId', () => {
    it('should validate and normalize CVE IDs', () => {
      expect(sanitizeCVEId('CVE-2021-1234')).toBe('CVE-2021-1234');
      expect(sanitizeCVEId('cve-2021-1234')).toBe('CVE-2021-1234');
      expect(sanitizeCVEId('  CVE-2021-1234  ')).toBe('CVE-2021-1234');
    });

    it('should reject invalid CVE IDs', () => {
      expect(sanitizeCVEId('CVE-123-456')).toBeNull();
      expect(sanitizeCVEId('invalid')).toBeNull();
      expect(sanitizeCVEId('CVE-20211234')).toBeNull();
    });
  });

  describe('isValidLength', () => {
    it('should validate string length', () => {
      expect(isValidLength('test', 1, 10)).toBe(true);
      expect(isValidLength('test', 4, 4)).toBe(true);
    });

    it('should reject invalid lengths', () => {
      expect(isValidLength('test', 5, 10)).toBe(false);
      expect(isValidLength('test', 1, 3)).toBe(false);
    });
  });

  describe('sanitizeFilename', () => {
    it('should sanitize filenames', () => {
      expect(sanitizeFilename('test file.txt')).toBe('test_file.txt');
      expect(sanitizeFilename('file<>:"/\\|?*.exe')).toBe('file_________.exe');
    });

    it('should prevent directory traversal', () => {
      expect(sanitizeFilename('../../../etc/passwd')).toBe('._._._etc_passwd');
      expect(sanitizeFilename('test..txt')).toBe('test.txt');
    });

    it('should limit length', () => {
      const longName = 'a'.repeat(300);
      expect(sanitizeFilename(longName).length).toBe(255);
    });
  });

  describe('isAlphanumeric', () => {
    it('should validate alphanumeric strings', () => {
      expect(isAlphanumeric('abc123')).toBe(true);
      expect(isAlphanumeric('ABC')).toBe(true);
      expect(isAlphanumeric('123')).toBe(true);
    });

    it('should reject non-alphanumeric', () => {
      expect(isAlphanumeric('abc-123')).toBe(false);
      expect(isAlphanumeric('abc 123')).toBe(false);
      expect(isAlphanumeric('abc@123')).toBe(false);
    });
  });

  describe('removeScriptTags', () => {
    it('should remove script tags', () => {
      const html = '<div>Safe</div><script>alert("xss")</script><p>More safe</p>';
      const result = removeScriptTags(html);
      expect(result).not.toContain('<script>');
      expect(result).toContain('<div>Safe</div>');
      expect(result).toContain('<p>More safe</p>');
    });

    it('should remove multiple script tags', () => {
      const html = '<script>bad1</script>text<script>bad2</script>';
      const result = removeScriptTags(html);
      expect(result).toBe('text');
    });
  });

  describe('OWASP helpers', () => {
    it('should prevent injection', () => {
      const malicious = "<script>alert('xss')</script>";
      const result = OWASP.preventInjection(malicious);
      expect(result).not.toContain('<script>');
    });

    it('should mask sensitive data', () => {
      expect(OWASP.maskSensitiveData('1234567890', 4)).toBe('******7890');
      expect(OWASP.maskSensitiveData('123', 4)).toBe('***');
    });

    it('should prevent XSS', () => {
      const xss = '<img src=x onerror=alert(1)>';
      const result = OWASP.preventXSS(xss);
      expect(result).not.toContain('<img');
      expect(result).not.toContain('<script');
      // Should be escaped
      expect(result).toContain('&lt;');
    });
  });
});
