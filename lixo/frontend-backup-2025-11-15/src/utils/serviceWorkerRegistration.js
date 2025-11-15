/**
 * Service Worker Registration
 * ============================
 *
 * Handles registration, updates, and lifecycle of service worker
 * Provides hooks for offline/online status and update notifications
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 */

const isLocalhost = Boolean(
  window.location.hostname === "localhost" ||
    window.location.hostname === "[::1]" ||
    window.location.hostname.match(
      /^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/,
    ),
);

/**
 * Register service worker
 *
 * @param {Object} config - Configuration options
 * @param {Function} config.onSuccess - Callback when SW is registered
 * @param {Function} config.onUpdate - Callback when SW update is available
 * @param {Function} config.onOffline - Callback when app goes offline
 * @param {Function} config.onOnline - Callback when app goes online
 */
export function register(config = {}) {
  if (process.env.NODE_ENV === "production" && "serviceWorker" in navigator) {
    const publicUrl = new URL(
      process.env.PUBLIC_URL || "",
      window.location.href,
    );
    if (publicUrl.origin !== window.location.origin) {
      return;
    }

    window.addEventListener("load", () => {
      const swUrl = `${process.env.PUBLIC_URL}/service-worker.js`;

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log("[SW] App is being served from cache (localhost)");
        });
      } else {
        registerValidSW(swUrl, config);
      }

      // Listen for online/offline events
      setupOnlineOfflineListeners(config);
    });
  }
}

function registerValidSW(swUrl, config) {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log("[SW] Service worker registered:", registration);

      // Check for updates every hour
      setInterval(
        () => {
          registration.update();
        },
        60 * 60 * 1000,
      );

      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === "installed") {
            if (navigator.serviceWorker.controller) {
              // New update available
              console.log("[SW] New content is available; please refresh.");

              if (config && config.onUpdate) {
                config.onUpdate(registration);
              }

              // Optionally auto-update
              if (config && config.autoUpdate) {
                installingWorker.postMessage({ type: "SKIP_WAITING" });
                window.location.reload();
              }
            } else {
              // Content cached for offline use
              console.log("[SW] Content is cached for offline use.");

              if (config && config.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };
    })
    .catch((error) => {
      console.error("[SW] Error during service worker registration:", error);
    });
}

function checkValidServiceWorker(swUrl, config) {
  fetch(swUrl, {
    headers: { "Service-Worker": "script" },
  })
    .then((response) => {
      const contentType = response.headers.get("content-type");
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf("javascript") === -1)
      ) {
        // Service worker not found, reload page
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log(
        "[SW] No internet connection. App is running in offline mode.",
      );
    });
}

function setupOnlineOfflineListeners(config) {
  window.addEventListener("online", () => {
    console.log("[SW] App is online");
    if (config && config.onOnline) {
      config.onOnline();
    }
  });

  window.addEventListener("offline", () => {
    console.log("[SW] App is offline");
    if (config && config.onOffline) {
      config.onOffline();
    }
  });
}

/**
 * Unregister service worker
 */
export function unregister() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
        console.log("[SW] Service worker unregistered");
      })
      .catch((error) => {
        console.error(
          "[SW] Error unregistering service worker:",
          error.message,
        );
      });
  }
}

/**
 * Send message to service worker
 */
export function sendMessageToSW(message) {
  if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage(message);
  }
}

/**
 * Clear all caches
 */
export function clearCaches() {
  sendMessageToSW({ type: "CLEAR_CACHE" });
}

/**
 * Get cache size
 */
export async function getCacheSize() {
  return new Promise((resolve) => {
    if ("serviceWorker" in navigator && navigator.serviceWorker.controller) {
      const messageChannel = new MessageChannel();

      messageChannel.port1.onmessage = (event) => {
        if (event.data.type === "CACHE_SIZE") {
          resolve(event.data.size);
        }
      };

      navigator.serviceWorker.controller.postMessage(
        { type: "GET_CACHE_SIZE" },
        [messageChannel.port2],
      );
    } else {
      resolve(0);
    }
  });
}

/**
 * Check if app is offline
 */
export function isOffline() {
  return !navigator.onLine;
}

/**
 * Check if service worker is supported
 */
export function isSupported() {
  return "serviceWorker" in navigator;
}

export default {
  register,
  unregister,
  sendMessageToSW,
  clearCaches,
  getCacheSize,
  isOffline,
  isSupported,
};
