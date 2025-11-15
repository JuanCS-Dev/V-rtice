/**
 * useRateLimit Hook
 *
 * Client-side rate limiting to prevent spam and abuse
 *
 * Features:
 * - Token bucket algorithm
 * - Per-action rate limits
 * - Cooldown periods
 * - Automatic reset
 * - Usage tracking
 *
 * Usage:
 * const { canExecute, execute, remaining, resetIn } = useRateLimit('api-call', {
 *   maxRequests: 10,
 *   windowMs: 60000 // 10 requests per minute
 * });
 */

import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Rate limiter using token bucket algorithm
 */
class RateLimiter {
  constructor(maxRequests, windowMs) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.tokens = maxRequests;
    this.lastRefill = Date.now();
  }

  refill() {
    const now = Date.now();
    const timePassed = now - this.lastRefill;
    const tokensToAdd = Math.floor((timePassed / this.windowMs) * this.maxRequests);

    if (tokensToAdd > 0) {
      this.tokens = Math.min(this.maxRequests, this.tokens + tokensToAdd);
      this.lastRefill = now;
    }
  }

  tryConsume() {
    this.refill();

    if (this.tokens > 0) {
      this.tokens--;
      return true;
    }

    return false;
  }

  getRemaining() {
    this.refill();
    return this.tokens;
  }

  getResetTime() {
    if (this.tokens >= this.maxRequests) {
      return 0;
    }

    const tokensNeeded = this.maxRequests - this.tokens;
    const timePerToken = this.windowMs / this.maxRequests;
    return Math.ceil(tokensNeeded * timePerToken);
  }
}

// Global rate limiters map
const rateLimiters = new Map();

/**
 * Hook for rate limiting actions
 *
 * @param {string} key - Unique identifier for this rate limit
 * @param {Object} options - Configuration options
 * @param {number} options.maxRequests - Maximum requests allowed
 * @param {number} options.windowMs - Time window in milliseconds
 * @param {Function} options.onLimitExceeded - Callback when limit exceeded
 * @returns {Object} Rate limit state and functions
 */
export const useRateLimit = (key, options = {}) => {
  const {
    maxRequests = 10,
    windowMs = 60000, // 1 minute
    onLimitExceeded = null
  } = options;

  // Get or create rate limiter
  if (!rateLimiters.has(key)) {
    rateLimiters.set(key, new RateLimiter(maxRequests, windowMs));
  }

  const limiter = rateLimiters.get(key);

  const [state, setState] = useState({
    remaining: limiter.getRemaining(),
    resetIn: limiter.getResetTime()
  });

  const updateIntervalRef = useRef(null);

  // Update state periodically
  useEffect(() => {
    updateIntervalRef.current = setInterval(() => {
      setState({
        remaining: limiter.getRemaining(),
        resetIn: limiter.getResetTime()
      });
    }, 1000);

    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, [limiter]);

  /**
   * Check if action can be executed
   */
  const canExecute = useCallback(() => {
    return limiter.getRemaining() > 0;
  }, [limiter]);

  /**
   * Execute action with rate limiting
   */
  const execute = useCallback(async (fn) => {
    if (!limiter.tryConsume()) {
      // Rate limit exceeded
      if (onLimitExceeded) {
        onLimitExceeded({
          key,
          remaining: 0,
          resetIn: limiter.getResetTime()
        });
      }

      throw new Error(`Rate limit exceeded for "${key}". Try again in ${Math.ceil(limiter.getResetTime() / 1000)}s`);
    }

    // Update state
    setState({
      remaining: limiter.getRemaining(),
      resetIn: limiter.getResetTime()
    });

    // Execute function
    return await fn();
  }, [limiter, key, onLimitExceeded]);

  /**
   * Reset rate limiter
   */
  const reset = useCallback(() => {
    limiter.tokens = limiter.maxRequests;
    limiter.lastRefill = Date.now();

    setState({
      remaining: limiter.getRemaining(),
      resetIn: 0
    });
  }, [limiter]);

  return {
    canExecute,
    execute,
    remaining: state.remaining,
    resetIn: state.resetIn,
    reset
  };
};

/**
 * Clear all rate limiters (useful for testing)
 */
export const clearAllRateLimiters = () => {
  rateLimiters.clear();
};

/**
 * Get rate limiter stats
 */
export const getRateLimiterStats = (key) => {
  const limiter = rateLimiters.get(key);
  if (!limiter) return null;

  return {
    remaining: limiter.getRemaining(),
    resetIn: limiter.getResetTime(),
    maxRequests: limiter.maxRequests,
    windowMs: limiter.windowMs
  };
};
