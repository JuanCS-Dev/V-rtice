/**
 * useKonamiCode Hook - PAGANI Easter Egg
 * =======================================
 *
 * Classic Konami Code: ↑↑↓↓←→←→BA
 * Because every great app needs a secret ;)
 *
 * @example
 * useKonamiCode(() => {
 *   alert('🎉 You found the secret!');
 * });
 */

import { useEffect, useRef, useCallback } from "react";

const KONAMI_CODE = [
  "ArrowUp",
  "ArrowUp",
  "ArrowDown",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "ArrowLeft",
  "ArrowRight",
  "b",
  "a",
];

/**
 * Detect Konami Code sequence
 *
 * @param {Function} callback - Function to call when code is entered
 * @param {Object} options - Configuration options
 * @param {boolean} options.enabled - Whether detection is enabled
 * @param {number} options.timeout - Timeout between keys (ms)
 * @returns {void}
 */
export const useKonamiCode = (
  callback,
  { enabled = true, timeout = 1000 } = {},
) => {
  const sequence = useRef([]);
  const timeoutRef = useRef(null);
  const callbackRef = useRef(callback);

  // Keep callback ref updated
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  const resetSequence = useCallback(() => {
    sequence.current = [];
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const checkSequence = useCallback(() => {
    const currentSequence = sequence.current.join(",");
    const konamiSequence = KONAMI_CODE.join(",");

    if (currentSequence === konamiSequence) {
      // Success! Call the callback
      callbackRef.current();
      resetSequence();

      // Visual feedback
      document.body.style.animation = "konami-success 0.5s ease";
      setTimeout(() => {
        document.body.style.animation = "";
      }, 500);
    } else if (sequence.current.length >= KONAMI_CODE.length) {
      // Sequence too long, reset
      resetSequence();
    }
  }, [resetSequence]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event) => {
      // Ignore if typing in input fields
      if (
        event.target.tagName === "INPUT" ||
        event.target.tagName === "TEXTAREA" ||
        event.target.isContentEditable
      ) {
        return;
      }

      // Add key to sequence
      const key = event.key.toLowerCase();
      sequence.current.push(key);

      // Check if sequence matches
      checkSequence();

      // Reset sequence after timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(resetSequence, timeout);
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [enabled, timeout, checkSequence, resetSequence]);

  return { reset: resetSequence };
};

// Add CSS animation for success feedback
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = `
    @keyframes konami-success {
      0%, 100% { transform: scale(1); }
      25% { transform: scale(1.02) rotate(1deg); }
      50% { transform: scale(1.02) rotate(-1deg); }
      75% { transform: scale(1.02) rotate(1deg); }
    }
  `;
  document.head.appendChild(style);
}

export default useKonamiCode;
