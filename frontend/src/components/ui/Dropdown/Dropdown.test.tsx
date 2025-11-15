import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  Dropdown,
  DropdownTrigger,
  DropdownContent,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator,
  DropdownCheckboxItem,
} from "./Dropdown";

describe("Dropdown", () => {
  it("renders trigger button", () => {
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem>Item 1</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    expect(screen.getByRole("button", { name: /menu/i })).toBeInTheDocument();
  });

  it("opens dropdown when trigger is clicked", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Open</DropdownTrigger>
        <DropdownContent>
          <DropdownItem>Action</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(
      screen.getByRole("menuitem", { name: /action/i }),
    ).toBeInTheDocument();
  });

  it("renders dropdown items", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem>Edit</DropdownItem>
          <DropdownItem>Delete</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("menuitem", { name: /edit/i })).toBeInTheDocument();
    expect(
      screen.getByRole("menuitem", { name: /delete/i }),
    ).toBeInTheDocument();
  });

  it("renders dropdown label", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownLabel>Actions</DropdownLabel>
          <DropdownItem>Item</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByText("Actions")).toBeInTheDocument();
  });

  it("renders separator", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem>Item 1</DropdownItem>
          <DropdownSeparator />
          <DropdownItem>Item 2</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    const separator = screen.getByRole("separator");
    expect(separator).toBeInTheDocument();
  });

  it("renders checkbox item", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownCheckboxItem>Option</DropdownCheckboxItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    expect(screen.getByRole("menuitemcheckbox")).toBeInTheDocument();
  });

  it("calls onSelect when item is clicked", async () => {
    const handleSelect = vi.fn();
    const user = userEvent.setup();

    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem onSelect={handleSelect}>Action</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    await user.click(screen.getByRole("menuitem"));

    expect(handleSelect).toHaveBeenCalled();
  });

  it("supports disabled items", async () => {
    const user = userEvent.setup();
    render(
      <Dropdown>
        <DropdownTrigger>Menu</DropdownTrigger>
        <DropdownContent>
          <DropdownItem disabled>Disabled</DropdownItem>
        </DropdownContent>
      </Dropdown>,
    );

    await user.click(screen.getByRole("button"));
    const item = screen.getByRole("menuitem", { name: /disabled/i });
    expect(item).toHaveAttribute("data-disabled");
  });
});
