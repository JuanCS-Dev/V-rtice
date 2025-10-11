/**
 * useClickOutside Hook - Detect clicks outside element
 * ====================================================
 * 
 * PAGANI Quality: Robust, performant, accessible
 */

import { useEffect, useRef } from 'react';

/**
 * Hook to detect clicks outside a referenced element
 * 
 * @param {Function} handler - Callback when click outside occurs
 * @param {boolean} enabled - Whether detection is enabled
 * @returns {Object} ref - Ref to attach to element
 * 
 * @example
 * const ref = useClickOutside(() => setIsOpen(false));
 * return <div ref={ref}>Content</div>
 */
export const useClickOutside = (handler, enabled = true) => {
  const ref = useRef(null);
  const handlerRef = useRef(handler);

  // Keep handler ref updated without re-running effect
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    if (!enabled) return;

    const handleClickOutside = (event) => {
      // Ignore if clicking on the ref element or its children
      if (ref.current && !ref.current.contains(event.target)) {
        handlerRef.current(event);
      }
    };

    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        handlerRef.current(event);
      }
    };

    // Use capture phase for better reliability
    document.addEventListener('mousedown', handleClickOutside, true);
    document.addEventListener('touchstart', handleClickOutside, true);
    document.addEventListener('keydown', handleEscapeKey, true);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside, true);
      document.removeEventListener('touchstart', handleClickOutside, true);
      document.removeEventListener('keydown', handleEscapeKey, true);
    };
  }, [enabled]);

  return ref;
};

export default useClickOutside;
