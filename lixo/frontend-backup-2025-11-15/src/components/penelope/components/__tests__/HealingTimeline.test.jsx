/**
 * HealingTimeline Component Tests
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import HealingTimeline from "../HealingTimeline";

describe("HealingTimeline", () => {
  const mockEvents = [
    {
      event_id: "heal-001",
      timestamp: "2025-10-31T08:15:23Z",
      anomaly_type: "latency_spike",
      affected_service: "api-gateway",
      severity: "P1",
      action_taken: "intervene",
      outcome: "success",
    },
    {
      event_id: "heal-002",
      timestamp: "2025-10-31T07:42:11Z",
      anomaly_type: "memory_leak",
      affected_service: "worker-service",
      severity: "P2",
      action_taken: "observe",
      outcome: "self_healed",
    },
  ];

  it("deve renderizar o título", () => {
    render(<HealingTimeline events={mockEvents} isLoading={false} />);
    expect(screen.getByText(/Healing Timeline/)).toBeInTheDocument();
  });

  it("deve renderizar eventos quando fornecidos", () => {
    render(<HealingTimeline events={mockEvents} isLoading={false} />);
    expect(screen.getByText(/latency_spike/)).toBeInTheDocument();
    expect(screen.getByText(/memory_leak/)).toBeInTheDocument();
  });

  it("deve exibir loading state", () => {
    render(<HealingTimeline events={[]} isLoading={true} />);
    expect(screen.getByText(/Carregando/i)).toBeInTheDocument();
  });

  it("deve exibir mensagem quando não há eventos", () => {
    render(<HealingTimeline events={[]} isLoading={false} />);
    expect(screen.getByText(/Nenhum evento/i)).toBeInTheDocument();
  });

  it("deve renderizar severity badges", () => {
    render(<HealingTimeline events={mockEvents} isLoading={false} />);
    expect(screen.getByText(/P1/)).toBeInTheDocument();
    expect(screen.getByText(/P2/)).toBeInTheDocument();
  });
});
