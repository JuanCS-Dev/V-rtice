// frontend/src/components/ThemeSelector/__tests__/ThemeSelector.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ThemeSelector from '../ThemeSelector';
import { ThemeProvider } from '../../../contexts/ThemeContext';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = value.toString(); },
    clear: () => { store = {}; },
    removeItem: (key) => { delete store[key]; }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('ThemeSelector', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  const renderWithThemeProvider = (component) => {
    return render(
      <ThemeProvider>
        {component}
      </ThemeProvider>
    );
  };

  it('deve renderizar o botão de tema', () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    expect(trigger).toBeInTheDocument();
  });

  it('deve exibir o tema atual', () => {
    renderWithThemeProvider(<ThemeSelector />);
    expect(screen.getByText('Matrix Green')).toBeInTheDocument();
  });

  it('deve abrir dropdown ao clicar', () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    fireEvent.click(trigger);
    
    expect(screen.getByText('Temas Disponíveis')).toBeInTheDocument();
  });

  it('deve mostrar todos os temas disponíveis', () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    fireEvent.click(trigger);
    
    // Verificar alguns temas
    expect(screen.getByText('Cyber Blue')).toBeInTheDocument();
    expect(screen.getByText('Purple Haze')).toBeInTheDocument();
    expect(screen.getByText('Windows 11')).toBeInTheDocument();
  });

  it('deve trocar tema ao clicar em opção', async () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    // Abrir dropdown
    fireEvent.click(trigger);
    
    // Clicar em Cyber Blue
    const cyberBlueOption = screen.getByText('Cyber Blue');
    fireEvent.click(cyberBlueOption);
    
    // Dropdown deve fechar
    await waitFor(() => {
      expect(screen.queryByText('Temas Disponíveis')).not.toBeInTheDocument();
    });
    
    // Verificar se tema foi salvo
    expect(localStorage.getItem('vertice-theme')).toBe('cyber-blue');
  });

  it('deve fechar dropdown ao clicar no backdrop', async () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    // Abrir dropdown
    fireEvent.click(trigger);
    expect(screen.getByText('Temas Disponíveis')).toBeInTheDocument();
    
    // Clicar no backdrop
    const backdrop = document.querySelector('.theme-selector__backdrop');
    fireEvent.click(backdrop);
    
    // Dropdown deve fechar
    await waitFor(() => {
      expect(screen.queryByText('Temas Disponíveis')).not.toBeInTheDocument();
    });
  });

  it('deve aplicar atributo data-theme no document', () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    // Abrir dropdown
    fireEvent.click(trigger);
    
    // Trocar para Purple Haze
    const purpleOption = screen.getByText('Purple Haze');
    fireEvent.click(purpleOption);
    
    // Verificar atributo no document
    expect(document.documentElement.getAttribute('data-theme')).toBe('purple-haze');
  });

  it('deve mostrar checkmark no tema ativo', () => {
    renderWithThemeProvider(<ThemeSelector />);
    const trigger = screen.getByLabelText('Selecionar tema');
    
    fireEvent.click(trigger);
    
    // O tema default (Matrix Green) deve ter classe active
    const activeOption = screen.getByText('Matrix Green').closest('button');
    expect(activeOption).toHaveClass('theme-selector__option--active');
  });

  it('deve posicionar corretamente baseado na prop', () => {
    const { container } = renderWithThemeProvider(<ThemeSelector position="bottom-left" />);
    const selector = container.querySelector('.theme-selector');
    expect(selector).toHaveClass('theme-selector--bottom-left');
  });
});
