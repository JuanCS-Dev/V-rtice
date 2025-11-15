import { renderHook, act, waitFor } from "@testing-library/react";
import { useDarkWebAccess } from "./useDarkWebAccess";
import { vi } from "vitest";

describe("useDarkWebAccess", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, "alert").mockImplementation(() => {}); // Mock window.alert
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("should return initial state correctly", () => {
    const { result } = renderHook(() => useDarkWebAccess());

    expect(result.current.isRequestingAccess).toBe(false);
    expect(result.current.accessStatus).toBe(null);
  });

  it("should set isRequestingAccess and accessStatus to pending when requestAccess is called", async () => {
    const { result } = renderHook(() => useDarkWebAccess());

    await act(async () => {
      result.current.requestAccess();
    });

    expect(result.current.isRequestingAccess).toBe(true);
    expect(result.current.accessStatus).toBe("pending");
  });

  it("should call alert and reset state after timeout", async () => {
    const { result } = renderHook(() => useDarkWebAccess());

    act(() => {
      result.current.requestAccess();
    });

    expect(result.current.isRequestingAccess).toBe(true);
    expect(result.current.accessStatus).toBe("pending");

    act(() => {
      vi.advanceTimersByTime(1500);
    });

    expect(window.alert).toHaveBeenCalledWith(
      "Funcionalidade em desenvolvimento - Requer autorização especial",
    );
    expect(result.current.isRequestingAccess).toBe(false);
    expect(result.current.accessStatus).toBe("denied");
  });
});
