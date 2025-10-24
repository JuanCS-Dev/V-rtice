/**
 * WebSocket Manager
 * ==================
 *
 * Centralized WebSocket connection management with pub/sub pattern
 * Eliminates duplicate connections and provides unified interface
 *
 * Features:
 * - Connection pooling (single connection per endpoint)
 * - Pub/sub pattern for multiple subscribers
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong mechanism
 * - Fallback to SSE/polling
 * - Message queue for offline resilience
 * - Connection state management
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 *
 * Architecture:
 * Component → Hook → WebSocketManager (THIS LAYER) → WebSocket/SSE
 */

import logger from '@/utils/logger';
import { getWebSocketEndpoint } from '@/config/endpoints';

// Connection states
export const ConnectionState = {
  IDLE: 'IDLE',
  CONNECTING: 'CONNECTING',
  CONNECTED: 'CONNECTED',
  DISCONNECTING: 'DISCONNECTING',
  DISCONNECTED: 'DISCONNECTED',
  ERROR: 'ERROR',
  FALLBACK: 'FALLBACK', // Using SSE/polling
};

// Default configuration
const DEFAULT_CONFIG = {
  reconnect: true,
  reconnectInterval: 1000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 25000, // 25s (server heartbeat is typically 30s)
  heartbeatMessage: { type: 'ping' },
  fallbackToSSE: true,
  fallbackToPolling: true,
  pollingInterval: 5000,
  debug: false,
};

/**
 * Manages a single WebSocket connection with multiple subscribers
 */
class ConnectionManager {
  constructor(url, config = {}) {
    this.url = url;
    this.config = { ...DEFAULT_CONFIG, ...config };

    // Connection state
    this.state = ConnectionState.IDLE;
    this.ws = null;
    this.eventSource = null;

    // Subscribers (pub/sub pattern)
    this.subscribers = new Set();

    // Reconnection management
    this.reconnectAttempts = 0;
    this.reconnectTimeout = null;

    // Heartbeat
    this.heartbeatInterval = null;

    // Message queue for offline resilience
    this.messageQueue = [];

    // Fallback polling
    this.pollingInterval = null;

    // Connection metadata
    this.connectionId = null;
    this.lastHeartbeat = null;
  }

  /**
   * Subscribes to connection messages
   * @param {Function} callback - Called on new message
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    this.log(`Subscriber added (total: ${this.subscribers.size})`);

    // Auto-connect if first subscriber
    if (this.subscribers.size === 1 && this.state === ConnectionState.IDLE) {
      this.connect();
    }

    // Return unsubscribe function
    return () => {
      this.subscribers.delete(callback);
      this.log(`Subscriber removed (remaining: ${this.subscribers.size})`);

      // Auto-disconnect if no subscribers
      if (this.subscribers.size === 0) {
        this.disconnect();
      }
    };
  }

  /**
   * Notifies all subscribers with message
   * @param {Object} message - Message data
   */
  notify(message) {
    this.subscribers.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        logger.error('[ConnectionManager] Subscriber callback error:', error);
      }
    });
  }

  /**
   * Connects to WebSocket
   */
  connect() {
    if (this.state === ConnectionState.CONNECTING || this.state === ConnectionState.CONNECTED) {
      this.log('Already connecting or connected');
      return;
    }

    this.log(`Connecting to ${this.url}`);
    this.setState(ConnectionState.CONNECTING);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onerror = (error) => this.handleError(error);
      this.ws.onclose = (event) => this.handleClose(event);
    } catch (error) {
      this.log('Failed to create WebSocket:', error);
      this.handleError(error);
      this.tryFallback();
    }
  }

  /**
   * Handles WebSocket open event
   */
  handleOpen() {
    this.log('Connected');
    this.setState(ConnectionState.CONNECTED);
    this.reconnectAttempts = 0;

    // Start heartbeat
    this.startHeartbeat();

    // Process queued messages
    this.processQueue();

    // Notify subscribers
    this.notify({
      type: 'connection',
      status: 'connected',
      url: this.url,
    });
  }

  /**
   * Handles WebSocket message event
   * @param {MessageEvent} event - Message event
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);

      // Handle system messages
      if (data.type === 'pong') {
        this.lastHeartbeat = Date.now();
        this.log('Pong received');
        return;
      }

      if (data.type === 'welcome') {
        this.connectionId = data.connection_id;
        this.log('Connection ID:', this.connectionId);
        return;
      }

      if (data.type === 'heartbeat') {
        this.lastHeartbeat = Date.now();
        this.log('Heartbeat received');
        return;
      }

      // Notify subscribers with data
      this.notify(data);
    } catch (error) {
      logger.error('[ConnectionManager] Failed to parse message:', error);
      // Send raw data if JSON parsing fails
      this.notify({ type: 'raw', data: event.data });
    }
  }

  /**
   * Handles WebSocket error event
   * @param {Event} error - Error event
   */
  handleError(error) {
    logger.error('[ConnectionManager] WebSocket error:', error);
    this.setState(ConnectionState.ERROR);

    this.notify({
      type: 'connection',
      status: 'error',
      error: error.message || 'WebSocket error',
    });
  }

  /**
   * Handles WebSocket close event
   * @param {CloseEvent} event - Close event
   */
  handleClose(event) {
    this.log(`Disconnected (code: ${event.code}, reason: ${event.reason})`);
    this.setState(ConnectionState.DISCONNECTED);
    this.stopHeartbeat();

    this.notify({
      type: 'connection',
      status: 'disconnected',
      code: event.code,
      reason: event.reason,
    });

    // Auto-reconnect if enabled and not a normal closure
    if (this.config.reconnect && event.code !== 1000) {
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached, trying fallback');
      this.tryFallback();
    }
  }

  /**
   * Schedules reconnection with exponential backoff
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached');
      this.tryFallback();
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts),
      30000 // Max 30s
    );

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.config.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Tries fallback to SSE or polling
   */
  tryFallback() {
    if (this.config.fallbackToSSE) {
      this.connectSSE();
    } else if (this.config.fallbackToPolling) {
      this.startPolling();
    }
  }

  /**
   * Connects using Server-Sent Events (SSE)
   */
  connectSSE() {
    this.log('Falling back to SSE');
    this.setState(ConnectionState.FALLBACK);

    const sseUrl = this.url.replace('ws://', 'http://').replace('wss://', 'https://').replace('/ws', '/sse');

    try {
      this.eventSource = new EventSource(sseUrl);

      this.eventSource.onopen = () => {
        this.log('SSE connected');
        this.notify({
          type: 'connection',
          status: 'connected_sse',
          url: sseUrl,
        });
      };

      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.notify(data);
        } catch (error) {
          logger.error('[ConnectionManager] Failed to parse SSE message:', error);
        }
      };

      this.eventSource.onerror = (error) => {
        logger.error('[ConnectionManager] SSE error:', error);
        this.eventSource.close();
        this.eventSource = null;

        // Try polling as last resort
        if (this.config.fallbackToPolling) {
          this.startPolling();
        }
      };
    } catch (error) {
      logger.error('[ConnectionManager] Failed to create EventSource:', error);
      if (this.config.fallbackToPolling) {
        this.startPolling();
      }
    }
  }

  /**
   * Starts polling fallback
   */
  startPolling() {
    if (this.pollingInterval) return;

    this.log('Falling back to polling');
    this.setState(ConnectionState.FALLBACK);

    const pollingUrl = this.url.replace('ws://', 'http://').replace('wss://', 'https://').replace('/ws', '');

    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch(pollingUrl);
        if (response.ok) {
          const data = await response.json();
          this.notify(data);
        }
      } catch (error) {
        logger.error('[ConnectionManager] Polling error:', error);
      }
    }, this.config.pollingInterval);

    this.notify({
      type: 'connection',
      status: 'connected_polling',
      url: pollingUrl,
    });
  }

  /**
   * Stops polling
   */
  stopPolling() {
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
      this.log('Polling stopped');
    }
  }

  /**
   * Starts heartbeat mechanism
   */
  startHeartbeat() {
    if (!this.config.heartbeatInterval) return;

    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send(this.config.heartbeatMessage);
        this.log('Heartbeat sent');
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stops heartbeat mechanism
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Sends message through WebSocket
   * @param {Object|string} message - Message to send
   * @returns {boolean} Success status
   */
  send(message) {
    const payload = typeof message === 'string' ? message : JSON.stringify(message);

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(payload);
      this.log('Message sent:', message);
      return true;
    } else {
      // Queue message for when connection is restored
      this.messageQueue.push(payload);
      this.log('Message queued (offline):', message);
      return false;
    }
  }

  /**
   * Processes queued messages
   */
  processQueue() {
    if (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      this.log(`Processing ${this.messageQueue.length} queued messages`);
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        this.ws.send(message);
      }
    }
  }

  /**
   * Disconnects from WebSocket
   */
  disconnect() {
    this.log('Disconnecting');
    this.setState(ConnectionState.DISCONNECTING);

    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Stop heartbeat
    this.stopHeartbeat();

    // Stop polling
    this.stopPolling();

    // Close SSE
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Close WebSocket
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
  }

  /**
   * Sets connection state
   * @param {string} state - New state
   */
  setState(state) {
    this.state = state;
    this.log(`State changed: ${state}`);
  }

  /**
   * Logs message if debug enabled
   * @param {...any} args - Log arguments
   */
  log(...args) {
    if (this.config.debug) {
      logger.debug(`[ConnectionManager:${this.url}]`, ...args);
    }
  }

  /**
   * Gets connection status
   * @returns {Object} Status object
   */
  getStatus() {
    return {
      url: this.url,
      state: this.state,
      isConnected: this.state === ConnectionState.CONNECTED || this.state === ConnectionState.FALLBACK,
      subscriberCount: this.subscribers.size,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length,
      connectionId: this.connectionId,
      lastHeartbeat: this.lastHeartbeat,
    };
  }
}

/**
 * WebSocket Manager - Singleton
 * Manages multiple WebSocket connections
 */
class WebSocketManager {
  constructor() {
    this.connections = new Map();
    this.config = DEFAULT_CONFIG;
  }

  /**
   * Sets global configuration
   * @param {Object} config - Configuration object
   */
  configure(config) {
    this.config = { ...this.config, ...config };
  }

  /**
   * Subscribes to WebSocket endpoint
   * @param {string} endpointPath - Endpoint path (e.g., 'maximus.stream')
   * @param {Function} callback - Message callback
   * @param {Object} options - Connection options
   * @returns {Function} Unsubscribe function
   */
  subscribe(endpointPath, callback, options = {}) {
    const url = getWebSocketEndpoint(endpointPath);

    // Get or create connection manager
    if (!this.connections.has(url)) {
      const config = { ...this.config, ...options };
      this.connections.set(url, new ConnectionManager(url, config));
    }

    const manager = this.connections.get(url);
    return manager.subscribe(callback);
  }

  /**
   * Sends message to specific endpoint
   * @param {string} endpointPath - Endpoint path
   * @param {Object|string} message - Message to send
   * @returns {boolean} Success status
   */
  send(endpointPath, message) {
    const url = getWebSocketEndpoint(endpointPath);
    const manager = this.connections.get(url);

    if (!manager) {
      logger.warn(`[WebSocketManager] No connection for ${endpointPath}`);
      return false;
    }

    return manager.send(message);
  }

  /**
   * Gets status of specific endpoint
   * @param {string} endpointPath - Endpoint path
   * @returns {Object|null} Status object or null
   */
  getStatus(endpointPath) {
    const url = getWebSocketEndpoint(endpointPath);
    const manager = this.connections.get(url);
    return manager ? manager.getStatus() : null;
  }

  /**
   * Gets status of all connections
   * @returns {Object} Status map
   */
  getAllStatus() {
    const status = {};
    this.connections.forEach((manager, url) => {
      status[url] = manager.getStatus();
    });
    return status;
  }

  /**
   * Disconnects specific endpoint
   * @param {string} endpointPath - Endpoint path
   */
  disconnect(endpointPath) {
    const url = getWebSocketEndpoint(endpointPath);
    const manager = this.connections.get(url);

    if (manager) {
      manager.disconnect();
      this.connections.delete(url);
    }
  }

  /**
   * Disconnects all endpoints
   */
  disconnectAll() {
    this.connections.forEach((manager) => manager.disconnect());
    this.connections.clear();
  }
}

// Singleton instance
const webSocketManager = new WebSocketManager();

export { webSocketManager, WebSocketManager };
export default webSocketManager;
