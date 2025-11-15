/**
 * Endpoints Configuration Tests
 * ==============================
 *
 * Test suite for config/endpoints.ts
 * Target: 100% coverage
 * Governed by: Constituição Vértice v2.5 - ADR-004
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock import.meta.env
const mockEnv = {
  PROD: false,
  DEV: true,
  VITE_API_GATEWAY_URL: "http://test-gateway:8000",
  VITE_MAXIMUS_CORE_URL: "http://test-maximus:8001",
  VITE_API_KEY: "test-key",
};

vi.mock("import.meta", () => ({
  env: mockEnv,
}));

import {
  ServiceEndpoints,
  WebSocketEndpoints,
  AuthConfig,
  validateConfiguration,
  getServiceEndpoint,
  getWebSocketEndpoint,
  httpToWs,
  ConfigurationError,
} from "../endpoints";

describe("ServiceEndpoints", () => {
  it("should have apiGateway configured", () => {
    expect(ServiceEndpoints.apiGateway).toBeDefined();
  });

  it("should have maximus services configured", () => {
    expect(ServiceEndpoints.maximus.core).toBeDefined();
    expect(ServiceEndpoints.maximus.orchestrator).toBeDefined();
  });

  it("should have offensive services configured", () => {
    expect(ServiceEndpoints.offensive.gateway).toBeDefined();
    expect(ServiceEndpoints.offensive.networkRecon).toBeDefined();
  });
});

describe("WebSocketEndpoints", () => {
  it("should have WebSocket URLs configured", () => {
    expect(WebSocketEndpoints.maximus.stream).toBeDefined();
    expect(WebSocketEndpoints.cockpit.verdicts).toBeDefined();
  });
});

describe("AuthConfig", () => {
  it("should have auth configuration", () => {
    expect(AuthConfig.apiKey).toBeDefined();
    expect(AuthConfig.google).toBeDefined();
  });
});

describe("validateConfiguration", () => {
  it("should pass validation in development mode", () => {
    mockEnv.DEV = true;
    mockEnv.PROD = false;

    expect(() => validateConfiguration()).not.toThrow();
  });

  it("should throw ConfigurationError if required vars missing in production", () => {
    mockEnv.PROD = true;
    mockEnv.DEV = false;
    mockEnv.VITE_API_GATEWAY_URL = undefined;

    expect(() => validateConfiguration()).toThrow(ConfigurationError);
  });
});

describe("getServiceEndpoint", () => {
  it("should return endpoint for valid path", () => {
    const endpoint = getServiceEndpoint("apiGateway");
    expect(endpoint).toBe(ServiceEndpoints.apiGateway);
  });

  it("should return nested endpoint", () => {
    const endpoint = getServiceEndpoint("maximus.core");
    expect(endpoint).toBe(ServiceEndpoints.maximus.core);
  });

  it("should throw ConfigurationError for invalid path", () => {
    expect(() => getServiceEndpoint("nonexistent")).toThrow(ConfigurationError);
  });

  it("should throw ConfigurationError for non-string endpoint", () => {
    expect(() => getServiceEndpoint("maximus")).toThrow(ConfigurationError);
  });
});

describe("getWebSocketEndpoint", () => {
  it("should return WebSocket endpoint for valid path", () => {
    const endpoint = getWebSocketEndpoint("maximus.stream");
    expect(endpoint).toBe(WebSocketEndpoints.maximus.stream);
  });

  it("should throw ConfigurationError for invalid path", () => {
    expect(() => getWebSocketEndpoint("invalid.path")).toThrow(
      ConfigurationError,
    );
  });
});

describe("httpToWs", () => {
  it("should convert http to ws", () => {
    expect(httpToWs("http://34.148.161.131:8000")).toBe(
      "ws://34.148.161.131:8000",
    );
  });

  it("should convert https to wss", () => {
    expect(httpToWs("https://secure.example.com")).toBe(
      "wss://secure.example.com",
    );
  });
});

describe("ConfigurationError", () => {
  it("should be throwable", () => {
    expect(() => {
      throw new ConfigurationError("Test error");
    }).toThrow(ConfigurationError);
  });

  it("should have correct name", () => {
    const error = new ConfigurationError("Test");
    expect(error.name).toBe("ConfigurationError");
  });
});
