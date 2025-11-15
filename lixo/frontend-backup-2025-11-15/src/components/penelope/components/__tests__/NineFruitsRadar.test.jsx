/**
 * NineFruitsRadar Component Tests
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import NineFruitsRadar from "../NineFruitsRadar";

// Mock Recharts
vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  RadarChart: ({ children }) => <div data-testid="radar-chart">{children}</div>,
  PolarGrid: () => <div data-testid="polar-grid" />,
  PolarAngleAxis: () => <div data-testid="polar-angle-axis" />,
  PolarRadiusAxis: () => <div data-testid="polar-radius-axis" />,
  Radar: () => <div data-testid="radar" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

describe("NineFruitsRadar", () => {
  const mockFruits = {
    amor: { score: 0.92 },
    alegria: { score: 0.88 },
    paz: { score: 0.95 },
    paciencia: { score: 0.87 },
    bondade: { score: 0.94 },
    fidelidade: { score: 0.91 },
    mansidao: { score: 0.89 },
    dominio_proprio: { score: 0.93 },
    gentileza: { score: 0.9 },
  };

  it("deve renderizar o título", () => {
    render(<NineFruitsRadar fruits={mockFruits} />);
    expect(screen.getByText(/9 Frutos do Espírito/)).toBeInTheDocument();
  });

  it("deve renderizar o RadarChart", () => {
    render(<NineFruitsRadar fruits={mockFruits} />);
    expect(screen.getByTestId("radar-chart")).toBeInTheDocument();
  });

  it("deve renderizar referência bíblica", () => {
    render(<NineFruitsRadar fruits={mockFruits} />);
    expect(screen.getByText(/Gálatas 5:22-23/)).toBeInTheDocument();
  });

  it("deve calcular overall score", () => {
    render(<NineFruitsRadar fruits={mockFruits} />);
    expect(screen.getByText(/Overall:/)).toBeInTheDocument();
  });
});
