import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "./Badge";

describe("Badge", () => {
  it("renders children correctly", () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("applies default variant", () => {
    render(<Badge data-testid="badge">Default</Badge>);
    expect(screen.getByTestId("badge")).toHaveClass("bg-primary-500");
  });

  it("applies secondary variant", () => {
    render(
      <Badge variant="secondary" data-testid="badge">
        Secondary
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("bg-gray-200");
  });

  it("applies success variant", () => {
    render(
      <Badge variant="success" data-testid="badge">
        Success
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("bg-green-600");
  });

  it("applies warning variant", () => {
    render(
      <Badge variant="warning" data-testid="badge">
        Warning
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("bg-amber-500");
  });

  it("applies danger variant", () => {
    render(
      <Badge variant="danger" data-testid="badge">
        Danger
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("bg-red-600");
  });

  it("applies info variant", () => {
    render(
      <Badge variant="info" data-testid="badge">
        Info
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("bg-blue-600");
  });

  it("applies outline variant", () => {
    render(
      <Badge variant="outline" data-testid="badge">
        Outline
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("border-current");
  });

  it("applies custom className", () => {
    render(
      <Badge className="custom" data-testid="badge">
        Custom
      </Badge>,
    );
    expect(screen.getByTestId("badge")).toHaveClass("custom");
  });
});
