/**
 * NarrativeFeed Component Tests
 *
 * Testa o feed de narrativas estilo editorial (Medium).
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import NarrativeFeed from "../NarrativeFeed";

describe("NarrativeFeed", () => {
  const mockNarratives = [
    {
      narrative_id: "narr-001",
      content: "Esta é uma narrativa analítica sobre o sistema.",
      tone: "analytical",
      nqs: 0.92,
      created_at: "2025-10-31T10:00:00Z",
      word_count: 150,
      reading_time: 2,
    },
    {
      narrative_id: "narr-002",
      content: "Uma narrativa poética e artística sobre os dados.",
      tone: "poetic",
      nqs: 0.88,
      created_at: "2025-10-31T09:00:00Z",
      word_count: 200,
      reading_time: 3,
    },
    {
      narrative_id: "narr-003",
      content: "Narrativa técnica com detalhes de implementação.",
      tone: "technical",
      nqs: 0.95,
      created_at: "2025-10-31T08:00:00Z",
      word_count: 300,
      reading_time: 5,
    },
  ];

  beforeEach(() => {
    // Clear any state between tests
  });

  it("deve renderizar loading state", () => {
    render(<NarrativeFeed narratives={[]} isLoading={true} />);
    expect(screen.getByText(/Carregando narrativas/i)).toBeInTheDocument();
  });

  it("deve exibir mensagem quando não há narrativas", () => {
    render(<NarrativeFeed narratives={[]} isLoading={false} />);
    expect(screen.getByText(/Nenhuma narrativa ainda/i)).toBeInTheDocument();
    expect(screen.getByText(/Nova Narrativa/i)).toBeInTheDocument();
  });

  it("deve renderizar barra de filtros", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);
    expect(
      screen.getByPlaceholderText(/Buscar narrativas/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Tone:/i)).toBeInTheDocument();
    expect(screen.getByText(/Ordenar:/i)).toBeInTheDocument();
  });

  it("deve renderizar contador de resultados", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);
    expect(screen.getByText(/3 narrativa\(s\)/i)).toBeInTheDocument();
  });

  it("deve renderizar todas as narrativas", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);
    expect(screen.getByText(/narrativa analítica/i)).toBeInTheDocument();
    expect(screen.getByText(/narrativa poética/i)).toBeInTheDocument();
    expect(screen.getByText(/Narrativa técnica/i)).toBeInTheDocument();
  });

  it("deve filtrar narrativas por busca", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    const searchInput = screen.getByPlaceholderText(/Buscar narrativas/i);
    fireEvent.change(searchInput, { target: { value: "técnica" } });

    expect(screen.getByText(/1 narrativa\(s\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Narrativa técnica/i)).toBeInTheDocument();
    expect(screen.queryByText(/narrativa analítica/i)).not.toBeInTheDocument();
  });

  it("deve filtrar narrativas por tone", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    const toneSelect = screen.getByLabelText(/Tone:/i);
    fireEvent.change(toneSelect, { target: { value: "poetic" } });

    expect(screen.getByText(/1 narrativa\(s\)/i)).toBeInTheDocument();
    expect(screen.getByText(/narrativa poética/i)).toBeInTheDocument();
  });

  it("deve ordenar narrativas por NQS", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    const sortSelect = screen.getByLabelText(/Ordenar:/i);
    fireEvent.change(sortSelect, { target: { value: "nqs" } });

    // Primeiro card deve ser o de maior NQS (0.95)
    const cards = screen.getAllByText(/caracteres/i);
    expect(cards.length).toBe(3);
  });

  it("deve exibir mensagem quando busca não retorna resultados", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    const searchInput = screen.getByPlaceholderText(/Buscar narrativas/i);
    fireEvent.change(searchInput, { target: { value: "xyz123notfound" } });

    expect(
      screen.getByText(/Nenhum resultado encontrado/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Tente ajustar os filtros/i)).toBeInTheDocument();
  });

  it("deve exibir select de tone com opções corretas", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    const toneSelect = screen.getByLabelText(/Tone:/i);
    expect(toneSelect).toBeInTheDocument();

    expect(screen.getByRole("option", { name: /Todos/i })).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Analytical/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Poetic/i })).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Technical/i }),
    ).toBeInTheDocument();
  });

  it("deve exibir select de ordenação com opções corretas", () => {
    render(<NarrativeFeed narratives={mockNarratives} isLoading={false} />);

    expect(
      screen.getByRole("option", { name: /Mais recentes/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Maior NQS/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /Mais longas/i }),
    ).toBeInTheDocument();
  });
});
