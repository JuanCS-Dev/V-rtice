/**
 * useFocusTrap Hook
 *
 * Trap focus within a container (modals, dropdowns, dialogs)
 * WCAG 2.1 AA Compliance - No Keyboard Trap (2.1.2)
 *
 * Features:
 * - Trap focus within container
 * - Return focus on unmount
 * - Escape key to release trap
 * - Auto-focus first focusable element
 *
 * @example
 * const trapRef = useFocusTrap({
 *   active: isModalOpen,
 *   onEscape: closeModal
 * });
 *
 * return <div ref={trapRef}>...</div>;
 */

import { useRef, useEffect, useCallback } from "react";

const FOCUSABLE_SELECTORS = [
  "a[href]",
  "area[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "button:not([disabled])",
  "iframe",
  "object",
  "embed",
  "[contenteditable]",
  '[tabindex]:not([tabindex^="-"])',
].join(",");

export const useFocusTrap = ({
  active = true,
  autoFocus = true,
  returnFocus = true,
  onEscape = null,
  allowOutsideClick = false,
}) => {
  const containerRef = useRef(null);
  const previousActiveElement = useRef(null);

  // Get all focusable elements
  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];

    const elements = Array.from(
      containerRef.current.querySelectorAll(FOCUSABLE_SELECTORS),
    );

    return elements.filter((el) => {
      return (
        el.offsetWidth > 0 &&
        el.offsetHeight > 0 &&
        !el.hasAttribute("disabled") &&
        !el.hasAttribute("hidden")
      );
    });
  }, []);

  // Handle Tab key navigation
  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "Escape" && onEscape) {
        event.preventDefault();
        onEscape();
        return;
      }

      if (event.key !== "Tab") return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Shift + Tab (backwards)
      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      }
      // Tab (forwards)
      else {
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    },
    [getFocusableElements, onEscape],
  );

  // Handle outside clicks
  const handleClickOutside = useCallback(
    (event) => {
      if (
        allowOutsideClick &&
        containerRef.current &&
        !containerRef.current.contains(event.target)
      ) {
        if (onEscape) onEscape();
      }
    },
    [allowOutsideClick, onEscape],
  );

  // Activate trap
  useEffect(() => {
    if (!active) return;

    // Save current focus
    previousActiveElement.current = document.activeElement;

    // Auto-focus first element
    let timeoutId;
    if (autoFocus) {
      const focusableElements = getFocusableElements();
      if (focusableElements.length > 0) {
        // Small delay to ensure DOM is ready
        timeoutId = setTimeout(() => {
          focusableElements[0]?.focus();
        }, 10);
      }
    }

    // Add event listeners
    document.addEventListener("keydown", handleKeyDown);
    if (allowOutsideClick) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    // Cleanup
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      document.removeEventListener("keydown", handleKeyDown);
      if (allowOutsideClick) {
        document.removeEventListener("mousedown", handleClickOutside);
      }

      // Return focus
      if (returnFocus && previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    };
  }, [
    active,
    autoFocus,
    returnFocus,
    allowOutsideClick,
    handleKeyDown,
    handleClickOutside,
    getFocusableElements,
  ]);

  return containerRef;
};

export default useFocusTrap;
