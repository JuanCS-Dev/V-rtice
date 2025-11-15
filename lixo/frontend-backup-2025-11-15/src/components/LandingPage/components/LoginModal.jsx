/**
 * ═══════════════════════════════════════════════════════════════════════════
 * LOGIN MODAL - Authentication Modal
 * ═══════════════════════════════════════════════════════════════════════════
 */

import React, { useState } from "react";
import { handleKeyboardClick } from "../../../utils/accessibility";
import styles from "./LoginModal.module.css";

export const LoginModal = ({ onClose, onSubmit }) => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const result = await onSubmit(email);
      if (!result.success) {
        setError(result.error || "Authentication failed");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setEmail("");
    setError("");
    onClose();
  };

  return (
    <div
      className={styles.overlay}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleClose();
        }
      }}
      onKeyDown={handleKeyboardClick((e) => {
        if (e.target === e.currentTarget) {
          handleClose();
        }
      })}
      role="presentation"
      aria-label="Close login modal"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-labelledby="login-title"
        aria-modal="true"
      >
        {/* Header */}
        <header className={styles.header}>
          <div className={styles.iconLarge}>🔐</div>
          <h2 id="login-title" className={styles.title}>
            VÉRTICE Authentication
          </h2>
          <p className={styles.subtitle}>Sistema de Autenticação Unificado</p>
        </header>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className={styles.field}>
            <label htmlFor="email-input" className={styles.label}>
              Email Google
            </label>
            <input
              id="email-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="seu.email@gmail.com"
              required
              disabled={isLoading}
              className={styles.input}
              aria-describedby={error ? "error-message" : "email-hint"}
            />
          </div>

          {/* Info Box */}
          <div className={styles.info}>
            <span className={styles.infoIcon}>ℹ️</span>
            <div>
              <div className={styles.infoTitle}>
                Super Admin: juan.brainfarma@gmail.com
              </div>
              <div className={styles.infoText}>
                Outros emails terão permissões de Analyst
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div id="error-message" className={styles.error} role="alert">
              <span className={styles.errorIcon}>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Actions */}
          <div className={styles.actions}>
            <button
              type="button"
              onClick={handleClose}
              className={styles.btnCancel}
              disabled={isLoading}
            >
              CANCELAR
            </button>
            <button
              type="submit"
              className={styles.btnSubmit}
              disabled={isLoading}
            >
              {isLoading ? "AUTENTICANDO..." : "AUTENTICAR"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginModal;
