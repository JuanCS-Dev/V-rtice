/**
 * BrowserSessionManager Component Tests
 *
 * Testa o gerenciador de sessões de browser do MABA.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import BrowserSessionManager from "../BrowserSessionManager";

// Mock window.confirm
global.confirm = vi.fn(() => true);

describe("BrowserSessionManager", () => {
  const mockSessions = [
    {
      session_id: "sess-001",
      current_url: "https://example.com",
      status: "active",
      pages_visited: 5,
      elements_learned: 42,
      screenshots: 3,
      created_at: "2025-10-31T10:00:00Z",
      last_navigation: "https://example.com/page1",
    },
    {
      session_id: "sess-002",
      current_url: "https://test.com",
      status: "idle",
      pages_visited: 2,
      elements_learned: 15,
      screenshots: 1,
      created_at: "2025-10-31T09:00:00Z",
    },
  ];

  const mockOnCreateSession = vi.fn();
  const mockOnCloseSession = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("deve renderizar o formulário de nova sessão", () => {
    render(
      <BrowserSessionManager
        sessions={[]}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Nova Sessão de Browser/i)).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/https:\/\/example.com/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Criar Sessão/i)).toBeInTheDocument();
  });

  it("deve exibir loading state", () => {
    render(
      <BrowserSessionManager
        sessions={[]}
        isLoading={true}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Carregando sessões/i)).toBeInTheDocument();
  });

  it("deve exibir mensagem quando não há sessões", () => {
    render(
      <BrowserSessionManager
        sessions={[]}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Nenhuma sessão ativa/i)).toBeInTheDocument();
    expect(screen.getByText(/Crie uma nova sessão acima/i)).toBeInTheDocument();
  });

  it("deve renderizar lista de sessões", () => {
    render(
      <BrowserSessionManager
        sessions={mockSessions}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Sessões Ativas \(2\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Session #sess-001/i)).toBeInTheDocument();
    expect(screen.getByText(/Session #sess-002/i)).toBeInTheDocument();
  });

  it("deve exibir métricas das sessões", () => {
    render(
      <BrowserSessionManager
        sessions={mockSessions}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Páginas:/i)).toBeInTheDocument();
    expect(screen.getByText(/Elementos:/i)).toBeInTheDocument();
    expect(screen.getByText(/Screenshots:/i)).toBeInTheDocument();
  });

  it("deve exibir status das sessões", () => {
    render(
      <BrowserSessionManager
        sessions={mockSessions}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("deve chamar onCreateSession ao submeter formulário", async () => {
    mockOnCreateSession.mockResolvedValue();

    render(
      <BrowserSessionManager
        sessions={[]}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    const input = screen.getByPlaceholderText(/https:\/\/example.com/i);
    const submitButton = screen.getByText(/Criar Sessão/i);

    fireEvent.change(input, { target: { value: "https://newsite.com" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnCreateSession).toHaveBeenCalledWith("https://newsite.com");
    });
  });

  it("deve desabilitar botão quando URL está vazia", () => {
    render(
      <BrowserSessionManager
        sessions={[]}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    const submitButton = screen.getByText(/Criar Sessão/i);
    expect(submitButton).toBeDisabled();
  });

  it("deve exibir último navigation quando presente", () => {
    render(
      <BrowserSessionManager
        sessions={mockSessions}
        isLoading={false}
        onCreateSession={mockOnCreateSession}
        onCloseSession={mockOnCloseSession}
      />,
    );

    expect(screen.getByText(/Última navegação:/i)).toBeInTheDocument();
    expect(
      screen.getByText(/https:\/\/example.com\/page1/i),
    ).toBeInTheDocument();
  });
});
