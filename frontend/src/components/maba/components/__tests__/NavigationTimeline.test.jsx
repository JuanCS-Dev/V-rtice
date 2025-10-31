/**
 * NavigationTimeline Component Tests
 *
 * Testa o componente de timeline de navegações do MABA.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import NavigationTimeline from "../NavigationTimeline";

describe("NavigationTimeline", () => {
  const mockSessions = [
    {
      session_id: "sess-001",
      current_url: "https://example.com",
      navigations: [
        {
          timestamp: "2025-10-31T10:15:00Z",
          action: "click",
          url: "https://example.com/page1",
          target: "button#submit",
          success: true,
          duration: 250,
        },
        {
          timestamp: "2025-10-31T10:10:00Z",
          action: "navigate",
          url: "https://example.com",
          success: true,
          duration: 150,
        },
      ],
    },
    {
      session_id: "sess-002",
      current_url: "https://test.com",
      navigations: [
        {
          timestamp: "2025-10-31T10:05:00Z",
          action: "type",
          url: "https://test.com/form",
          target: "input#email",
          value: "test@example.com",
          success: true,
          duration: 100,
        },
        {
          timestamp: "2025-10-31T10:00:00Z",
          action: "screenshot",
          url: "https://test.com",
          success: false,
          error: "Timeout exceeded",
          duration: 5000,
        },
      ],
    },
  ];

  it("deve renderizar loading state", () => {
    render(<NavigationTimeline sessions={[]} isLoading={true} />);
    expect(screen.getByText(/Carregando timeline/i)).toBeInTheDocument();
  });

  it("deve exibir mensagem quando não há sessões", () => {
    render(<NavigationTimeline sessions={[]} isLoading={false} />);
    expect(
      screen.getByText(/Nenhuma navegação registrada ainda/i),
    ).toBeInTheDocument();
  });

  it("deve renderizar timeline com navegações", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText(/Timeline de Navegações/i)).toBeInTheDocument();
    expect(screen.getByText(/\(4\)/i)).toBeInTheDocument(); // 4 navegações totais
  });

  it("deve renderizar botões de filtro", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText("Todas")).toBeInTheDocument();
    expect(screen.getByText(/Sucesso/i)).toBeInTheDocument();
    expect(screen.getByText(/Erros/i)).toBeInTheDocument();
  });

  it("deve exibir tipos de ação diferentes", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText("Click")).toBeInTheDocument();
    expect(screen.getByText("Navigate")).toBeInTheDocument();
    expect(screen.getByText("Type")).toBeInTheDocument();
    expect(screen.getByText("Screenshot")).toBeInTheDocument();
  });

  it("deve exibir URLs das navegações", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(
      screen.getByText(/https:\/\/example.com\/page1/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/https:\/\/test.com\/form/i)).toBeInTheDocument();
  });

  it("deve exibir targets quando presentes", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText(/button#submit/i)).toBeInTheDocument();
    expect(screen.getByText(/input#email/i)).toBeInTheDocument();
  });

  it("deve exibir status de sucesso/erro", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    const successBadges = screen.getAllByText(/Sucesso/i);
    expect(successBadges.length).toBeGreaterThan(0);
    expect(screen.getByText(/Erro: Timeout exceeded/i)).toBeInTheDocument();
  });

  it("deve filtrar navegações por sucesso", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);

    const successButton = screen.getByText(/✅ Sucesso/i);
    fireEvent.click(successButton);

    // Deve mostrar apenas as 3 navegações bem-sucedidas
    expect(screen.getByText(/\(3\)/i)).toBeInTheDocument();
  });

  it("deve filtrar navegações por erro", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);

    const errorButton = screen.getByText(/❌ Erros/i);
    fireEvent.click(errorButton);

    // Deve mostrar apenas 1 navegação com erro
    expect(screen.getByText(/\(1\)/i)).toBeInTheDocument();
  });

  it("deve exibir duração quando presente", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText(/Duração: 250ms/i)).toBeInTheDocument();
  });

  it("deve exibir session info", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText(/Session #sess-001/i)).toBeInTheDocument();
    expect(screen.getByText(/Session #sess-002/i)).toBeInTheDocument();
  });

  it("deve exibir value quando presente (type action)", () => {
    render(<NavigationTimeline sessions={mockSessions} isLoading={false} />);
    expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
  });
});
