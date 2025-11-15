/**
 * Custom hook for Module Navigation shortcuts
 * Enables Alt+[1-5] shortcuts for quick module switching
 */
import { useEffect, useCallback } from "react";

export const useModuleNavigation = (setCurrentView) => {
  const handleKeyPress = useCallback(
    (event) => {
      // Alt + Number shortcuts
      if (event.altKey) {
        const keyMap = {
          1: "main",
          2: "cyber",
          3: "osint",
          4: "terminal",
          5: "admin",
        };

        const view = keyMap[event.key];
        if (view) {
          event.preventDefault();
          setCurrentView(view);

          // Announce to screen readers
          const announcement = document.createElement("div");
          announcement.setAttribute("role", "status");
          announcement.setAttribute("aria-live", "polite");
          announcement.className = "sr-only";
          announcement.textContent = `Navegando para módulo ${view}`;
          document.body.appendChild(announcement);
          setTimeout(() => announcement.remove(), 1000);
        }
      }
    },
    [setCurrentView],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [handleKeyPress]);

  return null;
};
