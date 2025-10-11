import React, { useState, useEffect } from 'react';
import logger from '@/utils/logger';
import { useAuth } from '../../contexts/AuthContext';

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, isAuthenticated } = useAuth();

  useEffect(() => {
    // Load Google Identity Services script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || '742659550291-l5sik6vhh0p4k8c8n3klup0b9o1vvs8m.apps.googleusercontent.com',
          callback: handleGoogleResponse
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            theme: 'filled_black',
            size: 'large',
            type: 'standard',
            text: 'signin_with',
            logo_alignment: 'left'
          }
        );
      }
    };

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  const handleGoogleResponse = async (response) => {
    setIsLoading(true);
    setError('');

    try {
      const result = await login(response.credential);

      if (!result.success) {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
      logger.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isAuthenticated) {
    return null; // Will be handled by App component routing
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center px-4">
      <div className="bg-gray-900 border border-cyan-400/30 rounded-lg p-8 w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="text-cyan-400 text-6xl mb-4">🛡️</div>
          <h1 className="text-cyan-400 text-3xl font-bold tracking-wider mb-2">
            PROJETO VÉRTICE
          </h1>
          <p className="text-cyan-400/70 text-sm">
            Sistema Integrado de Inteligência e Segurança Cibernética
          </p>
        </div>

        {/* Login Form */}
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-cyan-400 text-xl font-bold mb-2">
              ACESSO RESTRITO
            </h2>
            <p className="text-cyan-400/70 text-sm mb-6">
              Faça login com sua conta Google autorizada para continuar
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-400/20 border border-red-400/50 rounded p-3 text-red-400 text-sm">
              ⚠️ {error}
            </div>
          )}

          {/* Google Sign In Button */}
          <div className="flex justify-center">
            <div
              id="google-signin-button"
              className={`${isLoading ? 'opacity-50 pointer-events-none' : ''}`}
            />
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center items-center space-x-2 text-cyan-400">
              <div className="w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-sm">Autenticando...</span>
            </div>
          )}

          {/* Security Notice */}
          <div className="border-t border-cyan-400/30 pt-4 text-center">
            <p className="text-cyan-400/50 text-xs">
              🔒 Todas as sessões são monitoradas e registradas<br/>
              💼 Acesso restrito a usuários autorizados<br/>
              ⚡ Ferramentas ofensivas requerem permissões especiais
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-cyan-400/30 text-xs">
          <p>Desenvolvido por Batman do Cerrado</p>
          <p>v2024.3 - Módulo de Autenticação</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;