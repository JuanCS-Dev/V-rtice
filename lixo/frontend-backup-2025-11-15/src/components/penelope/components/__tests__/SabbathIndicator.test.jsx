/**
 * SabbathIndicator Component Tests
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import SabbathIndicator from "../SabbathIndicator";

describe("SabbathIndicator", () => {
  it("deve renderizar quando isSabbath = true", () => {
    render(<SabbathIndicator isSabbath={true} />);
    expect(screen.getByText(/Modo Sabbath Ativo/)).toBeInTheDocument();
  });

  it("deve renderizar ícone de pomba quando ativo", () => {
    render(<SabbathIndicator isSabbath={true} />);
    expect(screen.getByText(/🕊️/)).toBeInTheDocument();
  });

  it("deve mostrar mensagem de reflexão", () => {
    render(<SabbathIndicator isSabbath={true} />);
    expect(screen.getByText(/dia de descanso/i)).toBeInTheDocument();
  });

  it("não deve renderizar quando isSabbath = false", () => {
    const { container } = render(<SabbathIndicator isSabbath={false} />);
    expect(container.firstChild).toBeNull();
  });
});
