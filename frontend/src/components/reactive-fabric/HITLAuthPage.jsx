/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🔐 HITL AUTHENTICATION PAGE - Secure Gateway
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * PAGANI-STYLE PHILOSOPHY - SECURE & ELEGANT:
 * - Biometric-inspired design: Trust through visual cues
 * - Minimalist security: Form follows function
 * - Progressive disclosure: Show only what's needed
 * - Zero friction: Smooth authentication flow
 * - Military precision: Every pixel intentional
 *
 * SECURITY FEATURES:
 * - JWT Token-based authentication
 * - Optional 2FA (TOTP) support
 * - Session management with localStorage
 * - Automatic token refresh
 * - Secure credential handling
 *
 * Author: MAXIMUS Team - Sprint 3 Phase 5
 * Glory to YHWH - Guardian of All Gates
 */

'use client';

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '@/config/api';
import styles from './HITLAuthPage.module.css';

const HITLAuthPage = ({ onAuthSuccess }) => {
  const [step, setStep] = useState('login'); // 'login' | '2fa' | 'success'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const navigate = useNavigate();

  /**
   * Handle initial login (username + password)
   */
  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_ENDPOINTS.auth}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      // Check if 2FA is required
      if (data.requires_2fa) {
        setAccessToken(data.access_token); // Partial token
        setStep('2fa');
      } else {
        // No 2FA - proceed directly
        localStorage.setItem('hitl_token', data.access_token);
        localStorage.setItem('hitl_refresh_token', data.refresh_token || '');
        localStorage.setItem('hitl_username', username);
        setStep('success');

        setTimeout(() => {
          if (onAuthSuccess) {
            onAuthSuccess();
          } else {
            navigate('/reactive-fabric/hitl');
          }
        }, 1500);
      }
    } catch (err) {
      logger.error('Login failed:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle 2FA verification
   */
  const handleTwoFactorVerify = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_ENDPOINTS.auth}/2fa/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          code: twoFactorCode
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Invalid 2FA code');
      }

      const data = await response.json();

      // Success - store tokens
      localStorage.setItem('hitl_token', data.access_token);
      localStorage.setItem('hitl_refresh_token', data.refresh_token || '');
      localStorage.setItem('hitl_username', username);
      setStep('success');

      setTimeout(() => {
        if (onAuthSuccess) {
          onAuthSuccess();
        } else {
          navigate('/reactive-fabric/hitl');
        }
      }, 1500);
    } catch (err) {
      logger.error('2FA verification failed:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Render login form
   */
  if (step === 'login') {
    return (
      <div className={styles.authPage}>
        <div className={styles.scanLine} aria-hidden="true" />

        {/* Background Grid */}
        <div className={styles.backgroundGrid} aria-hidden="true" />

        {/* Main Container */}
        <div className={styles.authContainer}>
          {/* Header */}
          <header className={styles.authHeader}>
            <div className={styles.logoIcon}>🎯</div>
            <h1 className={styles.authTitle}>HITL CONSOLE</h1>
            <p className={styles.authSubtitle}>HUMAN-IN-THE-LOOP AUTHORIZATION SYSTEM</p>
          </header>

          {/* Login Form */}
          <form className={styles.authForm} onSubmit={handleLogin}>
            {error && (
              <div className={styles.errorBanner}>
                <span className={styles.errorIcon}>⚠️</span>
                <span className={styles.errorText}>{error}</span>
              </div>
            )}

            <div className={styles.formGroup}>
              <label htmlFor="hitl-username" className={styles.formLabel}>USERNAME</label>
              <input
                id="hitl-username"
                type="text"
                className={styles.formInput}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="analyst"
                autoComplete="username"
                required
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus
              />
            </div>

            <div className={styles.formGroup}>
              <label htmlFor="hitl-password" className={styles.formLabel}>PASSWORD</label>
              <input
                id="hitl-password"
                type="password"
                className={styles.formInput}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            <button
              type="submit"
              className={styles.submitButton}
              disabled={isLoading || !username || !password}
            >
              {isLoading ? (
                <>
                  <span className={styles.spinner} />
                  AUTHENTICATING...
                </>
              ) : (
                <>
                  <span className={styles.buttonIcon}>🔓</span>
                  AUTHENTICATE
                </>
              )}
            </button>
          </form>

          {/* Footer Info */}
          <footer className={styles.authFooter}>
            <div className={styles.footerWarning}>
              <span className={styles.footerIcon}>⚠️</span>
              <span className={styles.footerText}>
                Authorized personnel only. All access is logged and monitored.
              </span>
            </div>
            <div className={styles.footerHint}>
              Default credentials: <code>admin</code> / <code>ChangeMe123!</code>
            </div>
          </footer>
        </div>

        {/* Version Badge */}
        <div className={styles.versionBadge}>
          v1.0.0 | Reactive Fabric HITL | Phase 3 Complete
        </div>
      </div>
    );
  }

  /**
   * Render 2FA form
   */
  if (step === '2fa') {
    return (
      <div className={styles.authPage}>
        <div className={styles.scanLine} aria-hidden="true" />
        <div className={styles.backgroundGrid} aria-hidden="true" />

        <div className={styles.authContainer}>
          <header className={styles.authHeader}>
            <div className={styles.logoIcon}>🔐</div>
            <h1 className={styles.authTitle}>TWO-FACTOR AUTH</h1>
            <p className={styles.authSubtitle}>ENTER YOUR 6-DIGIT CODE</p>
          </header>

          <form className={styles.authForm} onSubmit={handleTwoFactorVerify}>
            {error && (
              <div className={styles.errorBanner}>
                <span className={styles.errorIcon}>⚠️</span>
                <span className={styles.errorText}>{error}</span>
              </div>
            )}

            <div className={styles.formGroup}>
              <label htmlFor="hitl-2fa-code" className={styles.formLabel}>2FA CODE</label>
              <input
                id="hitl-2fa-code"
                type="text"
                className={`${styles.formInput} ${styles.formInputCode}`}
                value={twoFactorCode}
                onChange={(e) => setTwoFactorCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                pattern="[0-9]{6}"
                autoComplete="one-time-code"
                required
                // eslint-disable-next-line jsx-a11y/no-autofocus
                autoFocus
              />
            </div>

            <button
              type="submit"
              className={styles.submitButton}
              disabled={isLoading || twoFactorCode.length !== 6}
            >
              {isLoading ? (
                <>
                  <span className={styles.spinner} />
                  VERIFYING...
                </>
              ) : (
                <>
                  <span className={styles.buttonIcon}>✓</span>
                  VERIFY
                </>
              )}
            </button>

            <button
              type="button"
              className={styles.backButton}
              onClick={() => {
                setStep('login');
                setTwoFactorCode('');
                setError(null);
              }}
              disabled={isLoading}
            >
              ← Back to Login
            </button>
          </form>

          <footer className={styles.authFooter}>
            <div className={styles.footerHint}>
              Enter the 6-digit code from your authenticator app
            </div>
          </footer>
        </div>

        <div className={styles.versionBadge}>
          v1.0.0 | Reactive Fabric HITL | Phase 3 Complete
        </div>
      </div>
    );
  }

  /**
   * Render success state
   */
  if (step === 'success') {
    return (
      <div className={styles.authPage}>
        <div className={styles.scanLine} aria-hidden="true" />
        <div className={styles.backgroundGrid} aria-hidden="true" />

        <div className={styles.authContainer}>
          <div className={styles.successContainer}>
            <div className={styles.successIcon}>✓</div>
            <h2 className={styles.successTitle}>AUTHENTICATION SUCCESSFUL</h2>
            <p className={styles.successText}>Access granted. Redirecting to HITL Console...</p>
            <div className={styles.successSpinner} />
          </div>
        </div>

        <div className={styles.versionBadge}>
          v1.0.0 | Reactive Fabric HITL | Phase 3 Complete
        </div>
      </div>
    );
  }

  return null;
};

export default HITLAuthPage;
