import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const UserHeader = () => {
  const { user, logout, canAccessOffensive } = useAuth();
  const [permissions, setPermissions] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [hasOffensiveAccess, setHasOffensiveAccess] = useState(false);

  useEffect(() => {
    const loadPermissions = async () => {
      try {
        const hasOffensive = await canAccessOffensive();
        setHasOffensiveAccess(hasOffensive);
      } catch (error) {
        console.error('Failed to check permissions:', error);
      }
    };

    if (user) {
      loadPermissions();
    }
  }, [user, canAccessOffensive]);

  const handleLogout = async () => {
    try {
      await logout();
      window.location.reload();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  if (!user) {
    return null;
  }

  const getPermissionBadgeColor = (permission) => {
    switch (permission) {
      case 'admin': return 'bg-red-400/20 text-red-400 border-red-400/50';
      case 'offensive': return 'bg-orange-400/20 text-orange-400 border-orange-400/50';
      case 'write': return 'bg-yellow-400/20 text-yellow-400 border-yellow-400/50';
      case 'read': return 'bg-green-400/20 text-green-400 border-green-400/50';
      default: return 'bg-cyan-400/20 text-cyan-400 border-cyan-400/50';
    }
  };

  return (
    <div className="bg-gray-900 border-b border-cyan-400/30 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left side - System info */}
        <div className="flex items-center space-x-4">
          <div className="text-cyan-400 font-bold text-xl tracking-wider">
            🛡️ PROJETO VÉRTICE
          </div>
          <div className="text-cyan-400/50 text-sm">
            Sistema Integrado de Cibersegurança
          </div>
        </div>

        {/* Right side - User info */}
        <div className="flex items-center space-x-4">
          {/* Security Status */}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm font-mono">SECURE</span>
          </div>

          {/* Offensive Tools Access Badge */}
          {hasOffensiveAccess && (
            <div className="bg-orange-400/20 border border-orange-400/50 text-orange-400 px-2 py-1 rounded text-xs font-bold">
              ⚡ OFFENSIVE ACCESS
            </div>
          )}

          {/* User dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center space-x-3 bg-cyan-400/10 hover:bg-cyan-400/20 border border-cyan-400/30 rounded-lg px-3 py-2 transition-all"
            >
              <img
                src={user.picture || '/default-avatar.png'}
                alt={user.name}
                className="w-8 h-8 rounded-full"
              />
              <div className="text-left">
                <div className="text-cyan-400 text-sm font-medium">{user.name}</div>
                <div className="text-cyan-400/70 text-xs">{user.email}</div>
              </div>
              <div className="text-cyan-400">
                <svg
                  className={`w-4 h-4 transform transition-transform ${showDropdown ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {/* Dropdown menu */}
            {showDropdown && (
              <div className="absolute right-0 mt-2 w-64 bg-gray-900 border border-cyan-400/30 rounded-lg shadow-xl z-50">
                <div className="p-4">
                  {/* User info */}
                  <div className="border-b border-cyan-400/30 pb-3 mb-3">
                    <div className="flex items-center space-x-3">
                      <img
                        src={user.picture || '/default-avatar.png'}
                        alt={user.name}
                        className="w-12 h-12 rounded-full"
                      />
                      <div>
                        <div className="text-cyan-400 font-medium">{user.name}</div>
                        <div className="text-cyan-400/70 text-sm">{user.email}</div>
                      </div>
                    </div>
                  </div>

                  {/* Permissions */}
                  <div className="mb-3">
                    <div className="text-cyan-400 text-xs font-bold mb-2">PERMISSÕES:</div>
                    <div className="flex flex-wrap gap-1">
                      {permissions.map((permission) => (
                        <span
                          key={permission}
                          className={`px-2 py-1 rounded text-xs font-bold border ${getPermissionBadgeColor(permission)}`}
                        >
                          {permission.toUpperCase()}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Session info */}
                  <div className="border-t border-cyan-400/30 pt-3 mb-3">
                    <div className="text-cyan-400/50 text-xs">
                      🔒 Sessão autenticada<br/>
                      🕒 {new Date().toLocaleString('pt-BR')}<br/>
                      📍 IP: {window.location.hostname}
                    </div>
                  </div>

                  {/* Logout button */}
                  <button
                    onClick={handleLogout}
                    className="w-full bg-red-400/20 hover:bg-red-400/30 border border-red-400/50 text-red-400 font-bold py-2 px-3 rounded transition-all text-sm"
                  >
                    🚪 LOGOUT
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};

export default UserHeader;