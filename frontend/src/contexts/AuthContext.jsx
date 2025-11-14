import { API_BASE_URL } from "@/config/api";
/* eslint-disable react-refresh/only-export-components */
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  useCallback,
} from "react";
import logger from "@/utils/logger";
import { safeJSONParse } from "@/utils/security";
import { setTokenRefreshHandler } from "@/api/client";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

/**
 * AuthProvider - Sistema de autenticação integrado com vertice-terminal
 * Usa o sistema de roles do CLI (super_admin, admin, analyst, viewer)
 *
 * Boris Cherny Pattern: Automatic token refresh with secure storage
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(
    localStorage.getItem("vertice_auth_token"),
  );

  // Refs for auto-refresh timer (doesn't trigger re-renders)
  const refreshTimerRef = useRef(null);
  const isRefreshingRef = useRef(false);

  // Super Admin do sistema - configurado via environment variable
  const SUPER_ADMIN = import.meta.env.VITE_SUPER_ADMIN_EMAIL || "";

  // Roles e permissões (sincronizado com vertice-terminal)
  const ROLES = {
    super_admin: {
      email: SUPER_ADMIN,
      permissions: ["*"], // Todas as permissões
      level: 100,
    },
    admin: {
      permissions: ["read", "write", "execute", "manage_users", "offensive"],
      level: 80,
    },
    analyst: {
      permissions: ["read", "write", "execute"],
      level: 50,
    },
    viewer: {
      permissions: ["read"],
      level: 10,
    },
  };

  // Check if user is authenticated on app start
  useEffect(() => {
    const checkAuth = () => {
      const storedUser = localStorage.getItem("vertice_user");
      const storedToken = localStorage.getItem("vertice_auth_token");
      const tokenExpiry = localStorage.getItem("vertice_token_expiry");

      if (storedToken && storedUser && tokenExpiry) {
        const expiryDate = new Date(tokenExpiry);

        if (new Date() < expiryDate) {
          const userData = safeJSONParse(storedUser);
          if (!userData) {
            clearAuthData();
            setLoading(false);
            return;
          }
          setUser(userData);
          setToken(storedToken);
        } else {
          // Token expirado, limpar
          clearAuthData();
        }
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  const clearAuthData = () => {
    localStorage.removeItem("vertice_auth_token");
    localStorage.removeItem("vertice_user");
    localStorage.removeItem("vertice_token_expiry");
    localStorage.removeItem("vertice_refresh_token");
    setToken(null);
    setUser(null);

    // Clear refresh timer
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  };

  /**
   * Setup auto-refresh timer
   * Refreshes token 5 minutes before expiry (Boris Cherny pattern)
   */
  const scheduleTokenRefresh = useCallback((expiresIn) => {
    // Clear existing timer
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }

    // Schedule refresh 5 minutes (300s) before expiry
    const refreshDelay = Math.max((expiresIn - 300) * 1000, 60000); // Min 1 minute

    logger.info(
      `Token refresh scheduled in ${Math.floor(refreshDelay / 1000)}s`,
    );

    refreshTimerRef.current = setTimeout(async () => {
      logger.info("Auto-refresh timer triggered");
      await refreshAuthToken();
    }, refreshDelay);
  }, []);

  /**
   * Refresh authentication token
   * Boris Cherny Pattern: Idempotent, concurrency-safe
   */
  const refreshAuthToken = useCallback(async () => {
    // Prevent concurrent refreshes
    if (isRefreshingRef.current) {
      logger.info("Token refresh already in progress");
      return false;
    }

    isRefreshingRef.current = true;

    try {
      const refreshToken = localStorage.getItem("vertice_refresh_token");

      if (!refreshToken) {
        logger.warn("No refresh token available");
        isRefreshingRef.current = false;
        return false;
      }

      const AUTH_SERVICE_URL =
        import.meta.env.VITE_AUTH_SERVICE_URL || API_BASE_URL;

      logger.info("Attempting token refresh...");
      const response = await fetch(`${AUTH_SERVICE_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        logger.error("Token refresh failed:", response.status);
        clearAuthData();
        isRefreshingRef.current = false;
        return false;
      }

      const data = await response.json();

      // Update token and expiry
      const newToken = data.access_token;
      const expiresIn = data.expires_in || 3600;

      localStorage.setItem("vertice_auth_token", newToken);

      const expiryDate = new Date();
      expiryDate.setSeconds(expiryDate.getSeconds() + expiresIn);
      localStorage.setItem("vertice_token_expiry", expiryDate.toISOString());

      // Update refresh token if provided
      if (data.refresh_token) {
        localStorage.setItem("vertice_refresh_token", data.refresh_token);
      }

      setToken(newToken);

      // Schedule next refresh
      scheduleTokenRefresh(expiresIn);

      logger.info("Token refreshed successfully");
      isRefreshingRef.current = false;
      return true;
    } catch (error) {
      logger.error("Token refresh error:", error);
      clearAuthData();
      isRefreshingRef.current = false;
      return false;
    }
  }, [scheduleTokenRefresh]);

  /**
   * Register refresh handler with API client on mount
   * Boris Cherny Pattern: Loose coupling via dependency injection
   */
  useEffect(() => {
    setTokenRefreshHandler(refreshAuthToken);

    return () => {
      setTokenRefreshHandler(null);
      if (refreshTimerRef.current) {
        clearTimeout(refreshTimerRef.current);
      }
    };
  }, [refreshAuthToken]);

  /**
   * Login usando Google OAuth2
   * Conecta com auth_service backend REAL
   */
  const login = async (email, useMock = false) => {
    try {
      // Se explicitamente usar mock (desenvolvimento)
      if (useMock) {
        const role = email === SUPER_ADMIN ? "super_admin" : "analyst";
        const userData = {
          email: email,
          name:
            email.split("@")[0].charAt(0).toUpperCase() +
            email.split("@")[0].slice(1),
          picture: "",
          role: role,
          authenticated_at: new Date().toISOString(),
          permissions: ROLES[role].permissions,
          level: ROLES[role].level,
        };

        const authToken = `ya29.mock_token_for_${email}`;
        const mockRefreshToken = `refresh.mock_${email}`;
        const expiresIn = 3600; // 1 hour
        const expiryDate = new Date();
        expiryDate.setHours(expiryDate.getHours() + 1);

        localStorage.setItem("vertice_auth_token", authToken);
        localStorage.setItem("vertice_user", JSON.stringify(userData));
        localStorage.setItem("vertice_token_expiry", expiryDate.toISOString());
        localStorage.setItem("vertice_refresh_token", mockRefreshToken);

        setToken(authToken);
        setUser(userData);

        // Schedule automatic token refresh
        scheduleTokenRefresh(expiresIn);

        return { success: true, user: userData };
      }

      // OAuth2 REAL via auth_service
      const AUTH_SERVICE_URL =
        import.meta.env.VITE_AUTH_SERVICE_URL || API_BASE_URL;

      // Simula Google OAuth flow (em produção, usar Google Sign-In SDK)
      const response = await fetch(`${AUTH_SERVICE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        throw new Error("Authentication failed");
      }

      const data = await response.json();

      // Determinar role baseado no email
      const role =
        email === SUPER_ADMIN
          ? "super_admin"
          : data.user_info?.role || "analyst";

      const userData = {
        email: data.user_info.email,
        name: data.user_info.name || email.split("@")[0],
        picture: data.user_info.picture || "",
        role: role,
        authenticated_at: new Date().toISOString(),
        permissions: ROLES[role].permissions,
        level: ROLES[role].level,
      };

      const authToken = data.access_token;
      const expiresIn = data.expires_in || 3600;
      const expiryDate = new Date();
      expiryDate.setSeconds(expiryDate.getSeconds() + expiresIn);

      localStorage.setItem("vertice_auth_token", authToken);
      localStorage.setItem("vertice_user", JSON.stringify(userData));
      localStorage.setItem("vertice_token_expiry", expiryDate.toISOString());

      // Store refresh token if provided
      if (data.refresh_token) {
        localStorage.setItem("vertice_refresh_token", data.refresh_token);
      }

      setToken(authToken);
      setUser(userData);

      // Schedule automatic token refresh
      scheduleTokenRefresh(expiresIn);

      logger.info("Login successful, token refresh scheduled");

      return { success: true, user: userData };
    } catch (error) {
      logger.error("Login failed:", error);

      // REGRA DE OURO: No fallback to mock in production
      // Return error instead - UI should show appropriate error message
      return {
        success: false,
        error:
          error.message ||
          "Authentication service unavailable. Please try again later.",
      };
    }
  };

  /**
   * Logout - limpa tokens e dados
   */
  const logout = async () => {
    clearAuthData();
    return { success: true };
  };

  /**
   * Get user role
   */
  const getUserRole = () => {
    return user?.role || "viewer";
  };

  /**
   * Check if user has specific permission
   */
  const hasPermission = (permission) => {
    if (!user) return false;

    const userPermissions = user.permissions || [];

    // Super admin tem tudo
    if (userPermissions.includes("*")) {
      return true;
    }

    return userPermissions.includes(permission);
  };

  /**
   * Check offensive permission
   */
  const canAccessOffensive = () => {
    return hasPermission("offensive") || user?.email === SUPER_ADMIN;
  };

  /**
   * Get auth token
   */
  const getAuthToken = () => {
    return token;
  };

  /**
   * Get user permissions list
   */
  const getUserPermissions = () => {
    return user?.permissions || [];
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    getUserRole,
    getUserPermissions,
    hasPermission,
    canAccessOffensive,
    getAuthToken,
    isAuthenticated: !!user,
    SUPER_ADMIN,
    ROLES,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export { AuthContext };
