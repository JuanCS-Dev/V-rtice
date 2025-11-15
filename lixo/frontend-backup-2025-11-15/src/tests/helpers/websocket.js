/**
 * WebSocket Test Helpers
 *
 * Reusable utilities for testing WebSocket-based hooks and components
 * Uses vitest-websocket-mock for scientific, behavioral testing
 */

import WS from "vitest-websocket-mock";

/**
 * Create a mock WebSocket server for testing
 *
 * @param {string} url - WebSocket URL (e.g., 'ws://localhost:8000/ws/test')
 * @param {object} options - Server options
 * @param {boolean} options.jsonProtocol - Auto-serialize/deserialize JSON (default: true)
 * @returns {WS} Mock server instance
 *
 * @example
 * const server = createMockWSServer('ws://localhost:8000/ws/test');
 * await server.connected; // Wait for client connection
 * server.send({ type: 'message', data: 'hello' });
 * await expect(server).toReceiveMessage({ type: 'response' });
 */
export function createMockWSServer(url, options = {}) {
  const defaultOptions = {
    jsonProtocol: true,
    ...options,
  };

  return new WS(url, defaultOptions);
}

/**
 * Cleanup all WebSocket mocks
 * Call this in afterEach() to reset state between tests
 *
 * @example
 * afterEach(() => {
 *   cleanupWSMocks();
 * });
 */
export function cleanupWSMocks() {
  WS.clean();
}

/**
 * Simulate a WebSocket connection sequence
 * Useful for testing reconnection logic
 *
 * @param {WS} server - Mock server instance
 * @param {function} onConnected - Callback after connection
 * @returns {Promise<void>}
 *
 * @example
 * await simulateWSConnection(server, async () => {
 *   server.send({ type: 'welcome' });
 * });
 */
export async function simulateWSConnection(server, onConnected) {
  await server.connected;
  if (onConnected) {
    await onConnected();
  }
}

/**
 * Simulate a WebSocket disconnection
 *
 * @param {WS} server - Mock server instance
 * @param {number} code - Close code (default: 1000 = normal closure)
 * @param {string} reason - Close reason (default: '')
 *
 * @example
 * await simulateWSDisconnection(server);
 * // Client should handle reconnection
 */
export async function simulateWSDisconnection(
  server,
  code = 1000,
  reason = "",
) {
  server.close({ code, reason });
  await server.closed;
}

/**
 * Simulate a WebSocket error
 *
 * @param {WS} server - Mock server instance
 *
 * @example
 * await simulateWSError(server);
 * // Client should handle error state
 */
export async function simulateWSError(server) {
  server.error();
}

/**
 * Send a sequence of messages with delays
 * Useful for testing message queuing and processing
 *
 * @param {WS} server - Mock server instance
 * @param {Array<object>} messages - Messages to send
 * @param {number} delayMs - Delay between messages (default: 100ms)
 *
 * @example
 * await sendMessageSequence(server, [
 *   { type: 'msg1' },
 *   { type: 'msg2' },
 *   { type: 'msg3' }
 * ], 50);
 */
export async function sendMessageSequence(server, messages, delayMs = 100) {
  for (const message of messages) {
    server.send(message);
    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
}

/**
 * Assert that server received a sequence of messages in order
 *
 * @param {WS} server - Mock server instance
 * @param {Array<object>} expectedMessages - Expected messages
 *
 * @example
 * await assertReceivedSequence(server, [
 *   { type: 'ping' },
 *   { type: 'subscribe' }
 * ]);
 */
export async function assertReceivedSequence(server, expectedMessages) {
  for (const expectedMessage of expectedMessages) {
    await expect(server).toReceiveMessage(expectedMessage);
  }
}
