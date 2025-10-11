import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { RestrictedAccessMessage } from './RestrictedAccessMessage';

describe('RestrictedAccessMessage', () => {
  it('renders correctly with default state', () => {
    render(<RestrictedAccessMessage onRequestAccess={() => {}} isRequestingAccess={false} />);
    expect(screen.getByText('MÓDULO RESTRITO')).toBeInTheDocument();
    expect(screen.getByText('SOLICITAR ACESSO')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /solicitar acesso/i })).toBeEnabled();
    expect(screen.getByRole('img', { name: /warning/i })).toBeInTheDocument();
  });

  it('shows loading state when isRequestingAccess is true', () => {
    render(<RestrictedAccessMessage onRequestAccess={() => {}} isRequestingAccess={true} />);
    expect(screen.getByText('SOLICITANDO...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /solicitando.../i })).toBeDisabled();
  });

  it('calls onRequestAccess when button is clicked', () => {
    const mockRequestAccess = vi.fn();
    render(<RestrictedAccessMessage onRequestAccess={mockRequestAccess} isRequestingAccess={false} />);

    fireEvent.click(screen.getByRole('button', { name: /solicitar acesso/i }));
    expect(mockRequestAccess).toHaveBeenCalledTimes(1);
  });
});
