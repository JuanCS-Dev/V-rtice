/**
 * ═══════════════════════════════════════════════════════════════════════════
 * AUTH BADGE - Compact Authentication Display
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Design Philosophy:
 * - Elegant authentication indicator
 * - Smooth transitions
 * - Tema-agnóstico
 * - Compact & clean
 */

import React from "react";
import styles from "./AuthBadge.module.css";

export const AuthBadge = ({ isAuthenticated, user, onLogin, onLogout }) => {
  if (isAuthenticated) {
    return (
      <div className={styles.authenticated}>
        <div className={styles.userInfo}>
          <div className={styles.userName}>{user?.name || user?.email}</div>
          <div className={styles.userRole}>
            {user?.role?.toUpperCase() || "USER"}
            {user?.role === "super_admin" && " 👑"}
          </div>
        </div>
        <button
          onClick={onLogout}
          className={styles.logoutBtn}
          aria-label="Logout"
        >
          LOGOUT
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={onLogin}
      className={styles.loginBtn}
      aria-label="Login to system"
    >
      <span className={styles.loginIcon}>🔐</span>
      <span>ACESSAR</span>
    </button>
  );
};

export default AuthBadge;
