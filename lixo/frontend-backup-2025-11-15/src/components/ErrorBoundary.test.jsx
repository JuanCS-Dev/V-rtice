/**
 * ErrorBoundary Component Tests
 *
 * Tests for error boundary component
 */

import { describe, it, expect, vi, beforeAll, afterAll } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ErrorBoundary from "./ErrorBoundary";

// Component that throws an error
const ThrowError = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error("Test error");
  }
  return <div>No error</div>;
};

describe("ErrorBoundary", () => {
  // Suppress console.error for these tests
  const originalError = console.error;
  beforeAll(() => {
    console.error = vi.fn();
  });

  afterAll(() => {
    console.error = originalError;
  });

  it("should render children when there is no error", () => {
    render(
      <ErrorBoundary>
        <div>Test content</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("should render error UI when child component throws", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/Algo deu errado/i)).toBeInTheDocument();
  });

  it("should display custom title when provided", () => {
    render(
      <ErrorBoundary title="Custom Error Title">
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Custom Error Title")).toBeInTheDocument();
  });

  it("should display custom message when provided", () => {
    const customMessage = "This is a custom error message";

    render(
      <ErrorBoundary message={customMessage}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText(customMessage)).toBeInTheDocument();
  });

  it("should show retry button", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/Tentar Novamente/i)).toBeInTheDocument();
  });

  it("should show back to home button", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/Voltar ao Início/i)).toBeInTheDocument();
  });

  it("should reset error state when retry is clicked", async () => {
    const user = userEvent.setup();
    let shouldThrow = true;

    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={shouldThrow} />
      </ErrorBoundary>,
    );

    // Error should be shown
    expect(screen.getByText(/Algo deu errado/i)).toBeInTheDocument();

    // Fix the error
    shouldThrow = false;

    // Click retry
    const retryButton = screen.getByText(/Tentar Novamente/i);
    await user.click(retryButton);

    // Should show children again
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={shouldThrow} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("No error")).toBeInTheDocument();
  });

  it("should call onReset callback when provided", async () => {
    const user = userEvent.setup();
    const onReset = vi.fn();

    render(
      <ErrorBoundary onReset={onReset}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    const retryButton = screen.getByText(/Tentar Novamente/i);
    await user.click(retryButton);

    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("should track error count", () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>,
    );

    // Trigger multiple errors
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Should show warning for multiple errors
    expect(screen.getByText(/Múltiplos erros detectados/i)).toBeInTheDocument();
  });

  it("should display error context when provided", () => {
    render(
      <ErrorBoundary context="test-context">
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Error UI should be shown
    expect(screen.getByText(/Algo deu errado/i)).toBeInTheDocument();
  });

  it("should use custom fallback when provided", () => {
    const customFallback = ({ error, resetError }) => (
      <div>
        <p>Custom Fallback: {error?.message || "Unknown error"}</p>
        <button onClick={resetError}>Custom Reset</button>
      </div>
    );

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/Custom Fallback:/i)).toBeInTheDocument();
    expect(screen.getByText("Custom Reset")).toBeInTheDocument();
  });

  it("should log error to telemetry service", () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );

    // Should attempt to send error to /api/errors/log
    expect(fetchSpy).toHaveBeenCalledWith(
      "/api/errors/log",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );

    fetchSpy.mockRestore();
  });
});
