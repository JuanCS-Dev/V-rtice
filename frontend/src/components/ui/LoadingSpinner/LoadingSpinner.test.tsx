import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingSpinner } from "./LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders with default label", () => {
    render(<LoadingSpinner />);
    expect(screen.getByLabelText("Loading...")).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    render(<LoadingSpinner label="Please wait" />);
    expect(screen.getByLabelText("Please wait")).toBeInTheDocument();
  });

  it('has role="status"', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it('has aria-live="polite"', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole("status");
    expect(spinner).toHaveAttribute("aria-live", "polite");
  });

  it("applies small size", () => {
    render(<LoadingSpinner size="sm" />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("h-4", "w-4");
  });

  it("applies medium size by default", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("h-6", "w-6");
  });

  it("applies large size", () => {
    render(<LoadingSpinner size="lg" />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("h-8", "w-8");
  });

  it("applies extra large size", () => {
    render(<LoadingSpinner size="xl" />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("h-12", "w-12");
  });

  it("applies primary variant by default", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("text-primary-500");
  });

  it("applies secondary variant", () => {
    render(<LoadingSpinner variant="secondary" />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("text-gray-500");
  });

  it("applies white variant", () => {
    render(<LoadingSpinner variant="white" />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("text-white");
  });

  it("has animation class", () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole("status").firstChild;
    expect(spinner).toHaveClass("animate-spin");
  });

  it("applies custom className", () => {
    render(<LoadingSpinner className="custom" />);
    expect(screen.getByRole("status")).toHaveClass("custom");
  });
});
