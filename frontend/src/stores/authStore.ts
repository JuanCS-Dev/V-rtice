import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User, AuthTokens } from "@/types";

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,

      login: (user, tokens) => {
        set({ user, tokens, isAuthenticated: true });

        // Broadcast login to other tabs
        window.dispatchEvent(
          new CustomEvent("auth:login", { detail: { user, tokens } }),
        );
      },

      logout: () => {
        set({ user: null, tokens: null, isAuthenticated: false });

        // Broadcast logout to other tabs
        window.dispatchEvent(new CustomEvent("auth:logout"));
      },

      updateUser: (userData) => {
        set((state) => ({
          user: state.user ? { ...state.user, ...userData } : null,
        }));
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);

// Cross-tab sync
if (typeof window !== "undefined") {
  window.addEventListener("auth:login", ((event: CustomEvent) => {
    const { user, tokens } = event.detail;
    useAuthStore.setState({ user, tokens, isAuthenticated: true });
  }) as EventListener);

  window.addEventListener("auth:logout", () => {
    useAuthStore.setState({ user: null, tokens: null, isAuthenticated: false });
  });
}
