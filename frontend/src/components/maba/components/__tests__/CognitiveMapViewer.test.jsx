/**
 * CognitiveMapViewer Component Tests
 *
 * Testa o componente de visualização de grafo D3.js (força-direcionado).
 *
 * @author Vértice Platform Team
 * @license Proprietary
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CognitiveMapViewer from '../CognitiveMapViewer';

// Mock D3.js
vi.mock('d3', () => ({
  select: vi.fn(() => ({
    selectAll: vi.fn(() => ({
      remove: vi.fn(),
    })),
    append: vi.fn(() => ({
      selectAll: vi.fn(() => ({
        data: vi.fn(() => ({
          enter: vi.fn(() => ({
            append: vi.fn(() => ({
              attr: vi.fn(() => ({ attr: vi.fn(() => ({ attr: vi.fn() })) })),
              style: vi.fn(() => ({ style: vi.fn() })),
              call: vi.fn(),
              on: vi.fn(),
            })),
          })),
        })),
      })),
    })),
    call: vi.fn(),
  })),
  zoom: vi.fn(() => ({
    scaleExtent: vi.fn(() => ({
      on: vi.fn(),
    })),
  })),
  forceSimulation: vi.fn(() => ({
    force: vi.fn(() => ({ force: vi.fn(() => ({ force: vi.fn(() => ({ force: vi.fn() })) }) })),
    on: vi.fn(),
    stop: vi.fn(),
  })),
  forceLink: vi.fn(() => ({
    id: vi.fn(() => ({
      distance: vi.fn(),
    })),
  })),
  forceManyBody: vi.fn(() => ({
    strength: vi.fn(),
  })),
  forceCenter: vi.fn(() => ({})),
  forceCollide: vi.fn(() => ({
    radius: vi.fn(),
  })),
  scaleOrdinal: vi.fn(() => ({
    domain: vi.fn(() => ({
      range: vi.fn(),
    })),
  })),
  schemeCategory10: [],
  drag: vi.fn(() => ({
    on: vi.fn(() => ({
      on: vi.fn(() => ({
        on: vi.fn(),
      })),
    })),
  })),
}));

describe('CognitiveMapViewer', () => {
  const mockGraph = {
    nodes: [
      {
        id: 'node-1',
        url: 'https://example.com',
        domain: 'example.com',
        elements: 42,
        label: 'Example',
        visited_at: '2025-10-31T10:00:00Z',
      },
      {
        id: 'node-2',
        url: 'https://test.com',
        domain: 'test.com',
        elements: 15,
        label: 'Test',
        visited_at: '2025-10-31T11:00:00Z',
      },
    ],
    edges: [
      {
        source: 'node-1',
        target: 'node-2',
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve renderizar estado vazio quando não há nodes', () => {
    render(<CognitiveMapViewer graph={{ nodes: [], edges: [] }} isLoading={false} />);
    expect(screen.getByText(/Cognitive Map vazio/i)).toBeInTheDocument();
    expect(screen.getByText(/Nenhuma página foi mapeada ainda/i)).toBeInTheDocument();
  });

  it('deve renderizar estado vazio quando graph é null', () => {
    render(<CognitiveMapViewer graph={null} isLoading={false} />);
    expect(screen.getByText(/Cognitive Map vazio/i)).toBeInTheDocument();
  });

  it('deve renderizar SVG quando há graph', () => {
    const { container } = render(<CognitiveMapViewer graph={mockGraph} isLoading={false} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('deve renderizar instruções de uso', () => {
    render(<CognitiveMapViewer graph={mockGraph} isLoading={false} />);
    expect(screen.getByText(/Arraste para mover/i)).toBeInTheDocument();
    expect(screen.getByText(/Scroll para zoom/i)).toBeInTheDocument();
  });

  it('deve renderizar legenda', () => {
    render(<CognitiveMapViewer graph={mockGraph} isLoading={false} />);
    expect(screen.getByText(/Legenda/i)).toBeInTheDocument();
    expect(screen.getByText(/Poucas interações/i)).toBeInTheDocument();
    expect(screen.getByText(/Muitas interações/i)).toBeInTheDocument();
  });

  it('não deve mostrar painel de detalhes inicialmente', () => {
    render(<CognitiveMapViewer graph={mockGraph} isLoading={false} />);
    expect(screen.queryByText(/Detalhes da Página/i)).not.toBeInTheDocument();
  });

  it('deve renderizar ícone de cérebro no estado vazio', () => {
    render(<CognitiveMapViewer graph={null} isLoading={false} />);
    expect(screen.getByText(/🧠/)).toBeInTheDocument();
  });
});
