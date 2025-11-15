/**
 * StatsOverview Component Tests (MABA)
 *
 * Testa o componente de visão geral de estatísticas do MABA.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatsOverview from "../StatsOverview";

describe("StatsOverview (MABA)", () => {
  const mockStats = {
    total_sessions: 15,
    active_sessions: 3,
    pages_mapped: 127,
    elements_learned: 845,
    total_screenshots: 42,
    total_navigations: 358,
  };

  it("deve renderizar todas as métricas", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("Total Sessions")).toBeInTheDocument();
    expect(screen.getByText("Active Sessions")).toBeInTheDocument();
    expect(screen.getByText("Páginas Mapeadas")).toBeInTheDocument();
    expect(screen.getByText("Elementos Aprendidos")).toBeInTheDocument();
    expect(screen.getByText("Screenshots")).toBeInTheDocument();
    expect(screen.getByText("Navegações")).toBeInTheDocument();
  });

  it("deve exibir valores formatados", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("127")).toBeInTheDocument();
    expect(screen.getByText("845")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("358")).toBeInTheDocument();
  });

  it("deve exibir ícones corretos", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("🌐")).toBeInTheDocument(); // Total Sessions
    expect(screen.getByText("🟢")).toBeInTheDocument(); // Active Sessions
    expect(screen.getByText("📄")).toBeInTheDocument(); // Páginas Mapeadas
    expect(screen.getByText("🧩")).toBeInTheDocument(); // Elementos Aprendidos
    expect(screen.getByText("📸")).toBeInTheDocument(); // Screenshots
    expect(screen.getByText("🧭")).toBeInTheDocument(); // Navegações
  });

  it("deve renderizar valores zero quando não há dados", () => {
    const emptyStats = {
      total_sessions: 0,
      active_sessions: 0,
      pages_mapped: 0,
      elements_learned: 0,
      total_screenshots: 0,
      total_navigations: 0,
    };

    render(<StatsOverview stats={emptyStats} />);

    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBe(6);
  });

  it("deve usar valores padrão quando stats é undefined", () => {
    const partialStats = {
      total_sessions: 5,
      // Outros campos ausentes
    };

    render(<StatsOverview stats={partialStats} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBe(5); // 5 campos restantes devem ser 0
  });

  it("não deve renderizar quando stats é null", () => {
    const { container } = render(<StatsOverview stats={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("deve formatar números grandes com separador de milhar", () => {
    const largeStats = {
      total_sessions: 1234,
      active_sessions: 56,
      pages_mapped: 9876,
      elements_learned: 12345,
      total_screenshots: 999,
      total_navigations: 54321,
    };

    render(<StatsOverview stats={largeStats} />);

    // toLocaleString() vai adicionar separadores (1.234, 9.876, etc)
    expect(screen.getByText(/1.234|1,234/)).toBeInTheDocument();
  });
});
