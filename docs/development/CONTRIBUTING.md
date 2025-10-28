# Contributing to VÉRTICE Frontend

Obrigado por considerar contribuir para o projeto VÉRTICE! Este documento fornece diretrizes e padrões para contribuições.

---

## 📋 Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Contribuir](#como-contribuir)
3. [Padrões de Código](#padrões-de-código)
4. [Estrutura do Projeto](#estrutura-do-projeto)
5. [Desenvolvimento](#desenvolvimento)
6. [Testes](#testes)
7. [Commits](#commits)
8. [Pull Requests](#pull-requests)
9. [Reportando Bugs](#reportando-bugs)

---

## Código de Conduta

Este projeto adere a um código de conduta. Ao participar, espera-se que você mantenha este código:

- ✅ Seja respeitoso e inclusivo
- ✅ Aceite críticas construtivas
- ✅ Foque no que é melhor para a comunidade
- ✅ Mostre empatia com outros membros

---

## Como Contribuir

### 1. Fork e Clone

```bash
# Fork o repositório no GitHub
# Clone seu fork
git clone https://github.com/seu-usuario/vertice.git
cd vertice/frontend

# Adicione o upstream
git remote add upstream https://github.com/original/vertice.git
```

### 2. Crie uma Branch

```bash
# Atualize main
git checkout main
git pull upstream main

# Crie branch de feature
git checkout -b feature/nome-da-feature

# Ou branch de bugfix
git checkout -b fix/nome-do-bug
```

### 3. Desenvolva

- Siga os [Padrões de Código](#padrões-de-código)
- Escreva testes
- Documente mudanças
- Teste localmente

### 4. Commit

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
```

Veja [Commits](#commits) para convenções.

### 5. Push e PR

```bash
git push origin feature/nome-da-feature
```

Abra Pull Request no GitHub.

---

## Padrões de Código

### JavaScript/React

#### 1. ES6+ Moderno

```javascript
// ✅ BOM
const MyComponent = ({ prop1, prop2 }) => {
  const [state, setState] = useState(null);

  useEffect(() => {
    // Effect logic
  }, [dependencies]);

  return <div>{prop1}</div>;
};

// ❌ RUIM
var MyComponent = function(props) {
  // Old syntax
};
```

#### 2. Hooks First

```javascript
// ✅ BOM - Use hooks
const useCustomLogic = () => {
  const [value, setValue] = useState(0);
  // Logic
  return { value, setValue };
};

// ❌ RUIM - Class components (apenas ErrorBoundary)
class MyComponent extends React.Component {
  // Avoid unless necessary
}
```

#### 3. PropTypes

```javascript
import PropTypes from 'prop-types';

MyComponent.propTypes = {
  title: PropTypes.string.isRequired,
  count: PropTypes.number,
  onClick: PropTypes.func,
  items: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string
  }))
};

MyComponent.defaultProps = {
  count: 0,
  items: []
};
```

#### 4. Performance

```javascript
// ✅ BOM - Memoize callbacks
const handleClick = useCallback(() => {
  // Handler logic
}, [dependencies]);

// ✅ BOM - Memoize components
const MemoizedComponent = React.memo(({ prop }) => {
  return <div>{prop}</div>;
});

// ✅ BOM - useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);
```

#### 5. Async/Await

```javascript
// ✅ BOM
const fetchData = async () => {
  try {
    const response = await fetch('/api/data');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
};

// ❌ RUIM - Nested promises
fetch('/api/data')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));
```

### CSS

#### 1. CSS Modules ou Styled Components

```javascript
// ✅ BOM - CSS Modules
import styles from './MyComponent.module.css';

const MyComponent = () => (
  <div className={styles.container}>
    <h1 className={styles.title}>Title</h1>
  </div>
);
```

#### 2. BEM para Classes Globais

```css
/* ✅ BOM */
.dashboard-header { }
.dashboard-header__title { }
.dashboard-header__title--large { }

/* ❌ RUIM */
.title { }
.big-title { }
```

#### 3. Variáveis CSS

```css
:root {
  --color-primary: #00f0ff;
  --color-bg-dark: #0a1929;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
}

.component {
  color: var(--color-primary);
  padding: var(--spacing-md);
}
```

### Acessibilidade (WCAG 2.1 AA)

#### 1. Semantic HTML

```javascript
// ✅ BOM
<header role="banner">
  <nav role="navigation">
    <ul>
      <li><a href="/home">Home</a></li>
    </ul>
  </nav>
</header>
<main role="main">
  <article>Content</article>
</main>

// ❌ RUIM
<div class="header">
  <div class="nav">...</div>
</div>
```

#### 2. ARIA Labels

```javascript
// ✅ BOM
<button
  aria-label="Close dialog"
  aria-haspopup="dialog"
  onClick={closeDialog}
>
  <CloseIcon aria-hidden="true" />
</button>

// ❌ RUIM
<button onClick={closeDialog}>
  <CloseIcon />
</button>
```

#### 3. Keyboard Navigation

```javascript
// ✅ BOM - Suporte completo a teclado
const handleKeyDown = (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    handleAction();
  }
  if (e.key === 'Escape') {
    handleClose();
  }
};

<div
  role="button"
  tabIndex={0}
  onKeyDown={handleKeyDown}
  onClick={handleAction}
>
  Click or press Enter
</div>
```

#### 4. Focus Management

```javascript
// ✅ BOM - Focus trap em modals
import { useFocusTrap } from './hooks/useFocusTrap';

const Modal = ({ isOpen, onClose }) => {
  const trapRef = useFocusTrap({
    active: isOpen,
    returnFocus: true,
    onEscape: onClose
  });

  return (
    <div ref={trapRef} role="dialog" aria-modal="true">
      {/* Content */}
    </div>
  );
};
```

### Segurança

#### 1. Input Sanitization

```javascript
import { escapeHTML, sanitizeSQLInput } from './utils/security';

// ✅ BOM - Sanitize user input
const handleSubmit = (userInput) => {
  const safe = escapeHTML(userInput);
  setData(safe);
};

// ❌ RUIM - Raw user input
const handleSubmit = (userInput) => {
  setData(userInput); // XSS risk
};
```

#### 2. Rate Limiting

```javascript
import { useRateLimit } from './hooks/useRateLimit';

// ✅ BOM
const { execute } = useRateLimit('api-key', {
  maxRequests: 60,
  windowMs: 60000
});

const handleAPI = async () => {
  await execute(async () => {
    const res = await fetch('/api/endpoint');
    return res.json();
  });
};
```

---

## Estrutura do Projeto

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboards/          # Dashboard components
│   │   │   ├── DefensiveDashboard/
│   │   │   ├── OffensiveDashboard/
│   │   │   └── PurpleTeamDashboard/
│   │   ├── shared/              # Shared components
│   │   │   ├── ErrorBoundary.jsx
│   │   │   ├── LanguageSwitcher.jsx
│   │   │   └── SkipLink.jsx
│   │   └── ...
│   ├── hooks/                   # Custom hooks
│   │   ├── useWebSocket.js
│   │   ├── useKeyboardNavigation.js
│   │   ├── useFocusTrap.js
│   │   └── useRateLimit.js
│   ├── stores/                  # Zustand stores
│   │   ├── defensiveStore.js
│   │   └── offensiveStore.js
│   ├── utils/                   # Utilities
│   │   ├── security.js
│   │   └── accessibility.js
│   ├── i18n/                    # Internationalization
│   │   ├── config.js
│   │   └── locales/
│   │       ├── pt-BR.json
│   │       └── en-US.json
│   ├── config/                  # Configuration
│   │   ├── queryClient.js
│   │   └── security.js
│   ├── styles/                  # Global styles
│   │   └── accessibility.css
│   ├── tests/                   # Test files
│   │   └── setup.js
│   └── App.jsx
├── public/
├── docs/                        # Documentation
│   ├── COMPONENTS_API.md
│   ├── CONTRIBUTING.md
│   ├── ACCESSIBILITY_IMPLEMENTATION.md
│   └── ...
├── package.json
├── vite.config.js
└── vitest.config.js
```

### Onde Adicionar Código

| Tipo | Localização | Exemplo |
|------|-------------|---------|
| **Novo Dashboard** | `src/components/dashboards/` | `OSINTDashboard/` |
| **Componente Compartilhado** | `src/components/shared/` | `Button.jsx` |
| **Custom Hook** | `src/hooks/` | `useAuth.js` |
| **Utilitário** | `src/utils/` | `formatDate.js` |
| **Zustand Store** | `src/stores/` | `authStore.js` |
| **Tradução** | `src/i18n/locales/` | `pt-BR.json` |
| **Estilos Globais** | `src/styles/` | `variables.css` |
| **Testes** | Co-localizado | `Button.test.jsx` |

---

## Desenvolvimento

### Setup Inicial

```bash
cd frontend
npm install
```

### Scripts Disponíveis

```bash
# Desenvolvimento
npm run dev              # Vite dev server (port 5173)

# Build
npm run build            # Production build
npm run preview          # Preview production build

# Testes
npm test                 # Run all tests
npm test -- --ui         # Interactive UI
npm test -- --coverage   # With coverage

# Linting (quando disponível)
npm run lint             # ESLint
npm run lint:fix         # Auto-fix
```

### Environment Variables

Crie `.env.local`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_ENV=development
```

### Hot Reload

O Vite fornece HMR (Hot Module Replacement) automático. Mudanças aparecem instantaneamente.

---

## Testes

### Framework: Vitest + Testing Library

#### 1. Estrutura de Teste

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MyComponent from './MyComponent';

describe('MyComponent', () => {
  beforeEach(() => {
    // Setup
  });

  it('should render correctly', () => {
    render(<MyComponent title="Test" />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });

  it('should handle click events', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<MyComponent onClick={handleClick} />);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should fetch data on mount', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        json: () => Promise.resolve({ data: 'test' })
      })
    );

    render(<MyComponent />);

    await waitFor(() => {
      expect(screen.getByText('test')).toBeInTheDocument();
    });
  });
});
```

#### 2. Coverage Mínimo

| Métrica | Mínimo |
|---------|--------|
| Statements | 80% |
| Branches | 80% |
| Functions | 80% |
| Lines | 80% |

#### 3. Testes Obrigatórios

- ✅ Todos os custom hooks
- ✅ Todos os componentes compartilhados
- ✅ Todos os utilitários
- ✅ Todas as stores (Zustand)
- ✅ Casos de erro (error boundaries, try/catch)

---

## Commits

### Conventional Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

#### Tipos

| Tipo | Uso |
|------|-----|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `docs` | Mudanças em documentação |
| `style` | Formatação, espaços (não muda código) |
| `refactor` | Refatoração (não adiciona feature ou fix) |
| `perf` | Melhoria de performance |
| `test` | Adiciona ou corrige testes |
| `chore` | Tarefas de build, configs |
| `ci` | CI/CD changes |
| `revert` | Reverte commit anterior |

#### Exemplos

```bash
# Feature
git commit -m "feat(dashboard): add real-time metrics WebSocket"

# Fix
git commit -m "fix(auth): resolve token expiration issue"

# Docs
git commit -m "docs: update contributing guidelines"

# Refactor
git commit -m "refactor(hooks): extract keyboard nav logic to custom hook"

# Performance
git commit -m "perf(table): memoize expensive calculations"

# Breaking change
git commit -m "feat(api)!: change API response format

BREAKING CHANGE: API now returns { data, meta } instead of raw array"
```

#### Scope (Opcional)

- `dashboard` - Dashboard components
- `auth` - Autenticação
- `hooks` - Custom hooks
- `stores` - Zustand stores
- `i18n` - Internacionalização
- `a11y` - Acessibilidade
- `security` - Segurança
- `test` - Testes

---

## Pull Requests

### Checklist

Antes de abrir PR, certifique-se:

- [ ] Código segue padrões do projeto
- [ ] Testes adicionados/atualizados
- [ ] Testes passando (`npm test`)
- [ ] Build funciona (`npm run build`)
- [ ] Documentação atualizada
- [ ] Commits seguem Conventional Commits
- [ ] Branch atualizada com `main`
- [ ] Self-review realizado
- [ ] Screenshots (se UI changes)

### Template de PR

```markdown
## Descrição

Breve descrição das mudanças.

## Tipo de Mudança

- [ ] Bug fix
- [ ] Nova feature
- [ ] Breaking change
- [ ] Documentação

## Como Testar

1. Passo 1
2. Passo 2
3. Verificar resultado esperado

## Screenshots (se aplicável)

[Screenshots ou GIFs]

## Checklist

- [ ] Testes adicionados
- [ ] Documentação atualizada
- [ ] Build passa
- [ ] Self-review realizado
```

### Review Process

1. **Automated checks** - CI/CD executa testes e build
2. **Code review** - Pelo menos 1 aprovação necessária
3. **Testing** - Reviewer testa localmente
4. **Merge** - Squash and merge (mantém histórico limpo)

---

## Reportando Bugs

### Template de Issue

```markdown
## Descrição do Bug

Descrição clara e concisa do bug.

## Passos para Reproduzir

1. Ir para '...'
2. Clicar em '...'
3. Scroll até '...'
4. Ver erro

## Comportamento Esperado

O que deveria acontecer.

## Comportamento Atual

O que está acontecendo.

## Screenshots

[Se aplicável]

## Ambiente

- OS: [e.g. macOS 13.0]
- Browser: [e.g. Chrome 120]
- Versão: [e.g. 1.0.0]

## Contexto Adicional

Qualquer outra informação relevante.

## Possível Solução

[Opcional] Sugestão de como resolver.
```

---

## Recursos Adicionais

### Documentação

- [COMPONENTS_API.md](./COMPONENTS_API.md) - API de componentes e hooks
- [ACCESSIBILITY_IMPLEMENTATION.md](./ACCESSIBILITY_IMPLEMENTATION.md) - Guia de acessibilidade
- [SECURITY_HARDENING.md](./SECURITY_HARDENING.md) - Práticas de segurança
- [I18N_IMPLEMENTATION.md](./I18N_IMPLEMENTATION.md) - Internacionalização

### Links Úteis

- [React Docs](https://react.dev/)
- [Vite Docs](https://vitejs.dev/)
- [Vitest Docs](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## Dúvidas?

- 📧 Email: vertice-dev@example.com
- 💬 Discord: [Link]
- 📖 Wiki: [Link]

---

**Obrigado por contribuir! 🚀**
