/**
 * Safe Storage Utilities
 * Boris Cherny Pattern: Defensive localStorage/sessionStorage access
 *
 * Prevents crashes from:
 * - Corrupted JSON
 * - QuotaExceededError
 * - Disabled storage
 * - SecurityError (sandboxed iframes)
 *
 * Governed by: Constituição Vértice v2.7
 */

import { safeJSONParse } from "./security";
import logger from "./logger";

/**
 * Check if storage is available
 * @param {Storage} storage - localStorage or sessionStorage
 * @returns {boolean} True if storage works
 */
const isStorageAvailable = (storage) => {
  try {
    const test = "__storage_test__";
    storage.setItem(test, test);
    storage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};

/**
 * Safely get item from storage with JSON parsing
 * @param {string} key - Storage key
 * @param {*} defaultValue - Default value if not found or invalid
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {*} Parsed value or default
 *
 * @example
 * safeGetItem('user', null) // => {name: 'John'} or null
 * safeGetItem('count', 0) // => 42 or 0
 * safeGetItem('corrupted', {}) // => {} (if JSON.parse fails)
 */
export const safeGetItem = (
  key,
  defaultValue = null,
  storage = localStorage,
) => {
  if (!isStorageAvailable(storage)) {
    logger.warn(`Storage not available for key: ${key}`);
    return defaultValue;
  }

  try {
    const item = storage.getItem(key);

    if (item === null) {
      return defaultValue;
    }

    // Try to parse as JSON
    const parsed = safeJSONParse(item);

    // If parsing returns null (invalid JSON), check if it was intentional
    if (parsed === null && item !== "null") {
      // Item is a plain string, not JSON
      return item;
    }

    return parsed ?? defaultValue;
  } catch (error) {
    logger.error(`Error reading from storage (key: ${key}):`, error);
    return defaultValue;
  }
};

/**
 * Safely set item in storage with JSON serialization
 * @param {string} key - Storage key
 * @param {*} value - Value to store (will be JSON.stringified)
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {boolean} True if successful
 *
 * @example
 * safeSetItem('user', {name: 'John'}) // => true
 * safeSetItem('count', 42) // => true
 * safeSetItem('text', 'hello') // => true
 */
export const safeSetItem = (key, value, storage = localStorage) => {
  if (!isStorageAvailable(storage)) {
    logger.warn(`Storage not available, cannot set key: ${key}`);
    return false;
  }

  try {
    const serialized = JSON.stringify(value);
    storage.setItem(key, serialized);
    return true;
  } catch (error) {
    if (error.name === "QuotaExceededError") {
      logger.error(`Storage quota exceeded while setting key: ${key}`);

      // Attempt to clear old items to make space
      try {
        // Get all keys and sort by age (if they have timestamps)
        const keys = Object.keys(storage);
        const oldestKeys = keys.slice(0, Math.floor(keys.length / 4)); // Remove oldest 25%

        oldestKeys.forEach((k) => storage.removeItem(k));

        // Retry after cleanup
        storage.setItem(key, JSON.stringify(value));
        logger.info(
          `Storage cleanup successful, retry succeeded for key: ${key}`,
        );
        return true;
      } catch (retryError) {
        logger.error(`Storage cleanup failed:`, retryError);
        return false;
      }
    }

    logger.error(`Error writing to storage (key: ${key}):`, error);
    return false;
  }
};

/**
 * Safely remove item from storage
 * @param {string} key - Storage key
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {boolean} True if successful
 *
 * @example
 * safeRemoveItem('user') // => true
 */
export const safeRemoveItem = (key, storage = localStorage) => {
  if (!isStorageAvailable(storage)) {
    logger.warn(`Storage not available, cannot remove key: ${key}`);
    return false;
  }

  try {
    storage.removeItem(key);
    return true;
  } catch (error) {
    logger.error(`Error removing from storage (key: ${key}):`, error);
    return false;
  }
};

/**
 * Safely clear all items from storage
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {boolean} True if successful
 *
 * @example
 * safeClearAll() // => true
 */
export const safeClearAll = (storage = localStorage) => {
  if (!isStorageAvailable(storage)) {
    logger.warn(`Storage not available, cannot clear`);
    return false;
  }

  try {
    storage.clear();
    return true;
  } catch (error) {
    logger.error(`Error clearing storage:`, error);
    return false;
  }
};

/**
 * Get all keys from storage
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {string[]} Array of keys
 *
 * @example
 * getAllKeys() // => ['user', 'settings', 'cache']
 */
export const getAllKeys = (storage = localStorage) => {
  if (!isStorageAvailable(storage)) {
    return [];
  }

  try {
    return Object.keys(storage);
  } catch (error) {
    logger.error(`Error getting storage keys:`, error);
    return [];
  }
};

/**
 * Get storage size (approximate, in bytes)
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {number} Approximate size in bytes
 *
 * @example
 * getStorageSize() // => 1024 (1KB)
 */
export const getStorageSize = (storage = localStorage) => {
  if (!isStorageAvailable(storage)) {
    return 0;
  }

  try {
    let size = 0;
    for (let key in storage) {
      if (storage.hasOwnProperty(key)) {
        size += storage[key].length + key.length;
      }
    }
    return size;
  } catch (error) {
    logger.error(`Error calculating storage size:`, error);
    return 0;
  }
};

/**
 * Check if storage is near quota
 * @param {number} threshold - Warning threshold (0-1, default: 0.8 = 80%)
 * @param {Storage} storage - Storage object (default: localStorage)
 * @returns {boolean} True if near quota
 *
 * @example
 * isStorageNearQuota(0.9) // => true if > 90% full
 */
export const isStorageNearQuota = (threshold = 0.8, storage = localStorage) => {
  try {
    const size = getStorageSize(storage);
    const quota = 5 * 1024 * 1024; // Assume 5MB quota (typical for localStorage)
    return size / quota > threshold;
  } catch {
    return false;
  }
};

// SessionStorage variants
export const safeGetSessionItem = (key, defaultValue = null) =>
  safeGetItem(key, defaultValue, sessionStorage);

export const safeSetSessionItem = (key, value) =>
  safeSetItem(key, value, sessionStorage);

export const safeRemoveSessionItem = (key) =>
  safeRemoveItem(key, sessionStorage);

export const safeClearSession = () => safeClearAll(sessionStorage);

export default {
  safeGetItem,
  safeSetItem,
  safeRemoveItem,
  safeClearAll,
  getAllKeys,
  getStorageSize,
  isStorageNearQuota,
  safeGetSessionItem,
  safeSetSessionItem,
  safeRemoveSessionItem,
  safeClearSession,
};
