/**
 * AnomalyHeatmap Component Tests
 *
 * Testa o mapa de calor de anomalias (GitHub-style).
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AnomalyHeatmap from "../AnomalyHeatmap";

describe("AnomalyHeatmap", () => {
  const mockAnomalies = [
    {
      detected_at: "2025-10-31T10:15:00Z",
      severity: "critical",
      description: "CPU usage acima do threshold",
      metric_name: "cpu_usage",
      threshold: "90%",
    },
    {
      detected_at: "2025-10-31T09:30:00Z",
      severity: "high",
      description: "Memory leak detectado",
      metric_name: "memory_usage",
      threshold: "85%",
    },
    {
      detected_at: "2025-10-30T14:20:00Z",
      severity: "medium",
      description: "Response time elevado",
      metric_name: "avg_response_time",
      threshold: "500ms",
    },
    {
      detected_at: "2025-10-29T11:10:00Z",
      severity: "low",
      description: "Disk space baixo",
      metric_name: "disk_usage",
    },
  ];

  const mockTimeline = [
    { date: "2025-10-31", count: 2 },
    { date: "2025-10-30", count: 1 },
    { date: "2025-10-29", count: 1 },
  ];

  it("deve renderizar loading state", () => {
    render(<AnomalyHeatmap anomalies={[]} timeline={[]} isLoading={true} />);
    expect(screen.getByText(/Carregando anomalias/i)).toBeInTheDocument();
  });

  it("deve renderizar severity stats bar", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Critical:/i)).toBeInTheDocument();
    expect(screen.getByText(/High:/i)).toBeInTheDocument();
    expect(screen.getByText(/Medium:/i)).toBeInTheDocument();
    expect(screen.getByText(/Low:/i)).toBeInTheDocument();
  });

  it("deve exibir contadores de severidade corretos", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );

    // 1 critical, 1 high, 1 medium, 1 low
    const stats = screen.getAllByText("1");
    expect(stats.length).toBeGreaterThanOrEqual(4);
  });

  it("deve renderizar título do calendário", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Últimas 12 Semanas/i)).toBeInTheDocument();
  });

  it("deve renderizar legenda do heatmap", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Menos/i)).toBeInTheDocument();
    expect(screen.getByText(/Mais/i)).toBeInTheDocument();
  });

  it("deve renderizar labels dos dias da semana", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText("Dom")).toBeInTheDocument();
    expect(screen.getByText("Seg")).toBeInTheDocument();
    expect(screen.getByText("Ter")).toBeInTheDocument();
    expect(screen.getByText("Qua")).toBeInTheDocument();
    expect(screen.getByText("Qui")).toBeInTheDocument();
    expect(screen.getByText("Sex")).toBeInTheDocument();
    expect(screen.getByText("Sáb")).toBeInTheDocument();
  });

  it("deve renderizar título de anomalias recentes", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText(/Anomalias Recentes/i)).toBeInTheDocument();
  });

  it("deve renderizar lista de anomalias", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(
      screen.getByText(/CPU usage acima do threshold/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Memory leak detectado/i)).toBeInTheDocument();
    expect(screen.getByText(/Response time elevado/i)).toBeInTheDocument();
  });

  it("deve exibir severity labels em uppercase", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("MEDIUM")).toBeInTheDocument();
    expect(screen.getByText("LOW")).toBeInTheDocument();
  });

  it("deve exibir nome da métrica", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText("cpu_usage")).toBeInTheDocument();
    expect(screen.getByText("memory_usage")).toBeInTheDocument();
  });

  it("deve exibir threshold quando presente", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText("90%")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("deve exibir mensagem quando não há anomalias", () => {
    render(<AnomalyHeatmap anomalies={[]} timeline={[]} isLoading={false} />);
    expect(screen.getByText(/Nenhuma anomalia detectada/i)).toBeInTheDocument();
  });

  it("deve limitar lista a 10 anomalias recentes", () => {
    const manyAnomalies = Array.from({ length: 15 }, (_, i) => ({
      detected_at: `2025-10-${31 - i}T10:00:00Z`,
      severity: "low",
      description: `Anomalia ${i + 1}`,
      metric_name: `metric_${i}`,
    }));

    render(
      <AnomalyHeatmap
        anomalies={manyAnomalies}
        timeline={[]}
        isLoading={false}
      />,
    );

    // Deve mostrar apenas 10
    expect(screen.getByText(/Anomalia 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Anomalia 10/i)).toBeInTheDocument();
    expect(screen.queryByText(/Anomalia 11/i)).not.toBeInTheDocument();
  });

  it("deve exibir ícones de severidade", () => {
    render(
      <AnomalyHeatmap
        anomalies={mockAnomalies}
        timeline={mockTimeline}
        isLoading={false}
      />,
    );
    expect(screen.getByText("🔴")).toBeInTheDocument(); // Critical
    expect(screen.getByText("🟠")).toBeInTheDocument(); // High
    expect(screen.getByText("🟡")).toBeInTheDocument(); // Medium
    expect(screen.getByText("🔵")).toBeInTheDocument(); // Low
  });
});
