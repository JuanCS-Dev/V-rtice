import React, { createContext, useContext, useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useNotificationStore } from "@/stores/notificationStore";
import { post } from "@/lib/api/client";
import { wsManager } from "@/lib/websocket/WebSocketManager";
import type { User, AuthTokens, LoginCredentials } from "@/types";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const {
    user,
    isAuthenticated,
    login: setAuth,
    logout: clearAuth,
  } = useAuthStore();
  const { addNotification } = useNotificationStore();
  const [isLoading, setIsLoading] = React.useState(false);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);

    try {
      // MOCK AUTH: Backend not running yet - use mock authentication
      const useMockAuth = import.meta.env.VITE_MOCK_AUTH !== "false"; // Default to mock unless explicitly disabled

      if (useMockAuth) {
        // Simulate network delay
        await new Promise((resolve) => setTimeout(resolve, 800));

        // Mock tokens
        const mockTokens: AuthTokens = {
          access_token: "mock_jwt_token_" + Date.now(),
          token_type: "bearer",
          expires_in: 3600,
          refresh_token: "mock_refresh_token_" + Date.now(),
        };

        // Mock user based on username
        const isAdmin = credentials.username.toLowerCase().includes("admin");
        const mockUser: User = {
          id: crypto.randomUUID(),
          username: credentials.username,
          email: `${credentials.username}@vertice.local`,
          roles: isAdmin ? ["admin", "analyst", "offensive"] : ["analyst"],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        // Update auth store
        setAuth(mockUser, mockTokens);

        // Skip WebSocket connection in mock mode
        // wsManager.connect(mockTokens.access_token);

        addNotification({
          type: "success",
          title: "Welcome back!",
          message: `Logged in as ${mockUser.username} (MOCK MODE)`,
        });

        setIsLoading(false);
        return;
      }

      // Real backend authentication (when backend is running)
      const tokens = await post<AuthTokens>("/api/auth/login", {
        username: credentials.username,
        password: credentials.password,
      });

      // Get user profile
      const userProfile = await post<User>("/api/auth/me", undefined, {
        headers: {
          Authorization: `Bearer ${tokens.access_token}`,
        },
      });

      // Update auth store
      setAuth(userProfile, tokens);

      // Connect WebSocket
      wsManager.connect(tokens.access_token);

      addNotification({
        type: "success",
        title: "Welcome back!",
        message: `Logged in as ${userProfile.username}`,
      });
    } catch (error) {
      addNotification({
        type: "error",
        title: "Login failed",
        message: "Invalid credentials",
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuth();
    wsManager.disconnect();
    addNotification({
      type: "info",
      title: "Logged out",
      message: "You have been logged out successfully",
    });
  };

  // Auto-connect WebSocket on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      const { tokens } = useAuthStore.getState();
      if (tokens?.access_token) {
        wsManager.connect(tokens.access_token);
      }
    }

    return () => {
      wsManager.disconnect();
    };
  }, [isAuthenticated, user]);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
