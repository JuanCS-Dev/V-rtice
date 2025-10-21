# 🧪 GUIA COMPLETO DE TESTES - FRONTEND VÉRTICE

**Autor:** Claude Code (Senior Testing Engineer)
**Data:** 2025-10-01
**Versão:** 1.0
**Público:** Desenvolvedores (especialmente estagiários)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Por Que Testar?](#por-que-testar)
3. [Tipos de Testes](#tipos-de-testes)
4. [Setup do Ambiente](#setup-do-ambiente)
5. [Anatomia de um Teste](#anatomia-de-um-teste)
6. [Testando Componentes React](#testando-componentes-react)
7. [Testando Hooks Customizados](#testando-hooks-customizados)
8. [Mocking e Spies](#mocking-e-spies)
9. [Padrões e Best Practices](#padrões-e-best-practices)
10. [Troubleshooting Comum](#troubleshooting-comum)
11. [Exemplos Práticos Completos](#exemplos-práticos-completos)
12. [Checklist de Qualidade](#checklist-de-qualidade)

---

## 🎯 Visão Geral

### O Que São Testes?

Testes automatizados são **código que valida se outro código funciona corretamente**. Eles garantem que:

- ✅ Funcionalidades existentes continuam funcionando (sem regressões)
- ✅ Novas features funcionam como esperado
- ✅ Edge cases são tratados
- ✅ Código é refatorável com segurança

### Stack de Testes no Vértice

```yaml
Test Runner: Vitest (compatível com Jest, mais rápido)
Testing Library: React Testing Library
Asserções: Vitest (expect)
Mocking: Vitest (vi.fn, vi.mock)
Coverage: Vitest --coverage
```

### Estrutura de Arquivos

```
Component/
├── Component.jsx
├── Component.module.css
├── components/
│   ├── SubComponent.jsx
│   └── SubComponent.module.css
├── hooks/
│   └── useComponent.js
└── __tests__/
    ├── Component.test.jsx           # Testes do componente principal
    ├── SubComponent.test.jsx        # Testes de subcomponentes
    └── useComponent.test.js         # Testes do hook
```

---

## 💡 Por Que Testar?

### Benefícios Concretos

#### 1. **Confiança na Refatoração**
```javascript
// Sem testes: "Será que eu quebrei algo?"
// Com testes: "Todos os testes passaram, está seguro!"
```

#### 2. **Documentação Viva**
```javascript
it('deve desabilitar o botão quando loading é true', () => {
  // Este teste DOCUMENTA o comportamento esperado
});
```

#### 3. **Menos Bugs em Produção**
```javascript
// Teste captura bug ANTES de ir para produção
it('deve validar formato CVE-YYYY-NNNN', () => {
  expect(validateCVE('CVE-2024-1234')).toBe(true);
  expect(validateCVE('invalid')).toBe(false); // ❌ Captura input inválido
});
```

#### 4. **Desenvolvimento Mais Rápido**
```javascript
// Sem testes: Testar manualmente no browser 20x
// Com testes: npm test (2 segundos, 100% automático)
```

### ROI de Testes

| Investimento | Retorno |
|--------------|---------|
| 30% tempo a mais escrevendo | 70% menos bugs em produção |
| 1 hora escrevendo testes | 10 horas economizadas em debugging |
| 100 linhas de testes | 1000 linhas de código protegidas |

---

## 🎭 Tipos de Testes

### 1. Testes Unitários (Unit Tests)

**O que testam:** Funções e hooks isolados

**Exemplo:**
```javascript
// utils/validators.js
export const validateCVE = (cveId) => {
  return /^CVE-\d{4}-\d{4,}$/i.test(cveId);
};

// __tests__/validators.test.js
import { validateCVE } from '../utils/validators';

describe('validateCVE', () => {
  it('deve aceitar CVE válido', () => {
    expect(validateCVE('CVE-2024-1234')).toBe(true);
  });

  it('deve rejeitar CVE inválido', () => {
    expect(validateCVE('CVE-202-123')).toBe(false);
    expect(validateCVE('invalid')).toBe(false);
    expect(validateCVE('')).toBe(false);
  });
});
```

**Quando usar:** Funções puras, utilitários, validações

---

### 2. Testes de Componentes (Component Tests)

**O que testam:** Renderização e interação de componentes React

**Exemplo:**
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('deve renderizar texto corretamente', () => {
    render(<Button>Clique aqui</Button>);
    expect(screen.getByText('Clique aqui')).toBeInTheDocument();
  });

  it('deve chamar onClick quando clicado', () => {
    const handleClick = vi.fn(); // Mock function
    render(<Button onClick={handleClick}>Clique</Button>);

    fireEvent.click(screen.getByText('Clique'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('deve estar desabilitado quando disabled=true', () => {
    render(<Button disabled>Clique</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

**Quando usar:** Todos os componentes React

---

### 3. Testes de Hooks (Hook Tests)

**O que testam:** Lógica de negócio em hooks customizados

**Exemplo:**
```javascript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi } from './useApi';

describe('useApi', () => {
  it('deve iniciar com estado vazio', () => {
    const mockFn = vi.fn();
    const { result } = renderHook(() => useApi(mockFn));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('deve executar e retornar dados', async () => {
    const mockFn = vi.fn().mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApi(mockFn));

    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.data).toEqual({ data: 'test' });
    expect(result.current.loading).toBe(false);
  });
});
```

**Quando usar:** Todos os hooks customizados

---

### 4. Testes de Integração (Integration Tests)

**O que testam:** Interação entre múltiplos componentes

**Exemplo:**
```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExploitSearchWidget } from './ExploitSearchWidget';
import { searchExploits } from '../../../api/worldClassTools';

vi.mock('../../../api/worldClassTools');

describe('ExploitSearchWidget - Integração', () => {
  it('deve buscar e exibir resultados completos', async () => {
    // Mock da API
    searchExploits.mockResolvedValue({
      result: {
        cve_id: 'CVE-2024-1234',
        exploits: [{ title: 'Exploit 1' }],
        recommendations: ['Update system']
      }
    });

    // Renderizar componente
    render(<ExploitSearchWidget />);

    // Usuário digita CVE
    const input = screen.getByPlaceholderText(/CVE-/i);
    fireEvent.change(input, { target: { value: 'CVE-2024-1234' } });

    // Usuário clica em buscar
    fireEvent.click(screen.getByText(/BUSCAR/i));

    // Aguarda resultado aparecer
    await waitFor(() => {
      expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument();
      expect(screen.getByText('Exploit 1')).toBeInTheDocument();
      expect(screen.getByText('Update system')).toBeInTheDocument();
    });
  });
});
```

**Quando usar:** Fluxos completos de funcionalidades

---

## ⚙️ Setup do Ambiente

### 1. Instalar Dependências

```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event happy-dom
```

### 2. Configurar Vitest

**Arquivo: `vitest.config.js`**
```javascript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './src/test/setup.js',
    css: true, // Habilita CSS Modules nos testes
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 3. Setup de Testes

**Arquivo: `src/test/setup.js`**
```javascript
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest matchers
expect.extend(matchers);

// Cleanup após cada teste
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock global do fetch
global.fetch = vi.fn();

// Mock do window.matchMedia (necessário para testes de componentes responsivos)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
```

### 4. Scripts no package.json

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:run": "vitest run"
  }
}
```

### 5. Rodar Testes

```bash
# Watch mode (reexecuta ao salvar)
npm test

# Rodar uma vez
npm run test:run

# Com UI interativa
npm run test:ui

# Com coverage
npm run test:coverage
```

---

## 🔬 Anatomia de um Teste

### Estrutura AAA (Arrange, Act, Assert)

```javascript
describe('Button', () => {
  it('deve chamar onClick quando clicado', () => {
    // 🔧 ARRANGE (Preparar)
    // Configurar o ambiente, criar mocks, renderizar componentes
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Clique</Button>);

    // ⚡ ACT (Agir)
    // Executar a ação que queremos testar
    fireEvent.click(screen.getByText('Clique'));

    // ✅ ASSERT (Verificar)
    // Verificar se o resultado é o esperado
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Blocos de Organização

```javascript
// describe: Agrupa testes relacionados
describe('Button', () => {

  // it (ou test): Define um caso de teste específico
  it('deve renderizar corretamente', () => {
    // ...
  });

  it('deve estar desabilitado quando loading', () => {
    // ...
  });

  // describe aninhado: Sub-grupos
  describe('quando disabled=true', () => {
    it('deve adicionar atributo disabled', () => {
      // ...
    });

    it('não deve chamar onClick', () => {
      // ...
    });
  });
});
```

### beforeEach e afterEach

```javascript
describe('Counter', () => {
  let container;

  // Executado ANTES de cada teste
  beforeEach(() => {
    container = render(<Counter initialValue={0} />);
  });

  // Executado APÓS cada teste
  afterEach(() => {
    cleanup();
  });

  it('deve iniciar com 0', () => {
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('deve incrementar ao clicar', () => {
    fireEvent.click(screen.getByText('Increment'));
    expect(screen.getByText('1')).toBeInTheDocument();
  });
});
```

---

## ⚛️ Testando Componentes React

### Renderizando Componentes

```javascript
import { render, screen } from '@testing-library/react';
import { Button } from './Button';

it('deve renderizar children', () => {
  render(<Button>Texto do Botão</Button>);

  // ✅ BOM: Buscar por texto visível ao usuário
  expect(screen.getByText('Texto do Botão')).toBeInTheDocument();
});
```

### Queries (Como Encontrar Elementos)

#### 1. **getBy*** - Elemento DEVE existir

```javascript
// Buscar por texto
screen.getByText('Texto exato');
screen.getByText(/regex/i); // Case insensitive

// Buscar por role (PREFERIDO - acessibilidade)
screen.getByRole('button');
screen.getByRole('button', { name: /salvar/i });

// Buscar por label (para inputs)
screen.getByLabelText('Email');

// Buscar por placeholder
screen.getByPlaceholderText('Digite seu email');

// Buscar por test-id (último recurso)
screen.getByTestId('custom-element');
```

**❌ Lança erro se não encontrar**

#### 2. **queryBy*** - Elemento PODE NÃO existir

```javascript
const element = screen.queryByText('Pode não existir');

if (element) {
  // Elemento existe
} else {
  // Elemento não existe (não lança erro)
}

// Útil para testar ausência
expect(screen.queryByText('Não deve existir')).not.toBeInTheDocument();
```

#### 3. **findBy*** - Elemento aparecerá EVENTUALMENTE (async)

```javascript
// Aguarda até elemento aparecer (máx 1000ms)
const element = await screen.findByText('Carregado!');

// Útil para dados assíncronos
it('deve carregar dados da API', async () => {
  render(<DataComponent />);

  // Aguarda dados aparecerem
  expect(await screen.findByText('Dados carregados')).toBeInTheDocument();
});
```

### Hierarquia de Preferência de Queries

```javascript
// 🥇 MELHOR: Queries acessíveis (como usuário vê/interage)
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText('Email');
screen.getByPlaceholderText('Digite...');
screen.getByText('Texto visível');

// 🥈 BOM: Semantic queries
screen.getByAltText('Logo');
screen.getByTitle('Tooltip');

// 🥉 ÚLTIMO RECURSO: Test IDs
screen.getByTestId('custom-element');
```

### Interagindo com Elementos

```javascript
import { fireEvent, waitFor } from '@testing-library/react';

describe('SearchForm', () => {
  it('deve submeter formulário', async () => {
    const handleSubmit = vi.fn();
    render(<SearchForm onSubmit={handleSubmit} />);

    // Preencher input
    const input = screen.getByPlaceholderText('CVE-2024-1234');
    fireEvent.change(input, { target: { value: 'CVE-2024-9999' } });

    // Clicar botão
    fireEvent.click(screen.getByRole('button', { name: /buscar/i }));

    // Aguardar callback ser chamado
    await waitFor(() => {
      expect(handleSubmit).toHaveBeenCalledWith('CVE-2024-9999');
    });
  });
});
```

### User Event (Mais Realista)

```javascript
import userEvent from '@testing-library/user-event';

it('deve digitar no input', async () => {
  const user = userEvent.setup();
  render(<Input />);

  const input = screen.getByRole('textbox');

  // Simula digitação real (letra por letra)
  await user.type(input, 'Hello World');

  expect(input).toHaveValue('Hello World');
});
```

### Testando Estado e Props

```javascript
describe('Counter', () => {
  it('deve aceitar valor inicial via props', () => {
    render(<Counter initialValue={10} />);
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('deve incrementar estado ao clicar', () => {
    render(<Counter initialValue={0} />);

    const button = screen.getByRole('button', { name: /incrementar/i });
    fireEvent.click(button);

    expect(screen.getByText('1')).toBeInTheDocument();
  });
});
```

### Testando Renderização Condicional

```javascript
describe('LoadingButton', () => {
  it('deve mostrar spinner quando loading=true', () => {
    render(<LoadingButton loading={true}>Save</LoadingButton>);

    expect(screen.getByRole('button')).toContainHTML('spinner');
    expect(screen.queryByText('Save')).not.toBeInTheDocument();
  });

  it('deve mostrar texto quando loading=false', () => {
    render(<LoadingButton loading={false}>Save</LoadingButton>);

    expect(screen.getByText('Save')).toBeInTheDocument();
    expect(screen.queryByRole('spinner')).not.toBeInTheDocument();
  });
});
```

---

## 🪝 Testando Hooks Customizados

### Setup Básico

```javascript
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('deve iniciar com valor 0', () => {
    const { result } = renderHook(() => useCounter());

    expect(result.current.count).toBe(0);
  });

  it('deve incrementar', () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});
```

### Testando Hooks com Parâmetros

```javascript
it('deve aceitar valor inicial', () => {
  const { result } = renderHook(() => useCounter(10));

  expect(result.current.count).toBe(10);
});
```

### Testando Hooks Assíncronos

```javascript
describe('useApi', () => {
  it('deve fazer fetch e retornar dados', async () => {
    const mockFetch = vi.fn().mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApi(mockFetch));

    // Executar ação assíncrona
    await act(async () => {
      await result.current.execute();
    });

    // Aguardar estado atualizar
    await waitFor(() => {
      expect(result.current.data).toEqual({ data: 'test' });
      expect(result.current.loading).toBe(false);
    });
  });
});
```

### Testando useEffect

```javascript
describe('useDocumentTitle', () => {
  it('deve atualizar document.title', () => {
    renderHook(() => useDocumentTitle('Nova Página'));

    expect(document.title).toBe('Nova Página');
  });

  it('deve restaurar título original ao desmontar', () => {
    const originalTitle = document.title;
    const { unmount } = renderHook(() => useDocumentTitle('Temporário'));

    expect(document.title).toBe('Temporário');

    unmount();

    expect(document.title).toBe(originalTitle);
  });
});
```

---

## 🎭 Mocking e Spies

### Mock Functions (vi.fn)

```javascript
describe('Button com onClick', () => {
  it('deve chamar onClick com argumentos corretos', () => {
    // Criar mock function
    const handleClick = vi.fn();

    render(<Button onClick={handleClick} data="test">Click</Button>);

    fireEvent.click(screen.getByText('Click'));

    // Verificar que foi chamado
    expect(handleClick).toHaveBeenCalled();
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Verificar argumentos
    expect(handleClick).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'click' })
    );
  });
});
```

### Mock Modules (vi.mock)

```javascript
// Mock de módulo inteiro
vi.mock('../../../api/worldClassTools', () => ({
  searchExploits: vi.fn(),
  getConfidenceBadge: vi.fn(),
}));

import { searchExploits } from '../../../api/worldClassTools';

describe('ExploitSearchWidget', () => {
  it('deve chamar API ao buscar', async () => {
    // Configurar comportamento do mock
    searchExploits.mockResolvedValue({
      result: { cve_id: 'CVE-2024-1234' }
    });

    render(<ExploitSearchWidget />);

    fireEvent.click(screen.getByText(/buscar/i));

    await waitFor(() => {
      expect(searchExploits).toHaveBeenCalledWith('CVE-2024-1234', expect.anything());
    });
  });
});
```

### Mock de Valores de Retorno

```javascript
describe('useApi', () => {
  it('deve tratar erro', async () => {
    const mockFn = vi.fn().mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useApi(mockFn));

    await act(async () => {
      await result.current.execute();
    });

    expect(result.current.error).toBe('API Error');
    expect(result.current.data).toBeNull();
  });
});
```

### Spy em Métodos

```javascript
describe('Logger', () => {
  it('deve logar erro no console', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<ComponentWithError />);

    expect(consoleSpy).toHaveBeenCalledWith('Erro:', expect.any(Error));

    // Limpar spy
    consoleSpy.mockRestore();
  });
});
```

### Mock de Context

```javascript
import { AuthContext } from '../../contexts/AuthContext';

const mockUser = {
  email: 'test@example.com',
  permissions: ['offensive'],
};

const renderWithAuth = (component, user = mockUser) => {
  return render(
    <AuthContext.Provider value={{ user }}>
      {component}
    </AuthContext.Provider>
  );
};

describe('ProtectedComponent', () => {
  it('deve renderizar com permissão', () => {
    renderWithAuth(<ProtectedComponent />);
    expect(screen.getByText('Conteúdo Protegido')).toBeInTheDocument();
  });

  it('não deve renderizar sem permissão', () => {
    renderWithAuth(<ProtectedComponent />, { email: 'test@test.com', permissions: [] });
    expect(screen.queryByText('Conteúdo Protegido')).not.toBeInTheDocument();
  });
});
```

---

## 📚 Padrões e Best Practices

### 1. Um Conceito por Teste

```javascript
// ❌ RUIM: Testa múltiplas coisas
it('deve funcionar corretamente', () => {
  render(<Button>Click</Button>);
  expect(screen.getByText('Click')).toBeInTheDocument();
  expect(screen.getByRole('button')).not.toBeDisabled();
  fireEvent.click(screen.getByText('Click'));
  // ...
});

// ✅ BOM: Um conceito por teste
it('deve renderizar children', () => {
  render(<Button>Click</Button>);
  expect(screen.getByText('Click')).toBeInTheDocument();
});

it('deve estar habilitado por padrão', () => {
  render(<Button>Click</Button>);
  expect(screen.getByRole('button')).not.toBeDisabled();
});

it('deve chamar onClick ao clicar', () => {
  const handleClick = vi.fn();
  render(<Button onClick={handleClick}>Click</Button>);
  fireEvent.click(screen.getByText('Click'));
  expect(handleClick).toHaveBeenCalled();
});
```

### 2. Nomes Descritivos

```javascript
// ❌ RUIM
it('test 1', () => {});
it('works', () => {});
it('button', () => {});

// ✅ BOM
it('deve renderizar texto do botão', () => {});
it('deve estar desabilitado quando loading=true', () => {});
it('deve chamar onSubmit com valores do formulário', () => {});
```

### 3. Evitar Detalhes de Implementação

```javascript
// ❌ RUIM: Testa implementação (setState)
it('deve chamar setState', () => {
  const setStateSpy = vi.spyOn(React, 'useState');
  render(<Counter />);
  // ...
});

// ✅ BOM: Testa comportamento (usuário vê valor mudar)
it('deve incrementar contador ao clicar', () => {
  render(<Counter />);
  expect(screen.getByText('0')).toBeInTheDocument();

  fireEvent.click(screen.getByText('Increment'));

  expect(screen.getByText('1')).toBeInTheDocument();
});
```

### 4. Usar waitFor Para Assíncronos

```javascript
// ❌ RUIM: Não aguarda
it('deve carregar dados', () => {
  render(<AsyncComponent />);
  expect(screen.getByText('Dados carregados')).toBeInTheDocument(); // ❌ Falha
});

// ✅ BOM: Aguarda com waitFor
it('deve carregar dados', async () => {
  render(<AsyncComponent />);

  await waitFor(() => {
    expect(screen.getByText('Dados carregados')).toBeInTheDocument();
  });
});

// ✅ MELHOR: findBy (aguarda automaticamente)
it('deve carregar dados', async () => {
  render(<AsyncComponent />);
  expect(await screen.findByText('Dados carregados')).toBeInTheDocument();
});
```

### 5. Limpar Mocks

```javascript
describe('Component', () => {
  const mockFn = vi.fn();

  // Limpar ANTES de cada teste
  beforeEach(() => {
    mockFn.mockClear();
  });

  it('teste 1', () => {
    // mockFn começa limpo
  });

  it('teste 2', () => {
    // mockFn começa limpo novamente
  });
});
```

### 6. Organizar com describe

```javascript
describe('Button', () => {
  describe('Renderização', () => {
    it('deve renderizar children', () => {});
    it('deve aplicar className', () => {});
  });

  describe('Interações', () => {
    it('deve chamar onClick', () => {});
    it('não deve chamar onClick quando disabled', () => {});
  });

  describe('Estados', () => {
    it('deve mostrar spinner quando loading', () => {});
    it('deve estar disabled quando loading', () => {});
  });

  describe('Variantes', () => {
    it('deve aplicar variante primary', () => {});
    it('deve aplicar variante secondary', () => {});
  });
});
```

---

## 🐛 Troubleshooting Comum

### Problema 1: "jest is not defined"

**Erro:**
```
ReferenceError: jest is not defined
```

**Causa:** Usando sintaxe do Jest em ambiente Vitest

**Solução:**
```javascript
// ❌ ERRADO (Jest)
jest.fn()
jest.spyOn()
jest.mock()

// ✅ CORRETO (Vitest)
vi.fn()
vi.spyOn()
vi.mock()
```

---

### Problema 2: "Component is not defined"

**Erro:**
```
ReferenceError: Button is not defined
```

**Causa:** Export incorreto em index.js

**Solução:**
```javascript
// ❌ ERRADO
// index.js
export Button from './Button';

// ✅ CORRETO
// index.js
export { Button } from './Button';
export { default } from './Button';
```

---

### Problema 3: "Unable to find element"

**Erro:**
```
TestingLibraryElementError: Unable to find an element with the text: Submit
```

**Causa:** Elemento não existe ou texto está errado

**Solução:**
```javascript
// Debug: Ver o que foi renderizado
import { screen } from '@testing-library/react';
screen.debug(); // Imprime HTML no console

// Ou salvar em arquivo
console.log(screen.container.innerHTML);

// Usar regex case-insensitive
screen.getByText(/submit/i);

// Ou buscar por role
screen.getByRole('button', { name: /submit/i });
```

---

### Problema 4: "act(...) warning"

**Erro:**
```
Warning: An update to Component inside a test was not wrapped in act(...)
```

**Causa:** Estado atualizado fora de act()

**Solução:**
```javascript
// ❌ ERRADO
it('teste', () => {
  const { result } = renderHook(() => useCounter());
  result.current.increment(); // ❌ Sem act()
});

// ✅ CORRETO
it('teste', () => {
  const { result } = renderHook(() => useCounter());
  act(() => {
    result.current.increment();
  });
});

// ✅ CORRETO (async)
it('teste assíncrono', async () => {
  const { result } = renderHook(() => useApi());
  await act(async () => {
    await result.current.execute();
  });
});
```

---

### Problema 5: "Cannot read property of undefined"

**Erro:**
```
TypeError: Cannot read property 'map' of undefined
```

**Causa:** Mock não configurado ou retornando undefined

**Solução:**
```javascript
// ❌ ERRADO
vi.mock('./api');
// api retorna undefined por padrão

// ✅ CORRETO
vi.mock('./api', () => ({
  fetchData: vi.fn().mockResolvedValue({ items: [] }),
}));
```

---

### Problema 6: "Test timeout"

**Erro:**
```
Error: Timeout - Async callback was not invoked within the 5000ms timeout
```

**Causa:** Teste assíncrono não finaliza

**Solução:**
```javascript
// ❌ ERRADO: Esqueceu await
it('teste', async () => {
  const result = asyncFunction(); // ❌ Sem await
  expect(result).toBe('done');
});

// ✅ CORRETO
it('teste', async () => {
  const result = await asyncFunction();
  expect(result).toBe('done');
});

// ✅ CORRETO: Aumentar timeout se necessário
it('teste longo', async () => {
  // ...
}, 10000); // 10 segundos
```

---

## 💼 Exemplos Práticos Completos

### Exemplo 1: Componente Button

**Button.jsx:**
```javascript
import React from 'react';
import styles from './Button.module.css';

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  ...props
}) => {
  const handleClick = (e) => {
    if (!disabled && !loading && onClick) {
      onClick(e);
    }
  };

  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]}`}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading ? <span className={styles.spinner} /> : children}
    </button>
  );
};
```

**Button.test.jsx:**
```javascript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  describe('Renderização', () => {
    it('deve renderizar children', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('deve aplicar variante primary por padrão', () => {
      const { container } = render(<Button>Click</Button>);
      expect(container.firstChild).toHaveClass('primary');
    });

    it('deve aplicar variante customizada', () => {
      const { container } = render(<Button variant="secondary">Click</Button>);
      expect(container.firstChild).toHaveClass('secondary');
    });

    it('deve aplicar tamanho md por padrão', () => {
      const { container } = render(<Button>Click</Button>);
      expect(container.firstChild).toHaveClass('md');
    });

    it('deve aplicar tamanho customizado', () => {
      const { container } = render(<Button size="lg">Click</Button>);
      expect(container.firstChild).toHaveClass('lg');
    });
  });

  describe('Estados', () => {
    it('deve estar habilitado por padrão', () => {
      render(<Button>Click</Button>);
      expect(screen.getByRole('button')).not.toBeDisabled();
    });

    it('deve estar desabilitado quando disabled=true', () => {
      render(<Button disabled>Click</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('deve estar desabilitado quando loading=true', () => {
      render(<Button loading>Click</Button>);
      expect(screen.getByRole('button')).toBeDisabled();
    });

    it('deve mostrar spinner quando loading=true', () => {
      const { container } = render(<Button loading>Click</Button>);
      expect(container.querySelector('.spinner')).toBeInTheDocument();
    });

    it('não deve mostrar children quando loading=true', () => {
      render(<Button loading>Click</Button>);
      expect(screen.queryByText('Click')).not.toBeInTheDocument();
    });
  });

  describe('Interações', () => {
    it('deve chamar onClick quando clicado', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      fireEvent.click(screen.getByText('Click'));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('deve passar evento para onClick', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click</Button>);

      fireEvent.click(screen.getByText('Click'));

      expect(handleClick).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'click' })
      );
    });

    it('não deve chamar onClick quando disabled', () => {
      const handleClick = vi.fn();
      render(<Button disabled onClick={handleClick}>Click</Button>);

      fireEvent.click(screen.getByText('Click'));

      expect(handleClick).not.toHaveBeenCalled();
    });

    it('não deve chamar onClick quando loading', () => {
      const handleClick = vi.fn();
      render(<Button loading onClick={handleClick}>Click</Button>);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Props adicionais', () => {
    it('deve passar props adicionais para button', () => {
      render(<Button data-testid="custom-button" aria-label="Enviar">Click</Button>);

      const button = screen.getByTestId('custom-button');
      expect(button).toHaveAttribute('aria-label', 'Enviar');
    });
  });
});
```

---

### Exemplo 2: Hook useApi

**useApi.js:**
```javascript
import { useState, useCallback } from 'react';

export const useApi = (apiFn) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiFn(...args);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err.message || 'Erro desconhecido';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiFn]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
};
```

**useApi.test.js:**
```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi } from './useApi';

describe('useApi', () => {
  let mockApiFn;

  beforeEach(() => {
    mockApiFn = vi.fn();
  });

  describe('Estado Inicial', () => {
    it('deve iniciar com estado vazio', () => {
      const { result } = renderHook(() => useApi(mockApiFn));

      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Execução Bem-Sucedida', () => {
    it('deve definir loading=true durante execução', async () => {
      mockApiFn.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve('data'), 100)));

      const { result } = renderHook(() => useApi(mockApiFn));

      act(() => {
        result.current.execute();
      });

      expect(result.current.loading).toBe(true);

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
    });

    it('deve definir data após sucesso', async () => {
      const mockData = { id: 1, name: 'Test' };
      mockApiFn.mockResolvedValue(mockData);

      const { result } = renderHook(() => useApi(mockApiFn));

      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it('deve chamar apiFn com argumentos corretos', async () => {
      mockApiFn.mockResolvedValue('data');

      const { result } = renderHook(() => useApi(mockApiFn));

      await act(async () => {
        await result.current.execute('arg1', 'arg2');
      });

      expect(mockApiFn).toHaveBeenCalledWith('arg1', 'arg2');
    });

    it('deve retornar dados do execute', async () => {
      const mockData = { success: true };
      mockApiFn.mockResolvedValue(mockData);

      const { result } = renderHook(() => useApi(mockApiFn));

      let returnedData;
      await act(async () => {
        returnedData = await result.current.execute();
      });

      expect(returnedData).toEqual(mockData);
    });
  });

  describe('Tratamento de Erros', () => {
    it('deve definir error quando apiFn falha', async () => {
      const errorMessage = 'API Error';
      mockApiFn.mockRejectedValue(new Error(errorMessage));

      const { result } = renderHook(() => useApi(mockApiFn));

      await act(async () => {
        try {
          await result.current.execute();
        } catch (err) {
          // Esperado
        }
      });

      expect(result.current.error).toBe(errorMessage);
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
    });

    it('deve lançar erro novamente', async () => {
      const error = new Error('API Error');
      mockApiFn.mockRejectedValue(error);

      const { result } = renderHook(() => useApi(mockApiFn));

      await expect(
        act(async () => {
          await result.current.execute();
        })
      ).rejects.toThrow('API Error');
    });

    it('deve usar mensagem padrão se erro não tem message', async () => {
      mockApiFn.mockRejectedValue({});

      const { result } = renderHook(() => useApi(mockApiFn));

      await act(async () => {
        try {
          await result.current.execute();
        } catch (err) {
          // Esperado
        }
      });

      expect(result.current.error).toBe('Erro desconhecido');
    });
  });

  describe('Reset', () => {
    it('deve limpar todos os estados', async () => {
      mockApiFn.mockResolvedValue('data');
      const { result } = renderHook(() => useApi(mockApiFn));

      // Executar para preencher estado
      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.data).not.toBeNull();

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  describe('Múltiplas Execuções', () => {
    it('deve limpar erro antes de nova execução', async () => {
      mockApiFn
        .mockRejectedValueOnce(new Error('First error'))
        .mockResolvedValueOnce('success');

      const { result } = renderHook(() => useApi(mockApiFn));

      // Primeira execução (erro)
      await act(async () => {
        try {
          await result.current.execute();
        } catch (err) {
          // Esperado
        }
      });

      expect(result.current.error).toBe('First error');

      // Segunda execução (sucesso)
      await act(async () => {
        await result.current.execute();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.data).toBe('success');
    });
  });
});
```

---

### Exemplo 3: Integração ExploitSearchWidget

**ExploitSearchWidget.test.jsx:**
```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExploitSearchWidget } from './ExploitSearchWidget';
import { searchExploits } from '../../../api/worldClassTools';

// Mock da API
vi.mock('../../../api/worldClassTools');

describe('ExploitSearchWidget - Integração', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Renderização Inicial', () => {
    it('deve renderizar formulário de busca', () => {
      render(<ExploitSearchWidget />);

      expect(screen.getByPlaceholderText(/CVE-/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /buscar/i })).toBeInTheDocument();
    });

    it('deve ter botão desabilitado quando input vazio', () => {
      render(<ExploitSearchWidget />);

      const button = screen.getByRole('button', { name: /buscar/i });
      expect(button).toBeDisabled();
    });
  });

  describe('Busca de Exploits', () => {
    it('deve habilitar botão quando CVE é digitado', async () => {
      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'CVE-2024-1234');

      const button = screen.getByRole('button', { name: /buscar/i });
      expect(button).not.toBeDisabled();
    });

    it('deve buscar e exibir resultados completos', async () => {
      const mockResult = {
        result: {
          cve_id: 'CVE-2024-1234',
          description: 'Critical vulnerability',
          cvss_score: 9.8,
          exploits: [
            { title: 'Exploit 1', source: 'Exploit-DB' }
          ],
          recommendations: ['Update to version 2.0'],
          warnings: ['Critical severity']
        }
      };

      searchExploits.mockResolvedValue(mockResult);

      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      // Digitar CVE
      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'CVE-2024-1234');

      // Clicar buscar
      const button = screen.getByRole('button', { name: /buscar/i });
      await user.click(button);

      // Verificar chamada da API
      expect(searchExploits).toHaveBeenCalledWith(
        'CVE-2024-1234',
        expect.objectContaining({
          includePoc: true,
          includeMetasploit: true
        })
      );

      // Aguardar resultados aparecerem
      await waitFor(() => {
        expect(screen.getByText('CVE-2024-1234')).toBeInTheDocument();
        expect(screen.getByText(/Critical vulnerability/i)).toBeInTheDocument();
        expect(screen.getByText('Exploit 1')).toBeInTheDocument();
        expect(screen.getByText(/Update to version 2.0/i)).toBeInTheDocument();
      });
    });

    it('deve mostrar loading durante busca', async () => {
      searchExploits.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ result: {} }), 100))
      );

      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'CVE-2024-1234');

      const button = screen.getByRole('button', { name: /buscar/i });
      await user.click(button);

      // Loading deve aparecer
      expect(screen.getByRole('button', { name: /buscar/i })).toBeDisabled();
      expect(input).toBeDisabled();
    });

    it('deve exibir erro quando busca falha', async () => {
      searchExploits.mockRejectedValue(new Error('Erro de rede'));

      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'CVE-2024-1234');

      const button = screen.getByRole('button', { name: /buscar/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/Erro de rede/i)).toBeInTheDocument();
      });
    });
  });

  describe('Validação', () => {
    it('deve validar formato do CVE', async () => {
      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'INVALID');

      const button = screen.getByRole('button', { name: /buscar/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByText(/Formato inválido/i)).toBeInTheDocument();
      });

      expect(searchExploits).not.toHaveBeenCalled();
    });

    it('deve aceitar CVE em lowercase', async () => {
      searchExploits.mockResolvedValue({ result: { cve_id: 'CVE-2024-1234' } });

      const user = userEvent.setup();
      render(<ExploitSearchWidget />);

      const input = screen.getByPlaceholderText(/CVE-/i);
      await user.type(input, 'cve-2024-1234');

      const button = screen.getByRole('button', { name: /buscar/i });
      await user.click(button);

      expect(searchExploits).toHaveBeenCalledWith('CVE-2024-1234', expect.anything());
    });
  });
});
```

---

## ✅ Checklist de Qualidade

### Antes de Commitar

- [ ] **Todos os testes passam** (`npm test`)
- [ ] **Coverage mínimo atingido** (80%+ shared, 60%+ widgets)
- [ ] **Sem warnings no console**
- [ ] **Testes cobrem casos felizes E edge cases**
- [ ] **Testes são independentes** (não dependem de ordem)
- [ ] **Mocks estão limpos** (beforeEach/afterEach)
- [ ] **Nomes descritivos** nos testes
- [ ] **Um conceito por teste**

### Coverage por Tipo

| Tipo | Coverage Mínimo | Prioridade |
|------|-----------------|------------|
| Shared Components | 80% | Alta |
| Hooks Customizados | 90% | Crítica |
| Widgets | 60% | Média |
| Utils | 100% | Alta |

### Métricas de Sucesso

```bash
# Rodar coverage
npm run test:coverage

# Verificar relatório em:
# coverage/index.html
```

**Aprovado se:**
- ✅ Statements coverage > 70%
- ✅ Branches coverage > 60%
- ✅ Functions coverage > 70%
- ✅ Lines coverage > 70%

---

## 🎓 Conclusão

### Resumo Executivo

Testes são **investimento, não custo**. Eles:

1. ✅ **Economizam tempo** (menos debugging manual)
2. ✅ **Aumentam confiança** (refatoração segura)
3. ✅ **Documentam código** (exemplos de uso)
4. ✅ **Melhoram design** (código testável é código bem feito)

### Próximos Passos

1. **Ler este guia completamente** (sim, tudo!)
2. **Escolher 1 componente simples** (ex: Button)
3. **Escrever primeiro teste**
4. **Ver teste passar** 🎉
5. **Refatorar com confiança**
6. **Repetir para todos os componentes**

### Recursos Adicionais

- **Vitest Docs**: https://vitest.dev
- **React Testing Library**: https://testing-library.com/react
- **Testing Playground**: https://testing-playground.com
- **Common Mistakes**: https://kentcdodds.com/blog/common-mistakes-with-react-testing-library

---

## 📞 Suporte

**Dúvidas sobre testes?**

1. Consulte este guia
2. Veja exemplos práticos na seção anterior
3. Execute `screen.debug()` para ver o que foi renderizado
4. Pergunte no canal da equipe

**Problemas técnicos?**

1. Verifique TESTING_REPORT.md
2. Rode `npm run test:ui` para debug visual
3. Limpe node_modules e reinstale (`rm -rf node_modules && npm install`)

---

**Criado com ❤️ para a equipe Vértice**
**"Teste hoje, agradeça amanhã"** 🧪

---

**Versão:** 1.0
**Última atualização:** 2025-10-01
**Mantido por:** Claude Code (Senior Testing Engineer)
