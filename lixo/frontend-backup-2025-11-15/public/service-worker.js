/**
 * Service Worker - Vértice Frontend
 * ==================================
 *
 * Progressive Web App service worker with offline support
 * Implements intelligent caching strategies for different resource types
 *
 * Cache Strategies:
 * - Static Assets: Cache First (long-lived)
 * - API Calls: Network First with fallback
 * - Images: Cache First with background sync
 * - HTML: Network First (always fresh)
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 */

const CACHE_VERSION = "vertice-v1.0.0";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// Static assets to cache on install
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/manifest.json",
  "/favicon.ico",
  // Add other critical static assets
];

// API endpoints to cache (with TTL)
const API_CACHE_PATTERNS = [/\/api\/metrics/, /\/api\/scans/, /\/api\/alerts/];

// Max age for different cache types (in seconds)
const CACHE_MAX_AGE = {
  static: 30 * 24 * 60 * 60, // 30 days
  api: 5 * 60, // 5 minutes
  images: 7 * 24 * 60 * 60, // 7 days
  runtime: 24 * 60 * 60, // 1 day
};

// ============================================================================
// INSTALL EVENT - Cache static assets
// ============================================================================

self.addEventListener("install", (event) => {
  console.log("[Service Worker] Installing...", CACHE_VERSION);

  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => {
        console.log("[Service Worker] Caching static assets");
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log("[Service Worker] Installed successfully");
        return self.skipWaiting(); // Activate immediately
      })
      .catch((error) => {
        console.error("[Service Worker] Installation failed:", error);
      }),
  );
});

// ============================================================================
// ACTIVATE EVENT - Clean up old caches
// ============================================================================

self.addEventListener("activate", (event) => {
  console.log("[Service Worker] Activating...", CACHE_VERSION);

  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            // Delete old versions
            if (
              cacheName.startsWith("vertice-") &&
              !cacheName.startsWith(CACHE_VERSION)
            ) {
              console.log("[Service Worker] Deleting old cache:", cacheName);
              return caches.delete(cacheName);
            }
          }),
        );
      })
      .then(() => {
        console.log("[Service Worker] Activated successfully");
        return self.clients.claim(); // Take control immediately
      }),
  );
});

// ============================================================================
// FETCH EVENT - Intercept network requests
// ============================================================================

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== self.location.origin) {
    return;
  }

  // Skip WebSocket connections
  if (request.url.includes("/ws") || request.url.startsWith("ws:")) {
    return;
  }

  // Route request based on type
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirstStrategy(request, STATIC_CACHE));
  } else if (isAPIRequest(request)) {
    event.respondWith(networkFirstStrategy(request, API_CACHE));
  } else if (isImageRequest(request)) {
    event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
  } else if (isHTMLRequest(request)) {
    event.respondWith(networkFirstStrategy(request, RUNTIME_CACHE));
  } else {
    event.respondWith(networkFirstStrategy(request, RUNTIME_CACHE));
  }
});

// ============================================================================
// CACHE STRATEGIES
// ============================================================================

/**
 * Cache First Strategy
 * Return cached response if available, otherwise fetch from network
 */
async function cacheFirstStrategy(request, cacheName) {
  try {
    // Check cache first
    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      // Check if cache is still fresh
      const cacheTime = await getCacheTime(request, cacheName);
      const maxAge = CACHE_MAX_AGE[getCacheType(cacheName)];

      if (Date.now() - cacheTime < maxAge * 1000) {
        console.log("[Service Worker] Cache hit:", request.url);
        return cachedResponse;
      }
    }

    // Fetch from network
    console.log("[Service Worker] Fetching from network:", request.url);
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
      await setCacheTime(request, cacheName);
    }

    return networkResponse;
  } catch (error) {
    console.error("[Service Worker] Fetch failed:", error);

    // Return cached response even if stale
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log("[Service Worker] Returning stale cache:", request.url);
      return cachedResponse;
    }

    // Return offline fallback
    return new Response("Offline - Resource not available", {
      status: 503,
      statusText: "Service Unavailable",
    });
  }
}

/**
 * Network First Strategy
 * Try network first, fallback to cache if offline
 */
async function networkFirstStrategy(request, cacheName) {
  try {
    // Try network first
    console.log("[Service Worker] Fetching from network:", request.url);
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
      await setCacheTime(request, cacheName);
    }

    return networkResponse;
  } catch (error) {
    console.error("[Service Worker] Network failed, trying cache:", error);

    // Fallback to cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log("[Service Worker] Cache hit (fallback):", request.url);
      return cachedResponse;
    }

    // Return offline fallback
    return new Response(
      JSON.stringify({
        error: "Offline",
        message: "Network unavailable and no cached data",
      }),
      {
        status: 503,
        statusText: "Service Unavailable",
        headers: { "Content-Type": "application/json" },
      },
    );
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function isStaticAsset(request) {
  return (
    request.url.match(/\.(js|css|woff2?|ttf|otf|eot|svg)$/) ||
    request.url.includes("/assets/")
  );
}

function isAPIRequest(request) {
  return (
    request.url.includes("/api/") ||
    API_CACHE_PATTERNS.some((pattern) => pattern.test(request.url))
  );
}

function isImageRequest(request) {
  return request.url.match(/\.(png|jpg|jpeg|gif|webp|ico)$/);
}

function isHTMLRequest(request) {
  return request.headers.get("Accept")?.includes("text/html");
}

function getCacheType(cacheName) {
  if (cacheName.includes("static")) return "static";
  if (cacheName.includes("api")) return "api";
  if (cacheName.includes("images")) return "images";
  return "runtime";
}

// Cache timing (stored in IndexedDB for persistence)
const CACHE_TIMES_STORE = "cache-times";

async function getCacheTime(request, cacheName) {
  try {
    const db = await openCacheTimesDB();
    const tx = db.transaction(CACHE_TIMES_STORE, "readonly");
    const store = tx.objectStore(CACHE_TIMES_STORE);
    const key = `${cacheName}:${request.url}`;
    const result = await store.get(key);
    return result?.timestamp || 0;
  } catch (error) {
    console.error("[Service Worker] Failed to get cache time:", error);
    return 0;
  }
}

async function setCacheTime(request, cacheName) {
  try {
    const db = await openCacheTimesDB();
    const tx = db.transaction(CACHE_TIMES_STORE, "readwrite");
    const store = tx.objectStore(CACHE_TIMES_STORE);
    const key = `${cacheName}:${request.url}`;
    await store.put({ key, timestamp: Date.now() });
  } catch (error) {
    console.error("[Service Worker] Failed to set cache time:", error);
  }
}

function openCacheTimesDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("vertice-sw-cache", 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(CACHE_TIMES_STORE)) {
        db.createObjectStore(CACHE_TIMES_STORE, { keyPath: "key" });
      }
    };
  });
}

// ============================================================================
// MESSAGE HANDLER - Communication with main thread
// ============================================================================

self.addEventListener("message", (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case "SKIP_WAITING":
      self.skipWaiting();
      break;

    case "CACHE_URLS":
      event.waitUntil(
        caches.open(RUNTIME_CACHE).then((cache) => {
          return cache.addAll(payload.urls);
        }),
      );
      break;

    case "CLEAR_CACHE":
      event.waitUntil(
        caches.keys().then((cacheNames) => {
          return Promise.all(cacheNames.map((name) => caches.delete(name)));
        }),
      );
      break;

    case "GET_CACHE_SIZE":
      event.waitUntil(
        getCacheSize().then((size) => {
          event.ports[0].postMessage({ type: "CACHE_SIZE", size });
        }),
      );
      break;

    default:
      console.log("[Service Worker] Unknown message type:", type);
  }
});

async function getCacheSize() {
  const cacheNames = await caches.keys();
  let totalSize = 0;

  for (const name of cacheNames) {
    const cache = await caches.open(name);
    const keys = await cache.keys();
    totalSize += keys.length;
  }

  return totalSize;
}

console.log("[Service Worker] Loaded", CACHE_VERSION);
