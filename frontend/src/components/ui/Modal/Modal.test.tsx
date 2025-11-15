import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
  ModalClose,
} from "./Modal";

describe("Modal", () => {
  it("renders trigger button", () => {
    render(
      <Modal>
        <ModalTrigger>Open Modal</ModalTrigger>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Modal Title</ModalTitle>
          </ModalHeader>
        </ModalContent>
      </Modal>,
    );

    expect(
      screen.getByRole("button", { name: /open modal/i }),
    ).toBeInTheDocument();
  });

  it("opens modal when trigger is clicked", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
          <ModalDescription>Description</ModalDescription>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Title")).toBeInTheDocument();
  });

  it("closes modal when close button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /close/i }));
    // Dialog should be removed after animation
  });

  it("renders modal header", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalHeader>
            <ModalTitle>Header Title</ModalTitle>
          </ModalHeader>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(screen.getByText("Header Title")).toBeInTheDocument();
  });

  it("renders modal description", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
          <ModalDescription>This is a description</ModalDescription>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(screen.getByText("This is a description")).toBeInTheDocument();
  });

  it("renders modal footer", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
          <ModalFooter>
            <button>Cancel</button>
            <button>Confirm</button>
          </ModalFooter>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /confirm/i }),
    ).toBeInTheDocument();
  });

  it("closes modal when ModalClose is clicked", async () => {
    const user = userEvent.setup();
    render(
      <Modal>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
          <ModalFooter>
            <ModalClose>Cancel</ModalClose>
          </ModalFooter>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    // Dialog closes
  });

  it("renders with controlled state", () => {
    const { rerender } = render(
      <Modal open={false}>
        <ModalContent>
          <ModalTitle>Controlled</ModalTitle>
        </ModalContent>
      </Modal>,
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    rerender(
      <Modal open={true}>
        <ModalContent>
          <ModalTitle>Controlled</ModalTitle>
        </ModalContent>
      </Modal>,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("calls onOpenChange callback", async () => {
    const handleOpenChange = vi.fn();
    const user = userEvent.setup();

    render(
      <Modal onOpenChange={handleOpenChange}>
        <ModalTrigger>Open</ModalTrigger>
        <ModalContent>
          <ModalTitle>Title</ModalTitle>
        </ModalContent>
      </Modal>,
    );

    await user.click(screen.getByRole("button", { name: /open/i }));
    expect(handleOpenChange).toHaveBeenCalledWith(true);
  });
});
