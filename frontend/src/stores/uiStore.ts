import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIState {
  sidebarOpen: boolean;
  theme: "light" | "dark";
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleTheme: () => void;
  setTheme: (theme: "light" | "dark") => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "light",

      toggleSidebar: () =>
        set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      toggleTheme: () =>
        set((state) => {
          const newTheme = state.theme === "light" ? "dark" : "light";
          // Update document class for dark mode
          if (typeof document !== "undefined") {
            document.documentElement.classList.toggle(
              "dark",
              newTheme === "dark",
            );
          }
          return { theme: newTheme };
        }),

      setTheme: (theme) => {
        set({ theme });
        if (typeof document !== "undefined") {
          document.documentElement.classList.toggle("dark", theme === "dark");
        }
      },
    }),
    {
      name: "ui-storage",
      onRehydrateStorage: () => (state) => {
        // Apply theme on load
        if (state && typeof document !== "undefined") {
          document.documentElement.classList.toggle(
            "dark",
            state.theme === "dark",
          );
        }
      },
    },
  ),
);
