/**
 * ServiceWorkerUpdateNotification Component
 * ==========================================
 *
 * Displays notification when service worker update is available
 * Provides user option to update immediately or dismiss
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 */

import React from "react";
import { useServiceWorker } from "@/hooks/useServiceWorker";
import styles from "./ServiceWorkerUpdateNotification.module.css";

export const ServiceWorkerUpdateNotification = () => {
  const { hasUpdate, updateServiceWorker, isOffline } = useServiceWorker();
  const [dismissed, setDismissed] = React.useState(false);

  if (!hasUpdate || dismissed) {
    return null;
  }

  const handleUpdate = () => {
    updateServiceWorker();
  };

  const handleDismiss = () => {
    setDismissed(true);
  };

  return (
    <div className={styles.notification}>
      <div className={styles.content}>
        <div className={styles.icon}>🔄</div>
        <div className={styles.message}>
          <strong>Update Available</strong>
          <p>A new version of the application is ready.</p>
        </div>
      </div>
      <div className={styles.actions}>
        <button onClick={handleUpdate} className={styles.updateBtn}>
          Update Now
        </button>
        <button onClick={handleDismiss} className={styles.dismissBtn}>
          Later
        </button>
      </div>
    </div>
  );
};

export const OfflineIndicator = () => {
  const { isOffline } = useServiceWorker();

  if (!isOffline) {
    return null;
  }

  return (
    <div className={styles.offlineIndicator}>
      <span className={styles.offlineIcon}>📡</span>
      <span>Offline Mode - Using cached data</span>
    </div>
  );
};

export default ServiceWorkerUpdateNotification;
