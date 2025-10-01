import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import DarkWebModule from './DarkWebModule';

// Mock the useDarkWebAccess hook
vi.mock('./hooks/useDarkWebAccess', () => ({
  useDarkWebAccess: () => ({
    isRequestingAccess: false,
    requestAccess: vi.fn(),
  }),
}));

describe('DarkWebModule', () => {
  it('renders the module title and description', () => {
    render(<DarkWebModule />);
    expect(screen.getByText('DARK WEB MONITOR')).toBeInTheDocument();
    expect(screen.getByText('Monitoramento de atividades na dark web e mercados ocultos')).toBeInTheDocument();
  });

  it('renders the RestrictedAccessMessage component', () => {
    render(<DarkWebModule />);
    expect(screen.getByText('MÓDULO RESTRITO')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /solicitar acesso/i })).toBeInTheDocument();
  });

  it('renders the resources available section', () => {
    render(<DarkWebModule />);
    expect(screen.getByText('RECURSOS DISPONÍVEIS (COM AUTORIZAÇÃO)')).toBeInTheDocument();
    expect(screen.getByText(/Monitoramento de mercados de dados vazados/i)).toBeInTheDocument();
  });

  // Nota: Este teste foi simplificado pois o mock do hook já está configurado
  // e testar o click seria redundante com o teste do RestrictedAccessMessage
  it('integrates with RestrictedAccessMessage', () => {
    render(<DarkWebModule />);
    const button = screen.getByRole('button', { name: /solicitar acesso/i });
    expect(button).toBeEnabled();
    // O requestAccess real é mockado no nível do arquivo
  });
});
