/**
 * StatsOverview Component Tests (MVP)
 *
 * Testa o componente de visão geral de estatísticas do MVP.
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import StatsOverview from "../StatsOverview";

describe("StatsOverview (MVP)", () => {
  const mockStats = {
    total: 42,
    analytical: 15,
    poetic: 12,
    technical: 10,
    avg_nqs: 0.88,
    last_24h: 8,
  };

  it("deve renderizar todas as métricas", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("Total Narrativas")).toBeInTheDocument();
    expect(screen.getByText("Analytical")).toBeInTheDocument();
    expect(screen.getByText("Poetic")).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
    expect(screen.getByText("NQS Médio")).toBeInTheDocument();
    expect(screen.getByText("Última 24h")).toBeInTheDocument();
  });

  it("deve exibir valores formatados", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("42")).toBeInTheDocument(); // total
    expect(screen.getByText("15")).toBeInTheDocument(); // analytical
    expect(screen.getByText("12")).toBeInTheDocument(); // poetic
    expect(screen.getByText("10")).toBeInTheDocument(); // technical
    expect(screen.getByText("88%")).toBeInTheDocument(); // avg_nqs
    expect(screen.getByText("8")).toBeInTheDocument(); // last_24h
  });

  it("deve exibir ícones corretos", () => {
    render(<StatsOverview stats={mockStats} />);

    expect(screen.getByText("📚")).toBeInTheDocument(); // Total
    expect(screen.getByText("🔬")).toBeInTheDocument(); // Analytical
    expect(screen.getByText("🎭")).toBeInTheDocument(); // Poetic
    expect(screen.getByText("⚙️")).toBeInTheDocument(); // Technical
    expect(screen.getByText("⭐")).toBeInTheDocument(); // NQS
    expect(screen.getByText("🕐")).toBeInTheDocument(); // Última 24h
  });

  it("deve renderizar valores zero quando não há dados", () => {
    const emptyStats = {
      total: 0,
      analytical: 0,
      poetic: 0,
      technical: 0,
      last_24h: 0,
    };

    render(<StatsOverview stats={emptyStats} />);

    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBeGreaterThanOrEqual(5);
  });

  it("deve exibir N/A quando avg_nqs não está presente", () => {
    const statsWithoutNqs = {
      total: 10,
      analytical: 5,
      poetic: 3,
      technical: 2,
      last_24h: 1,
    };

    render(<StatsOverview stats={statsWithoutNqs} />);
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("deve usar valores padrão quando stats parcial", () => {
    const partialStats = {
      total: 20,
      // Outros campos ausentes
    };

    render(<StatsOverview stats={partialStats} />);

    expect(screen.getByText("20")).toBeInTheDocument();
    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBeGreaterThanOrEqual(4); // Campos restantes
  });

  it("não deve renderizar quando stats é null", () => {
    const { container } = render(<StatsOverview stats={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("deve formatar NQS com percentual", () => {
    render(<StatsOverview stats={mockStats} />);
    expect(screen.getByText(/88%/)).toBeInTheDocument();
  });

  it("deve arredondar NQS para inteiro", () => {
    const statsWithDecimalNqs = {
      ...mockStats,
      avg_nqs: 0.8765,
    };

    render(<StatsOverview stats={statsWithDecimalNqs} />);
    expect(screen.getByText("88%")).toBeInTheDocument(); // Arredondado
  });

  it("deve aplicar classes de cor corretas", () => {
    const { container } = render(<StatsOverview stats={mockStats} />);

    const metrics = container.querySelectorAll('[class*="metric"]');
    expect(metrics.length).toBe(6);

    // Verifica se há classes de cor
    const hasColorClasses = Array.from(metrics).some(
      (m) =>
        m.className.includes("purple") ||
        m.className.includes("blue") ||
        m.className.includes("pink"),
    );
    expect(hasColorClasses).toBe(true);
  });
});
