/**
 * StoryCard Component Tests
 *
 * Testa o card de narrativa estilo Medium.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StoryCard from "../StoryCard";

describe("StoryCard", () => {
  const mockNarrative = {
    narrative_id: "narr-001",
    content:
      "Esta é uma narrativa de teste com conteúdo suficiente para demonstrar as funcionalidades do card. ".repeat(
        5,
      ),
    tone: "analytical",
    nqs: 0.92,
    created_at: "2025-10-31T10:00:00Z",
    word_count: 150,
    reading_time: 2,
  };

  const shortNarrative = {
    narrative_id: "narr-002",
    content: "Narrativa curta.",
    tone: "poetic",
    nqs: 0.88,
    created_at: "2025-10-31T09:00:00Z",
  };

  it("deve renderizar o conteúdo da narrativa", () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText(/narrativa de teste/i)).toBeInTheDocument();
  });

  it("deve renderizar o tone badge", () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText("analytical")).toBeInTheDocument();
  });

  it("deve renderizar NQS badge quando presente", () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText("NQS")).toBeInTheDocument();
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("deve renderizar timestamp formatado", () => {
    render(<StoryCard narrative={mockNarrative} />);
    // Timestamp deve estar no formato relativo ou absoluto
    const timestamp = screen.getByText(/atrás|31/);
    expect(timestamp).toBeInTheDocument();
  });

  it("deve exibir ícone correto por tone", () => {
    const { rerender } = render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText("🔬")).toBeInTheDocument(); // analytical

    rerender(<StoryCard narrative={{ ...mockNarrative, tone: "poetic" }} />);
    expect(screen.getByText("🎭")).toBeInTheDocument(); // poetic

    rerender(<StoryCard narrative={{ ...mockNarrative, tone: "technical" }} />);
    expect(screen.getByText("⚙️")).toBeInTheDocument(); // technical
  });

  it("deve exibir métricas de footer", () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText(/caracteres/i)).toBeInTheDocument();
    expect(screen.getByText(/150 palavras/i)).toBeInTheDocument();
    expect(screen.getByText(/2 min/i)).toBeInTheDocument();
  });

  it("deve exibir ID da narrativa", () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText(/ID:/i)).toBeInTheDocument();
    expect(screen.getByText("narr-001")).toBeInTheDocument();
  });

  it("deve truncar conteúdo longo", () => {
    render(<StoryCard narrative={mockNarrative} />);
    const content = screen.getByText(/narrativa de teste/i);
    expect(content.textContent).toContain("...");
  });

  it('deve exibir botão "Ler mais" quando conteúdo é longo', () => {
    render(<StoryCard narrative={mockNarrative} />);
    expect(screen.getByText(/Ler mais/i)).toBeInTheDocument();
  });

  it('não deve exibir botão "Ler mais" quando conteúdo é curto', () => {
    render(<StoryCard narrative={shortNarrative} />);
    expect(screen.queryByText(/Ler mais/i)).not.toBeInTheDocument();
  });

  it('deve expandir conteúdo ao clicar em "Ler mais"', () => {
    render(<StoryCard narrative={mockNarrative} />);

    const expandButton = screen.getByText(/Ler mais/i);
    fireEvent.click(expandButton);

    expect(screen.getByText(/Recolher/i)).toBeInTheDocument();
  });

  it('deve recolher conteúdo ao clicar em "Recolher"', () => {
    render(<StoryCard narrative={mockNarrative} />);

    const expandButton = screen.getByText(/Ler mais/i);
    fireEvent.click(expandButton);

    const collapseButton = screen.getByText(/Recolher/i);
    fireEvent.click(collapseButton);

    expect(screen.getByText(/Ler mais/i)).toBeInTheDocument();
  });

  it("deve aplicar classe de cor baseada no tone", () => {
    const { container } = render(<StoryCard narrative={mockNarrative} />);
    const card = container.querySelector("article");
    expect(card?.className).toMatch(/blue/i);
  });

  it("deve renderizar sem NQS quando não está presente", () => {
    const narrativeWithoutNqs = { ...mockNarrative, nqs: undefined };
    render(<StoryCard narrative={narrativeWithoutNqs} />);
    expect(screen.queryByText("NQS")).not.toBeInTheDocument();
  });
});
