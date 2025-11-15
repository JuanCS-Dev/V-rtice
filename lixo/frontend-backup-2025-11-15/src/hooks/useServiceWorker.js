/**
 * useServiceWorker Hook
 * ======================
 *
 * React hook for service worker integration
 * Provides offline status, update notifications, and cache management
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 *
 * @example
 * const { isOffline, hasUpdate, updateServiceWorker, cacheSize } = useServiceWorker();
 */

import { useState, useEffect, useCallback } from "react";
import {
  register,
  isOffline as checkOffline,
  getCacheSize,
  clearCaches,
  sendMessageToSW,
} from "@/utils/serviceWorkerRegistration";
import logger from "@/utils/logger";

export const useServiceWorker = () => {
  const [isOffline, setIsOffline] = useState(checkOffline());
  const [hasUpdate, setHasUpdate] = useState(false);
  const [registration, setRegistration] = useState(null);
  const [cacheSize, setCacheSize] = useState(0);
  const [isSupported, setIsSupported] = useState("serviceWorker" in navigator);

  // Register service worker on mount
  useEffect(() => {
    if (!isSupported) {
      logger.warn("[useServiceWorker] Service Worker not supported");
      return;
    }

    register({
      onSuccess: (reg) => {
        logger.info(
          "[useServiceWorker] Service worker registered successfully",
        );
        setRegistration(reg);
        updateCacheSize();
      },
      onUpdate: (reg) => {
        logger.info("[useServiceWorker] Service worker update available");
        setHasUpdate(true);
        setRegistration(reg);
      },
      onOnline: () => {
        logger.info("[useServiceWorker] App is online");
        setIsOffline(false);
      },
      onOffline: () => {
        logger.warn("[useServiceWorker] App is offline");
        setIsOffline(true);
      },
    });

    // Update cache size periodically
    const interval = setInterval(updateCacheSize, 60000); // Every minute

    return () => {
      clearInterval(interval);
    };
  }, [isSupported]);

  // Listen for online/offline events
  useEffect(() => {
    const handleOnline = () => {
      logger.info("[useServiceWorker] Online event");
      setIsOffline(false);
    };

    const handleOffline = () => {
      logger.warn("[useServiceWorker] Offline event");
      setIsOffline(true);
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Update cache size
  const updateCacheSize = useCallback(async () => {
    try {
      const size = await getCacheSize();
      setCacheSize(size);
      logger.debug("[useServiceWorker] Cache size:", size);
    } catch (error) {
      logger.error("[useServiceWorker] Failed to get cache size:", error);
    }
  }, []);

  // Update service worker
  const updateServiceWorker = useCallback(() => {
    if (registration && registration.waiting) {
      logger.info("[useServiceWorker] Activating service worker update");
      sendMessageToSW({ type: "SKIP_WAITING" });

      // Reload page after SW activates
      let refreshing = false;
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (!refreshing) {
          refreshing = true;
          window.location.reload();
        }
      });
    }
  }, [registration]);

  // Clear all caches
  const clearAllCaches = useCallback(async () => {
    try {
      logger.info("[useServiceWorker] Clearing all caches");
      await clearCaches();
      await updateCacheSize();
      logger.info("[useServiceWorker] Caches cleared successfully");
    } catch (error) {
      logger.error("[useServiceWorker] Failed to clear caches:", error);
    }
  }, [updateCacheSize]);

  // Cache specific URLs
  const cacheUrls = useCallback(
    (urls) => {
      if (!Array.isArray(urls) || urls.length === 0) {
        logger.warn("[useServiceWorker] Invalid URLs provided for caching");
        return;
      }

      logger.info("[useServiceWorker] Caching URLs:", urls);
      sendMessageToSW({ type: "CACHE_URLS", payload: { urls } });
      updateCacheSize();
    },
    [updateCacheSize],
  );

  return {
    // State
    isOffline,
    hasUpdate,
    cacheSize,
    isSupported,
    registration,

    // Actions
    updateServiceWorker,
    clearAllCaches,
    cacheUrls,
    updateCacheSize,
  };
};

export default useServiceWorker;
