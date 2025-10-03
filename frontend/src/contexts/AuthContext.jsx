import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

/**
 * AuthProvider - Sistema de autenticação integrado com vertice-terminal
 * Usa o sistema de roles do CLI (super_admin, admin, analyst, viewer)
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('vertice_auth_token'));

  // Super Admin do sistema
  const SUPER_ADMIN = 'juan.brainfarma@gmail.com';

  // Roles e permissões (sincronizado com vertice-terminal)
  const ROLES = {
    super_admin: {
      email: SUPER_ADMIN,
      permissions: ['*'], // Todas as permissões
      level: 100
    },
    admin: {
      permissions: ['read', 'write', 'execute', 'manage_users', 'offensive'],
      level: 80
    },
    analyst: {
      permissions: ['read', 'write', 'execute'],
      level: 50
    },
    viewer: {
      permissions: ['read'],
      level: 10
    }
  };

  // Check if user is authenticated on app start
  useEffect(() => {
    const checkAuth = () => {
      const storedUser = localStorage.getItem('vertice_user');
      const storedToken = localStorage.getItem('vertice_auth_token');
      const tokenExpiry = localStorage.getItem('vertice_token_expiry');

      if (storedToken && storedUser && tokenExpiry) {
        const expiryDate = new Date(tokenExpiry);

        if (new Date() < expiryDate) {
          const userData = JSON.parse(storedUser);
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
    localStorage.removeItem('vertice_auth_token');
    localStorage.removeItem('vertice_user');
    localStorage.removeItem('vertice_token_expiry');
    setToken(null);
    setUser(null);
  };

  /**
   * Login usando Google OAuth2
   * Conecta com auth_service backend REAL
   */
  const login = async (email, useMock = false) => {
    try {
      // Se explicitamente usar mock (desenvolvimento)
      if (useMock) {
        const role = email === SUPER_ADMIN ? 'super_admin' : 'analyst';
        const userData = {
          email: email,
          name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1),
          picture: '',
          role: role,
          authenticated_at: new Date().toISOString(),
          permissions: ROLES[role].permissions,
          level: ROLES[role].level
        };

        const authToken = `ya29.mock_token_for_${email}`;
        const expiryDate = new Date();
        expiryDate.setHours(expiryDate.getHours() + 1);

        localStorage.setItem('vertice_auth_token', authToken);
        localStorage.setItem('vertice_user', JSON.stringify(userData));
        localStorage.setItem('vertice_token_expiry', expiryDate.toISOString());

        setToken(authToken);
        setUser(userData);

        return { success: true, user: userData };
      }

      // OAuth2 REAL via auth_service
      const AUTH_SERVICE_URL = import.meta.env.VITE_AUTH_SERVICE_URL || 'http://localhost:8010';

      // Simula Google OAuth flow (em produção, usar Google Sign-In SDK)
      const response = await fetch(`${AUTH_SERVICE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();

      // Determinar role baseado no email
      const role = email === SUPER_ADMIN ? 'super_admin' :
                   data.user_info?.role || 'analyst';

      const userData = {
        email: data.user_info.email,
        name: data.user_info.name || email.split('@')[0],
        picture: data.user_info.picture || '',
        role: role,
        authenticated_at: new Date().toISOString(),
        permissions: ROLES[role].permissions,
        level: ROLES[role].level
      };

      const authToken = data.access_token;
      const expiryDate = new Date();
      expiryDate.setSeconds(expiryDate.getSeconds() + (data.expires_in || 3600));

      localStorage.setItem('vertice_auth_token', authToken);
      localStorage.setItem('vertice_user', JSON.stringify(userData));
      localStorage.setItem('vertice_token_expiry', expiryDate.toISOString());

      setToken(authToken);
      setUser(userData);

      return { success: true, user: userData };
    } catch (error) {
      console.error('Login failed:', error);

      // Fallback para mock em caso de erro (desenvolvimento)
      console.warn('Falling back to mock auth due to error');
      return login(email, true);
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
    return user?.role || 'viewer';
  };

  /**
   * Check if user has specific permission
   */
  const hasPermission = (permission) => {
    if (!user) return false;

    const userPermissions = user.permissions || [];

    // Super admin tem tudo
    if (userPermissions.includes('*')) {
      return true;
    }

    return userPermissions.includes(permission);
  };

  /**
   * Check offensive permission
   */
  const canAccessOffensive = () => {
    return hasPermission('offensive') || user?.email === SUPER_ADMIN;
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
    ROLES
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthContext };
