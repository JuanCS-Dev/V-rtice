/**
 * Debounce Utility - Boris Cherny Standard
 *
 * Prevents race conditions on rapid refetch calls
 *
 * GAP #70 FIX: Add debouncing to manual refetch functions
 *
 * Usage:
 * const debouncedRefetch = debounce(refetch, 300);
 *
 * // In component
 * onClick={debouncedRefetch} // Won't fire more than once per 300ms
 */

import logger from "./logger";

/**
 * Creates a debounced function that delays invoking func until after wait milliseconds
 * have elapsed since the last time the debounced function was invoked.
 *
 * @param {Function} func - The function to debounce
 * @param {number} wait - The number of milliseconds to delay
 * @param {Object} options - Options object
 * @param {boolean} options.leading - Invoke on the leading edge of the timeout
 * @param {boolean} options.trailing - Invoke on the trailing edge of the timeout
 * @returns {Function} Returns the new debounced function
 */
export function debounce(func, wait = 300, options = {}) {
  const { leading = false, trailing = true } = options;

  let timeoutId = null;
  let lastArgs = null;
  let lastThis = null;
  let lastCallTime = 0;

  function invokeFunc() {
    const args = lastArgs;
    const thisArg = lastThis;

    lastArgs = lastThis = null;
    return func.apply(thisArg, args);
  }

  function leadingEdge() {
    lastCallTime = Date.now();
    if (leading) {
      return invokeFunc();
    }
  }

  function trailingEdge() {
    timeoutId = null;
    if (trailing && lastArgs) {
      return invokeFunc();
    }
    lastArgs = lastThis = null;
  }

  function cancel() {
    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }
    lastCallTime = 0;
    lastArgs = lastThis = timeoutId = null;
  }

  function flush() {
    return timeoutId === null ? undefined : trailingEdge();
  }

  function debounced(...args) {
    const time = Date.now();
    const isInvoking = shouldInvoke(time);

    lastArgs = args;
    lastThis = this;
    lastCallTime = time;

    if (isInvoking) {
      if (timeoutId === null) {
        return leadingEdge();
      }
    }

    if (timeoutId !== null) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(trailingEdge, wait);
  }

  function shouldInvoke(time) {
    const timeSinceLastCall = time - lastCallTime;
    return lastCallTime === 0 || timeSinceLastCall >= wait;
  }

  debounced.cancel = cancel;
  debounced.flush = flush;

  return debounced;
}

/**
 * Creates a throttled function that only invokes func at most once per every wait milliseconds.
 *
 * @param {Function} func - The function to throttle
 * @param {number} wait - The number of milliseconds to throttle invocations to
 * @returns {Function} Returns the new throttled function
 */
export function throttle(func, wait = 300) {
  return debounce(func, wait, { leading: true, trailing: false });
}

/**
 * Debounce for React Query refetch functions
 * Prevents race conditions when users rapidly click refresh buttons
 *
 * @param {Function} refetchFn - React Query refetch function
 * @param {number} wait - Debounce delay in milliseconds
 * @returns {Function} Debounced refetch function
 */
// Boris Cherny Standard - GAP #83: Replace console.error with logger
export function debounceRefetch(refetchFn, wait = 300) {
  return debounce(
    async () => {
      try {
        await refetchFn();
      } catch (error) {
        // React Query handles errors, just prevent throw
        logger.error("[Debounce] Refetch error:", error);
      }
    },
    wait,
    { leading: true, trailing: false }, // Execute immediately, ignore rapid subsequent calls
  );
}

export default debounce;
