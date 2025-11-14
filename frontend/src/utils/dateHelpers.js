/**
 * Date Utilities - Safe date handling with fallbacks
 * Prevents "Invalid Date" from appearing in UI
 */

/**
 * Safely create Date object with fallback
 * @param {any} value - Date string, timestamp, or Date object
 * @param {Date|null} fallback - Fallback date (default: null)
 * @returns {Date|null} Valid Date or fallback
 */
export const safeDate = (value, fallback = null) => {
  if (!value) return fallback;

  try {
    const date = new Date(value);
    return isNaN(date.getTime()) ? fallback : date;
  } catch {
    return fallback;
  }
};

/**
 * Format date safely with fallback string
 * @param {any} value - Date to format
 * @param {object} options - Intl.DateTimeFormat options
 * @param {string} fallback - Fallback string (default: 'N/A')
 * @returns {string} Formatted date or fallback
 */
export const formatDate = (
  value,
  options = { dateStyle: "medium" },
  fallback = "N/A",
) => {
  const date = safeDate(value);
  if (!date) return fallback;

  try {
    return new Intl.DateTimeFormat("pt-BR", options).format(date);
  } catch {
    return fallback;
  }
};

/**
 * Format datetime safely
 * @param {any} value - Date to format
 * @param {string} fallback - Fallback string (default: 'N/A')
 * @returns {string} Formatted datetime or fallback
 */
export const formatDateTime = (value, fallback = "N/A") => {
  return formatDate(
    value,
    { dateStyle: "medium", timeStyle: "short" },
    fallback,
  );
};

/**
 * Format time safely
 * @param {any} value - Date to format
 * @param {string} fallback - Fallback string (default: 'N/A')
 * @returns {string} Formatted time or fallback
 */
export const formatTime = (value, fallback = "N/A") => {
  return formatDate(value, { timeStyle: "medium" }, fallback);
};

/**
 * Get relative time string (e.g., "2 hours ago")
 * @param {any} value - Date to format
 * @param {string} fallback - Fallback string (default: 'N/A')
 * @returns {string} Relative time or fallback
 */
export const getRelativeTime = (value, fallback = "N/A") => {
  const date = safeDate(value);
  if (!date) return fallback;

  try {
    const now = Date.now();
    const diff = now - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d atrás`;
    if (hours > 0) return `${hours}h atrás`;
    if (minutes > 0) return `${minutes}m atrás`;
    return `${seconds}s atrás`;
  } catch {
    return fallback;
  }
};

/**
 * Check if date is valid
 * @param {any} value - Date to check
 * @returns {boolean} True if valid
 */
export const isValidDate = (value) => {
  return safeDate(value) !== null;
};

/**
 * Get timestamp safely
 * @param {any} value - Date to convert
 * @param {number|null} fallback - Fallback timestamp (default: null)
 * @returns {number|null} Timestamp or fallback
 */
export const getTimestamp = (value, fallback = null) => {
  const date = safeDate(value);
  return date ? date.getTime() : fallback;
};
