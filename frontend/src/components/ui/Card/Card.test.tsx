import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./Card";

describe("Card", () => {
  it("renders children correctly", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("applies default variant", () => {
    render(<Card data-testid="card">Default</Card>);
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("rounded-lg", "border");
  });

  it("applies bordered variant", () => {
    render(
      <Card variant="bordered" data-testid="card">
        Bordered
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("border-2", "border-primary-500");
  });

  it("applies elevated variant", () => {
    render(
      <Card variant="elevated" data-testid="card">
        Elevated
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("shadow-md");
  });

  it("applies ghost variant", () => {
    render(
      <Card variant="ghost" data-testid="card">
        Ghost
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("border-transparent", "shadow-none");
  });

  it("applies small padding", () => {
    render(
      <Card padding="sm" data-testid="card">
        Small
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("p-4");
  });

  it("applies medium padding by default", () => {
    render(<Card data-testid="card">Medium</Card>);
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("p-6");
  });

  it("applies large padding", () => {
    render(
      <Card padding="lg" data-testid="card">
        Large
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("p-8");
  });

  it("applies no padding", () => {
    render(
      <Card padding="none" data-testid="card">
        None
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).not.toHaveClass("p-4", "p-6", "p-8");
  });

  it("applies custom className", () => {
    render(
      <Card className="custom-class" data-testid="card">
        Custom
      </Card>,
    );
    const card = screen.getByTestId("card");
    expect(card).toHaveClass("custom-class");
  });

  it("renders CardHeader correctly", () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText("Header content")).toBeInTheDocument();
  });

  it("renders CardTitle correctly", () => {
    render(<CardTitle>Title</CardTitle>);
    const title = screen.getByText("Title");
    expect(title.tagName).toBe("H3");
    expect(title).toHaveClass("text-2xl", "font-semibold");
  });

  it("renders CardDescription correctly", () => {
    render(<CardDescription>Description text</CardDescription>);
    const desc = screen.getByText("Description text");
    expect(desc.tagName).toBe("P");
    expect(desc).toHaveClass("text-sm");
  });

  it("renders CardContent correctly", () => {
    render(<CardContent>Content</CardContent>);
    expect(screen.getByText("Content")).toBeInTheDocument();
  });

  it("renders CardFooter correctly", () => {
    render(<CardFooter>Footer</CardFooter>);
    expect(screen.getByText("Footer")).toBeInTheDocument();
  });

  it("renders complete card composition", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
          <CardDescription>Card Description</CardDescription>
        </CardHeader>
        <CardContent>Card Content</CardContent>
        <CardFooter>Card Footer</CardFooter>
      </Card>,
    );

    expect(screen.getByText("Card Title")).toBeInTheDocument();
    expect(screen.getByText("Card Description")).toBeInTheDocument();
    expect(screen.getByText("Card Content")).toBeInTheDocument();
    expect(screen.getByText("Card Footer")).toBeInTheDocument();
  });
});
