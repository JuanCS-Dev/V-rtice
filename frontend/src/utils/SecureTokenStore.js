/**
 * SecureTokenStore - Secure token storage with memory-first strategy
 * Boris Cherny Pattern: Defense in depth against XSS attacks
 *
 * Storage Strategy:
 * 1. Primary: In-memory (cleared on tab close, XSS-resistant)
 * 2. Backup: sessionStorage (cleared on tab close, NOT XSS-proof)
 * 3. Future: httpOnly cookies (requires backend support)
 *
 * Why NOT localStorage:
 * - Persists across sessions (bad for security)
 * - Accessible via XSS (any injected script can steal tokens)
 * - No automatic cleanup on browser close
 *
 * Governed by: Constituição Vértice v2.7, Security Best Practices
 */

import logger from "./logger";

class SecureTokenStore {
  constructor() {
    // Primary storage: In-memory (most secure)
    this._memoryCache = new Map();

    // Setup cleanup on window close
    if (typeof window !== "undefined") {
      window.addEventListener("beforeunload", () => {
        this.clearAll();
      });
    }
  }

  /**
   * Store a token securely
   * Boris Cherny Pattern: Fail-safe with graceful degradation
   */
  setToken(key, value, expiresIn) {
    if (!key || !value) {
      logger.warn("SecureTokenStore: Cannot store empty key or value");
      return false;
    }

    try {
      const expiresAt = Date.now() + expiresIn * 1000;

      // Store in memory (primary)
      this._memoryCache.set(key, {
        value,
        expiresAt,
        storedAt: Date.now(),
      });

      // Backup in sessionStorage (cleared on tab close)
      // Note: Still vulnerable to XSS, but better than localStorage
      if (typeof sessionStorage !== "undefined") {
        const encryptedData = this._simpleEncrypt(
          JSON.stringify({ value, expiresAt }),
        );
        sessionStorage.setItem(`vertice_secure_${key}`, encryptedData);
      }

      logger.info(`Token '${key}' stored securely (expires in ${expiresIn}s)`);
      return true;
    } catch (error) {
      logger.error("SecureTokenStore: Failed to store token", error);
      return false;
    }
  }

  /**
   * Retrieve a token securely
   * Boris Cherny Pattern: Defense in depth with multiple fallbacks
   */
  getToken(key) {
    if (!key) {
      return null;
    }

    try {
      // Check memory first (fastest, most secure)
      const memoryEntry = this._memoryCache.get(key);
      if (memoryEntry) {
        // Check expiration
        if (memoryEntry.expiresAt > Date.now()) {
          return memoryEntry.value;
        }

        // Expired - remove from memory
        this._memoryCache.delete(key);
        logger.warn(`Token '${key}' expired in memory cache`);
      }

      // Fallback to sessionStorage (if memory was cleared)
      if (typeof sessionStorage !== "undefined") {
        const encrypted = sessionStorage.getItem(`vertice_secure_${key}`);
        if (encrypted) {
          try {
            const decrypted = this._simpleDecrypt(encrypted);
            const { value, expiresAt } = JSON.parse(decrypted);

            // Check expiration
            if (expiresAt > Date.now()) {
              // Restore to memory cache
              this._memoryCache.set(key, {
                value,
                expiresAt,
                storedAt: Date.now(),
              });
              logger.info(
                `Token '${key}' restored from sessionStorage to memory`,
              );
              return value;
            }

            // Expired - remove from sessionStorage
            sessionStorage.removeItem(`vertice_secure_${key}`);
            logger.warn(`Token '${key}' expired in sessionStorage`);
          } catch (parseError) {
            logger.error(
              "SecureTokenStore: Failed to parse sessionStorage data",
              parseError,
            );
            sessionStorage.removeItem(`vertice_secure_${key}`);
          }
        }
      }

      return null;
    } catch (error) {
      logger.error("SecureTokenStore: Failed to retrieve token", error);
      return null;
    }
  }

  /**
   * Remove a specific token
   */
  removeToken(key) {
    if (!key) {
      return false;
    }

    try {
      // Remove from memory
      this._memoryCache.delete(key);

      // Remove from sessionStorage
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.removeItem(`vertice_secure_${key}`);
      }

      logger.info(`Token '${key}' removed from secure storage`);
      return true;
    } catch (error) {
      logger.error("SecureTokenStore: Failed to remove token", error);
      return false;
    }
  }

  /**
   * Clear all tokens (on logout or window close)
   */
  clearAll() {
    try {
      // Clear memory
      this._memoryCache.clear();

      // Clear all vertice_secure_* keys from sessionStorage
      if (typeof sessionStorage !== "undefined") {
        const keysToRemove = [];
        for (let i = 0; i < sessionStorage.length; i++) {
          const key = sessionStorage.key(i);
          if (key && key.startsWith("vertice_secure_")) {
            keysToRemove.push(key);
          }
        }

        keysToRemove.forEach((key) => sessionStorage.removeItem(key));
        logger.info(
          `Cleared ${keysToRemove.length} tokens from sessionStorage`,
        );
      }

      logger.info("All tokens cleared from secure storage");
      return true;
    } catch (error) {
      logger.error("SecureTokenStore: Failed to clear all tokens", error);
      return false;
    }
  }

  /**
   * Check if a token exists and is valid
   */
  hasValidToken(key) {
    return this.getToken(key) !== null;
  }

  /**
   * Get token metadata (without exposing the token itself)
   */
  getTokenMetadata(key) {
    const memoryEntry = this._memoryCache.get(key);
    if (!memoryEntry) {
      return null;
    }

    const now = Date.now();
    const ttl = Math.max(0, memoryEntry.expiresAt - now);

    return {
      key,
      storedAt: memoryEntry.storedAt,
      expiresAt: memoryEntry.expiresAt,
      ttlSeconds: Math.floor(ttl / 1000),
      isExpired: ttl <= 0,
    };
  }

  /**
   * Simple encryption for sessionStorage
   * Note: This is NOT cryptographically secure - it's obfuscation
   * Real security comes from httpOnly cookies (future implementation)
   *
   * Boris Cherny: "Security through obscurity is not security,
   * but it's better than plain text"
   */
  _simpleEncrypt(text) {
    try {
      // Base64 encoding + simple XOR cipher
      const key = "vertice_xor_key_v1"; // In production, use env variable
      let encrypted = "";

      for (let i = 0; i < text.length; i++) {
        encrypted += String.fromCharCode(
          text.charCodeAt(i) ^ key.charCodeAt(i % key.length),
        );
      }

      return btoa(encrypted);
    } catch {
      return btoa(text); // Fallback to simple base64
    }
  }

  /**
   * Simple decryption for sessionStorage
   */
  _simpleDecrypt(encrypted) {
    try {
      const decoded = atob(encrypted);
      const key = "vertice_xor_key_v1";
      let decrypted = "";

      for (let i = 0; i < decoded.length; i++) {
        decrypted += String.fromCharCode(
          decoded.charCodeAt(i) ^ key.charCodeAt(i % key.length),
        );
      }

      return decrypted;
    } catch {
      return atob(encrypted); // Fallback to simple base64
    }
  }
}

// Singleton instance
const secureTokenStore = new SecureTokenStore();

export default secureTokenStore;
