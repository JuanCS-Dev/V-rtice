/**
 * VirtualizedExecutionsList Tests
 * Testing virtual scrolling with large datasets
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { VirtualizedExecutionsList } from "../VirtualizedExecutionsList";

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

describe("VirtualizedExecutionsList", () => {
  const mockExecutions = [
    {
      id: "exec-001",
      type: "NMAP_SCAN",
      status: "running",
      target: "192.168.1.1",
      progress: 45,
      timestamp: new Date().toISOString(),
    },
    {
      id: "exec-002",
      type: "WEB_ATTACK",
      status: "completed",
      target: "https://example.com",
      progress: 100,
      findings: [
        { severity: "high", description: "SQL Injection found" },
        { severity: "medium", description: "XSS vulnerability" },
      ],
      timestamp: new Date().toISOString(),
    },
  ];

  it("renders without crashing", () => {
    render(<VirtualizedExecutionsList executions={[]} />);
    expect(screen.getByText(/no executions to display/i)).toBeInTheDocument();
  });

  it("displays empty state when no executions", () => {
    render(<VirtualizedExecutionsList executions={[]} />);
    expect(screen.getByText(/no executions to display/i)).toBeInTheDocument();
  });

  it("renders executions with virtual scrolling", () => {
    render(<VirtualizedExecutionsList executions={mockExecutions} />);
    expect(screen.getByTestId("virtualized-list")).toBeInTheDocument();
  });

  it("displays execution status correctly", () => {
    render(<VirtualizedExecutionsList executions={mockExecutions} />);
    expect(screen.getByText("RUNNING")).toBeInTheDocument();
    expect(screen.getByText("COMPLETED")).toBeInTheDocument();
  });

  it("displays execution targets", () => {
    render(<VirtualizedExecutionsList executions={mockExecutions} />);
    expect(screen.getByText("192.168.1.1")).toBeInTheDocument();
    expect(screen.getByText("https://example.com")).toBeInTheDocument();
  });

  it("displays progress bars when progress is available", () => {
    render(<VirtualizedExecutionsList executions={mockExecutions} />);
    expect(screen.getByText("45%")).toBeInTheDocument();
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("displays findings when available", () => {
    render(<VirtualizedExecutionsList executions={mockExecutions} />);
    expect(screen.getByText("SQL Injection found")).toBeInTheDocument();
    expect(screen.getByText("XSS vulnerability")).toBeInTheDocument();
  });

  it("handles large datasets efficiently (1000+ items)", () => {
    const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
      id: `exec-${i.toString().padStart(4, "0")}`,
      type: "SCAN",
      status: "running",
      target: `192.168.1.${i % 255}`,
      progress: i % 100,
      timestamp: new Date().toISOString(),
    }));

    const { container } = render(
      <VirtualizedExecutionsList executions={largeDataset} />,
    );

    // Should render virtualized list (only renders visible items)
    expect(screen.getByTestId("virtualized-list")).toBeInTheDocument();

    // Should NOT render all 1000 items (performance check)
    const renderedItems = container.querySelectorAll(
      '[class*="executionCard"]',
    );
    expect(renderedItems.length).toBeLessThan(100); // Only renders visible window
  });

  it("displays statistics bar with correct counts", () => {
    const executions = [
      {
        id: "exec-1",
        status: "running",
        type: "SCAN",
        target: "test1",
        timestamp: new Date().toISOString(),
      },
      {
        id: "exec-2",
        status: "running",
        type: "SCAN",
        target: "test2",
        timestamp: new Date().toISOString(),
      },
      {
        id: "exec-3",
        status: "completed",
        type: "SCAN",
        target: "test3",
        timestamp: new Date().toISOString(),
      },
      {
        id: "exec-4",
        status: "failed",
        type: "SCAN",
        target: "test4",
        timestamp: new Date().toISOString(),
      },
    ];

    render(<VirtualizedExecutionsList executions={executions} />);

    expect(screen.getByText("Total:")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument(); // Total value
    expect(screen.getByText("Running:")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // Running value
    expect(screen.getByText("Completed:")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // Completed value
  });

  it("renders container with stats", () => {
    const { container } = render(
      <VirtualizedExecutionsList executions={mockExecutions} />,
    );

    // Check that container and stats exist
    expect(container.querySelector('[class*="container"]')).toBeInTheDocument();
    expect(container.querySelector('[class*="statsBar"]')).toBeInTheDocument();
  });
});
