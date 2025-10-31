/**
 * SystemPulseVisualization Component Tests
 *
 * Testa a visualização de pulso do sistema (medical monitor style).
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SystemPulseVisualization from "../SystemPulseVisualization";

describe("SystemPulseVisualization", () => {
  const mockPulse = {
    health: 0.85,
    status_messages: [
      {
        timestamp: "2025-10-31T10:15:00Z",
        message: "Sistema operando normalmente",
      },
      {
        timestamp: "2025-10-31T10:10:00Z",
        message: "Backup concluído com sucesso",
      },
    ],
  };

  const mockMetrics = {
    cpu_usage: 0.65,
    memory_usage: 0.72,
    avg_response_time: 250,
    throughput: 12.5,
    error_rate: 0.02,
    uptime_hours: 168,
  };

  it("deve renderizar loading state", () => {
    render(
      <SystemPulseVisualization pulse={null} metrics={null} isLoading={true} />,
    );
    expect(screen.getByText(/Carregando system pulse/i)).toBeInTheDocument();
  });

  it("deve renderizar System Health principal", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/System Health/i)).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument(); // 85%
  });

  it("deve renderizar título de sinais vitais", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Sinais Vitais/i)).toBeInTheDocument();
  });

  it("deve renderizar todas as métricas vitais", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/CPU Usage/i)).toBeInTheDocument();
    expect(screen.getByText(/Memory Usage/i)).toBeInTheDocument();
    expect(screen.getByText(/Response Time/i)).toBeInTheDocument();
    expect(screen.getByText(/Throughput/i)).toBeInTheDocument();
    expect(screen.getByText(/Error Rate/i)).toBeInTheDocument();
    expect(screen.getByText(/Uptime/i)).toBeInTheDocument();
  });

  it("deve exibir valores formatados de CPU", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/65.0%/i)).toBeInTheDocument();
  });

  it("deve exibir valores formatados de Memory", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/72.0%/i)).toBeInTheDocument();
  });

  it("deve exibir response time em ms", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/250ms/i)).toBeInTheDocument();
  });

  it("deve exibir throughput em req/s", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/12.5 req\/s/i)).toBeInTheDocument();
  });

  it("deve exibir error rate em percentual", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/2.00%/i)).toBeInTheDocument();
  });

  it("deve exibir uptime em horas", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/168h/i)).toBeInTheDocument();
  });

  it("deve renderizar ícones das métricas", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText("🖥️")).toBeInTheDocument(); // CPU
    expect(screen.getByText("💾")).toBeInTheDocument(); // Memory
    expect(screen.getByText("⚡")).toBeInTheDocument(); // Response Time
    expect(screen.getByText("📊")).toBeInTheDocument(); // Throughput
    expect(screen.getByText("⚠️")).toBeInTheDocument(); // Error Rate
    expect(screen.getByText("⏰")).toBeInTheDocument(); // Uptime
  });

  it("deve renderizar status messages quando presentes", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Status do Sistema/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Sistema operando normalmente/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Backup concluído com sucesso/i),
    ).toBeInTheDocument();
  });

  it("não deve renderizar status messages quando não há", () => {
    const pulseWithoutMessages = { health: 0.85 };
    render(
      <SystemPulseVisualization
        pulse={pulseWithoutMessages}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.queryByText(/Status do Sistema/i)).not.toBeInTheDocument();
  });

  it("deve exibir N/A quando métricas não estão disponíveis", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={{}}
        isLoading={false}
      />,
    );
    const naElements = screen.getAllByText(/N\/A/i);
    expect(naElements.length).toBeGreaterThan(0);
  });

  it("deve usar valor padrão de 85% quando pulse.health não está presente", () => {
    render(
      <SystemPulseVisualization
        pulse={{}}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    expect(screen.getByText("85")).toBeInTheDocument(); // Default 0.85
  });

  it("deve exibir valor de porcentagem com símbolo %", () => {
    render(
      <SystemPulseVisualization
        pulse={mockPulse}
        metrics={mockMetrics}
        isLoading={false}
      />,
    );
    const percentSymbols = screen.getAllByText("%");
    expect(percentSymbols.length).toBeGreaterThan(0);
  });
});
