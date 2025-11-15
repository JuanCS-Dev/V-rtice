import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Input } from "./Input";

describe("Input", () => {
  it("renders correctly", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(<Input label="Username" />);
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
  });

  it("shows required asterisk when required", () => {
    render(<Input label="Email" required />);
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("renders with helper text", () => {
    render(<Input helperText="Must be at least 8 characters" />);
    expect(
      screen.getByText("Must be at least 8 characters"),
    ).toBeInTheDocument();
  });

  it("renders with error", () => {
    render(<Input error="This field is required" />);
    const error = screen.getByRole("alert");
    expect(error).toHaveTextContent("This field is required");
  });

  it("applies error variant when error is present", () => {
    render(<Input error="Error" data-testid="input" />);
    const input = screen.getByTestId("input");
    expect(input).toHaveClass("border-red-500");
  });

  it("hides helper text when error is shown", () => {
    render(<Input helperText="Helper" error="Error" />);
    expect(screen.queryByText("Helper")).not.toBeInTheDocument();
    expect(screen.getByText("Error")).toBeInTheDocument();
  });

  it("applies small size", () => {
    render(<Input inputSize="sm" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveClass("h-8");
  });

  it("applies medium size by default", () => {
    render(<Input data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveClass("h-10");
  });

  it("applies large size", () => {
    render(<Input inputSize="lg" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveClass("h-12");
  });

  it("handles onChange events", async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    render(<Input onChange={handleChange} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "test");

    expect(handleChange).toHaveBeenCalled();
    expect(input).toHaveValue("test");
  });

  it("is disabled when disabled prop is true", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("applies custom className", () => {
    render(<Input className="custom-class" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveClass("custom-class");
  });

  it("forwards ref correctly", () => {
    const ref = vi.fn();
    render(<Input ref={ref} />);
    expect(ref).toHaveBeenCalled();
  });

  it("supports different input types", () => {
    render(<Input type="email" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveAttribute("type", "email");
  });

  it("has proper ARIA attributes", () => {
    render(<Input label="Name" error="Required" />);
    const input = screen.getByLabelText("Name");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute("aria-describedby");
  });

  it("associates label with input via htmlFor", () => {
    render(<Input label="Email" id="email-input" />);
    const label = screen.getByText("Email");
    const input = screen.getByLabelText("Email");
    expect(label).toHaveAttribute("for", input.id);
  });

  it("supports success variant", () => {
    render(<Input variant="success" data-testid="input" />);
    expect(screen.getByTestId("input")).toHaveClass("border-primary-500");
  });

  it("supports placeholder text", () => {
    render(<Input placeholder="Enter your name" />);
    expect(screen.getByPlaceholderText("Enter your name")).toBeInTheDocument();
  });

  it("supports defaultValue", () => {
    render(<Input defaultValue="Default text" />);
    expect(screen.getByRole("textbox")).toHaveValue("Default text");
  });

  it("supports controlled value", () => {
    const { rerender } = render(<Input value="Initial" onChange={() => {}} />);
    expect(screen.getByRole("textbox")).toHaveValue("Initial");

    rerender(<Input value="Updated" onChange={() => {}} />);
    expect(screen.getByRole("textbox")).toHaveValue("Updated");
  });
});
