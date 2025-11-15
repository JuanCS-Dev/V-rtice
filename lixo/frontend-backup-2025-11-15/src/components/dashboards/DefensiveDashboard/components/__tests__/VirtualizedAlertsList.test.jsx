/**
 * VirtualizedAlertsList Tests
 * Testing virtual scrolling with large alert datasets
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { VirtualizedAlertsList } from "../VirtualizedAlertsList";

// Mock react-window to avoid rendering complexity in tests
vi.mock("react-window", () => {
  const MockList = ({ children, itemCount }) => (
    <div data-testid="virtualized-list">
      {Array.from({ length: Math.min(itemCount, 10) }, (_, index) =>
        children({ index, style: {} }),
      )}
    </div>
  );

  return {
    FixedSizeList: MockList,
    List: MockList, // VirtualList component uses "List" export
  };
});

vi.mock("react-virtualized-auto-sizer", () => ({
  default: ({ children }) => children({ height: 600, width: 300 }),
}));

describe("VirtualizedAlertsList", () => {
  const mockAlerts = [
    {
      id: "alert-001",
      type: "INTRUSION_DETECTED",
      severity: "critical",
      message: "Unauthorized access attempt detected",
      source: "192.168.1.100",
      timestamp: new Date().toISOString(),
    },
    {
      id: "alert-002",
      type: "MALWARE_DETECTED",
      severity: "high",
      message: "Suspicious file detected",
      source: "endpoint-42",
      timestamp: new Date().toISOString(),
    },
    {
      id: "alert-003",
      type: "ANOMALY",
      severity: "medium",
      message: "Unusual network traffic pattern",
      source: "firewall-01",
      timestamp: new Date().toISOString(),
    },
  ];

  it("renders without crashing", () => {
    render(<VirtualizedAlertsList alerts={[]} />);
    expect(screen.getByText(/no alerts at this time/i)).toBeInTheDocument();
  });

  it("displays empty state when no alerts", () => {
    render(<VirtualizedAlertsList alerts={[]} />);
    expect(screen.getByText(/all clear/i)).toBeInTheDocument();
  });

  it("renders alerts with virtual scrolling", () => {
    render(<VirtualizedAlertsList alerts={mockAlerts} />);
    expect(screen.getByTestId("virtualized-list")).toBeInTheDocument();
  });

  it("displays alert types correctly", () => {
    render(<VirtualizedAlertsList alerts={mockAlerts} />);
    expect(screen.getByText("INTRUSION_DETECTED")).toBeInTheDocument();
    expect(screen.getByText("MALWARE_DETECTED")).toBeInTheDocument();
    expect(screen.getByText("ANOMALY")).toBeInTheDocument();
  });

  it("displays severity badges", () => {
    render(<VirtualizedAlertsList alerts={mockAlerts} />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
  });

  it("displays alert messages", () => {
    render(<VirtualizedAlertsList alerts={mockAlerts} />);
    expect(
      screen.getByText(/unauthorized access attempt/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/suspicious file detected/i)).toBeInTheDocument();
    expect(screen.getByText(/unusual network traffic/i)).toBeInTheDocument();
  });

  it("displays alert sources", () => {
    render(<VirtualizedAlertsList alerts={mockAlerts} />);
    expect(screen.getByText(/192.168.1.100/)).toBeInTheDocument();
    expect(screen.getByText(/endpoint-42/)).toBeInTheDocument();
    expect(screen.getByText(/firewall-01/)).toBeInTheDocument();
  });

  it("handles large datasets efficiently (1000+ alerts)", () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: `alert-${i.toString().padStart(4, "0")}`,
      type: "TEST_ALERT",
      severity: ["critical", "high", "medium", "low"][i % 4],
      message: `Test alert ${i}`,
      source: `source-${i}`,
      timestamp: new Date().toISOString(),
    }));

    const { container } = render(
      <VirtualizedAlertsList alerts={largeDataset} />,
    );

    // Should render virtualized list (only renders visible items)
    expect(screen.getByTestId("virtualized-list")).toBeInTheDocument();

    // Should NOT render all 1000 items (performance check)
    const renderedItems = container.querySelectorAll('[class*="alertRow"]');
    expect(renderedItems.length).toBeLessThan(100); // Only renders visible window
  });

  it("displays statistics bar with correct severity counts", () => {
    const alerts = [
      {
        id: "alert-1",
        severity: "critical",
        type: "TEST",
        message: "msg1",
        timestamp: new Date().toISOString(),
      },
      {
        id: "alert-2",
        severity: "critical",
        type: "TEST",
        message: "msg2",
        timestamp: new Date().toISOString(),
      },
      {
        id: "alert-3",
        severity: "high",
        type: "TEST",
        message: "msg3",
        timestamp: new Date().toISOString(),
      },
      {
        id: "alert-4",
        severity: "medium",
        type: "TEST",
        message: "msg4",
        timestamp: new Date().toISOString(),
      },
      {
        id: "alert-5",
        severity: "medium",
        type: "TEST",
        message: "msg5",
        timestamp: new Date().toISOString(),
      },
      {
        id: "alert-6",
        severity: "low",
        type: "TEST",
        message: "msg6",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<VirtualizedAlertsList alerts={alerts} />);

    expect(screen.getByText("Total:")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("Critical:")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("applies correct CSS classes for severity levels", () => {
    const { container } = render(<VirtualizedAlertsList alerts={mockAlerts} />);

    const criticalAlert = container.querySelector(
      '[class*="severity-critical"]',
    );
    const highAlert = container.querySelector('[class*="severity-high"]');
    const mediumAlert = container.querySelector('[class*="severity-medium"]');

    expect(criticalAlert).toBeInTheDocument();
    expect(highAlert).toBeInTheDocument();
    expect(mediumAlert).toBeInTheDocument();
  });

  it("renders container with stats", () => {
    const { container } = render(<VirtualizedAlertsList alerts={mockAlerts} />);

    // Check that container and stats exist
    expect(container.querySelector('[class*="container"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="statsBar"]')).toBeInTheDocument();
  });

  it("formats timestamps correctly", () => {
    const testDate = new Date("2025-01-24T10:30:00Z");
    const alerts = [
      {
        id: "alert-test",
        type: "TEST",
        severity: "medium",
        message: "Test",
        timestamp: testDate.toISOString(),
      },
    ];

    render(<VirtualizedAlertsList alerts={alerts} />);

    // Should format time (exact format depends on locale, just check it renders)
    const timeElement = screen.getByText((content) => content.includes(":"));
    expect(timeElement).toBeInTheDocument();
  });
});
