/**
 * FruitCard Component Tests
 *
 * Testes unitários para o componente FruitCard (9 Frutos do Espírito).
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import FruitCard from "../FruitCard";

describe("FruitCard", () => {
  const mockFruit = {
    name: "Amor (Ἀγάπη)",
    name_pt: "Amor",
    score: 0.92,
    description: "Qualidade do atendimento aos usuários",
    metric: "customer_satisfaction_score",
    status: "healthy",
  };

  it("deve renderizar o nome do fruto", () => {
    render(<FruitCard fruit={mockFruit} />);
    expect(screen.getByText(/Amor/)).toBeInTheDocument();
  });

  it("deve renderizar o score formatado", () => {
    render(<FruitCard fruit={mockFruit} />);
    expect(screen.getByText(/92%/)).toBeInTheDocument();
  });

  it("deve renderizar a descrição", () => {
    render(<FruitCard fruit={mockFruit} />);
    expect(screen.getByText(/Qualidade do atendimento/)).toBeInTheDocument();
  });

  it("deve aplicar classe healthy quando score >= 0.85", () => {
    const { container } = render(<FruitCard fruit={mockFruit} />);
    expect(container.querySelector(".healthy")).toBeInTheDocument();
  });

  it("deve aplicar classe warning quando score < 0.85", () => {
    const lowScoreFruit = { ...mockFruit, score: 0.75 };
    const { container } = render(<FruitCard fruit={lowScoreFruit} />);
    expect(container.querySelector(".warning")).toBeInTheDocument();
  });

  it("deve aplicar classe critical quando score < 0.60", () => {
    const criticalFruit = { ...mockFruit, score: 0.5 };
    const { container } = render(<FruitCard fruit={criticalFruit} />);
    expect(container.querySelector(".critical")).toBeInTheDocument();
  });
});
