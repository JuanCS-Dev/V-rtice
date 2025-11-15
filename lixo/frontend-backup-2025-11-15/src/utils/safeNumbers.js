/**
 * Safe Number Utilities
 * Boris Cherny Pattern: Type-safe number parsing with validation
 *
 * Prevents NaN propagation and provides sensible defaults
 * Governed by: Constituição Vértice v2.7
 */

/**
 * Safe parseFloat with validation and clamping
 * @param {*} value - Value to parse
 * @param {number} defaultValue - Default value if parsing fails
 * @param {number} min - Minimum allowed value
 * @param {number} max - Maximum allowed value
 * @returns {number} Parsed and validated number
 *
 * @example
 * safeParseFloat("3.14", 0, 0, 10) // => 3.14
 * safeParseFloat("abc", 0, 0, 10) // => 0
 * safeParseFloat("999", 0, 0, 10) // => 10 (clamped)
 */
export const safeParseFloat = (
  value,
  defaultValue = 0,
  min = -Infinity,
  max = Infinity,
) => {
  const num = parseFloat(value);

  if (isNaN(num)) {
    return defaultValue;
  }

  // Clamp to [min, max] range
  return Math.max(min, Math.min(max, num));
};

/**
 * Safe parseInt with validation
 * @param {*} value - Value to parse
 * @param {number} defaultValue - Default value if parsing fails
 * @param {number} radix - Number base (default: 10)
 * @returns {number} Parsed integer or default
 *
 * @example
 * safeParseInt("42", 0) // => 42
 * safeParseInt("abc", 0) // => 0
 * safeParseInt("ff", 0, 16) // => 255
 */
export const safeParseInt = (value, defaultValue = 0, radix = 10) => {
  const num = parseInt(value, radix);
  return isNaN(num) ? defaultValue : num;
};

/**
 * Safe division (avoids division by zero)
 * @param {number} numerator - Dividend
 * @param {number} denominator - Divisor
 * @param {number} defaultValue - Value to return if denominator is zero
 * @returns {number} Result or default value
 *
 * @example
 * safeDivide(10, 2) // => 5
 * safeDivide(10, 0) // => 0
 * safeDivide(10, 0, -1) // => -1
 */
export const safeDivide = (numerator, denominator, defaultValue = 0) => {
  if (denominator === 0) {
    return defaultValue;
  }
  return numerator / denominator;
};

/**
 * Clamp a number to a range
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 *
 * @example
 * clamp(5, 0, 10) // => 5
 * clamp(-5, 0, 10) // => 0
 * clamp(15, 0, 10) // => 10
 */
export const clamp = (value, min, max) => {
  return Math.max(min, Math.min(max, value));
};

/**
 * Check if value is a valid number
 * @param {*} value - Value to check
 * @returns {boolean} True if valid number
 *
 * @example
 * isValidNumber(42) // => true
 * isValidNumber(NaN) // => false
 * isValidNumber(Infinity) // => false
 * isValidNumber("42") // => false
 */
export const isValidNumber = (value) => {
  return typeof value === "number" && !isNaN(value) && isFinite(value);
};

/**
 * Safe percentage calculation
 * @param {number} value - Current value
 * @param {number} total - Total value
 * @param {number} decimals - Number of decimal places
 * @returns {number} Percentage (0-100) or 0 if invalid
 *
 * @example
 * safePercentage(25, 100) // => 25
 * safePercentage(1, 3, 2) // => 33.33
 * safePercentage(10, 0) // => 0
 */
export const safePercentage = (value, total, decimals = 0) => {
  if (total === 0 || !isValidNumber(value) || !isValidNumber(total)) {
    return 0;
  }

  const percentage = (value / total) * 100;
  return decimals > 0
    ? parseFloat(percentage.toFixed(decimals))
    : Math.round(percentage);
};

/**
 * Format number with fallback
 * @param {*} value - Value to format
 * @param {string} fallback - Fallback string if invalid
 * @param {number} decimals - Decimal places
 * @returns {string} Formatted number or fallback
 *
 * @example
 * formatNumber(3.14159, 'N/A', 2) // => "3.14"
 * formatNumber(NaN, 'N/A') // => "N/A"
 * formatNumber(null, 'N/A') // => "N/A"
 */
export const formatNumber = (value, fallback = "N/A", decimals = 0) => {
  const num = Number(value);

  if (!isValidNumber(num)) {
    return fallback;
  }

  return decimals > 0 ? num.toFixed(decimals) : num.toString();
};

export default {
  safeParseFloat,
  safeParseInt,
  safeDivide,
  clamp,
  isValidNumber,
  safePercentage,
  formatNumber,
};
