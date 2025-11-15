import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Alert, AlertTitle, AlertDescription } from "./Alert";

describe("Alert", () => {
  it("renders children correctly", () => {
    render(<Alert>Alert message</Alert>);
    expect(screen.getByText("Alert message")).toBeInTheDocument();
  });

  it("renders with title", () => {
    render(<Alert title="Warning">Message</Alert>);
    expect(screen.getByText("Warning")).toBeInTheDocument();
  });

  it('has role="alert"', () => {
    render(<Alert>Message</Alert>);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("applies default variant", () => {
    render(<Alert data-testid="alert">Default</Alert>);
    expect(screen.getByTestId("alert")).toHaveClass("bg-gray-50");
  });

  it("applies success variant", () => {
    render(
      <Alert variant="success" data-testid="alert">
        Success
      </Alert>,
    );
    expect(screen.getByTestId("alert")).toHaveClass("bg-green-50");
  });

  it("applies warning variant", () => {
    render(
      <Alert variant="warning" data-testid="alert">
        Warning
      </Alert>,
    );
    expect(screen.getByTestId("alert")).toHaveClass("bg-amber-50");
  });

  it("applies error variant", () => {
    render(
      <Alert variant="error" data-testid="alert">
        Error
      </Alert>,
    );
    expect(screen.getByTestId("alert")).toHaveClass("bg-red-50");
  });

  it("applies info variant", () => {
    render(
      <Alert variant="info" data-testid="alert">
        Info
      </Alert>,
    );
    expect(screen.getByTestId("alert")).toHaveClass("bg-blue-50");
  });

  it("renders close button when onClose provided", () => {
    render(<Alert onClose={() => {}}>Message</Alert>);
    expect(screen.getByLabelText("Close alert")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", async () => {
    const handleClose = vi.fn();
    const user = userEvent.setup();
    render(<Alert onClose={handleClose}>Message</Alert>);

    await user.click(screen.getByLabelText("Close alert"));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it("renders AlertTitle correctly", () => {
    render(<AlertTitle>Title</AlertTitle>);
    const title = screen.getByText("Title");
    expect(title.tagName).toBe("H5");
  });

  it("renders AlertDescription correctly", () => {
    render(<AlertDescription>Description</AlertDescription>);
    expect(screen.getByText("Description")).toBeInTheDocument();
  });

  it("renders complete alert composition", () => {
    render(
      <Alert variant="error" title="Error occurred">
        <AlertDescription>Something went wrong</AlertDescription>
      </Alert>,
    );

    expect(screen.getByText("Error occurred")).toBeInTheDocument();
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });
});
