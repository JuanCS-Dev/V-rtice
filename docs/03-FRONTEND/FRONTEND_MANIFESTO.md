# 🎯 MANIFESTO DO FRONTEND - PROJETO VÉRTICE

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Filosofia de Desenvolvimento](#filosofia-de-desenvolvimento)
3. [Arquitetura](#arquitetura)
4. [Design System](#design-system)
5. [Padrões de Código](#padrões-de-código)
6. [Guia de Componentes](#guia-de-componentes)
7. [Guia de Estilização](#guia-de-estilização)
8. [Hooks Customizados](#hooks-customizados)
9. [Testes](#testes)
10. [Troubleshooting](#troubleshooting)
11. [Blueprint para Novas Features](#blueprint-para-novas-features)
12. [Manutenção e Evolução](#manutenção-e-evolução)

---

## 🎯 VISÃO GERAL

### Missão do Frontend
Prover uma interface cyberpunk de alta performance para operações de **OSINT**, **Cyber Security** e **Analytics**, mantendo:
- 🎨 **Consistência visual** em todos os módulos
- ⚡ **Performance otimizada** mesmo com dados em tempo real
- 🧩 **Componentes reutilizáveis** e modulares
- 📦 **Manutenibilidade** para equipes de qualquer tamanho

### Stack Tecnológica
```yaml
Framework: React 18
Build Tool: Vite
Estilização: CSS Modules + Design Tokens
State: React Hooks (useState, useEffect, useCallback, useMemo)
Maps: Leaflet
Icons: Font Awesome
Temas: Cyber (Cyan), OSINT (Purple), Analytics (Blue)
```

### Métricas de Qualidade
```yaml
Linhas por Componente: < 200 linhas (ideal: < 150)
CSS Hardcoded: 0% (100% em CSS Modules)
Componentes Reutilizáveis: 15+ componentes shared
Code Duplication: < 5%
Performance: Time to Interactive < 2s
```

---

## 💭 FILOSOFIA DE DESENVOLVIMENTO

### Princípios Fundamentais

#### 1. **Component-Driven Development**
> "Componentes pequenos, focados e reutilizáveis são a base de tudo."

**✅ BOM:**
```jsx
// Componente focado em uma única responsabilidade
const Button = ({ children, variant, onClick }) => (
  <button className={styles[variant]} onClick={onClick}>
    {children}
  </button>
);
```

**❌ RUIM:**
```jsx
// Componente que faz TUDO
const Dashboard = () => {
  // 500 linhas de lógica misturada...
  // Estado + API + Rendering + Estilos...
};
```

#### 2. **Separation of Concerns**
> "Lógica, apresentação e estilos devem viver em lugares separados."

```
Component/
├── Component.jsx        # Apenas JSX e coordenação
├── Component.module.css # Apenas estilos
├── hooks/
│   └── useComponent.js  # Apenas lógica de negócio
└── components/          # Subcomponentes
```

#### 3. **Design Tokens First**
> "Nunca hardcode cores, espaçamentos ou tipografia. Use tokens."

**✅ BOM:**
```css
.card {
  background: var(--bg-secondary);
  padding: var(--space-4);
  color: var(--text-primary);
  border: var(--border-1) solid var(--color-cyber-primary);
}
```

**❌ RUIM:**
```css
.card {
  background: #0a0a0a;
  padding: 16px;
  color: #ffffff;
  border: 1px solid #00ffff;
}
```

#### 4. **Progressive Enhancement**
> "Funcionalidade básica primeiro, enhancements depois."

1. Componente funciona sem CSS
2. Adiciona estilos base
3. Adiciona animações e efeitos
4. Adiciona otimizações de performance

#### 5. **Zero Surprises**
> "O código deve ser previsível e fácil de entender."

- Use nomes descritivos
- Mantenha estrutura consistente
- Documente decisões não-óbvias
- Evite "magic numbers"

---

## 🏗️ ARQUITETURA

### Estrutura de Diretórios

```
frontend/src/
├── components/
│   ├── shared/                      # Componentes reutilizáveis (NUNCA toque sem motivo)
│   │   ├── Button/
│   │   │   ├── Button.jsx
│   │   │   ├── Button.module.css
│   │   │   ├── Button.test.jsx
│   │   │   └── index.js
│   │   ├── Input/
│   │   ├── Card/
│   │   ├── Badge/
│   │   ├── Alert/
│   │   ├── Modal/
│   │   ├── LoadingSpinner/
│   │   └── index.js               # Export central
│   │
│   ├── cyber/                       # Módulo Cyber Security
│   │   ├── CyberDashboard.jsx
│   │   ├── CyberHeader.jsx
│   │   ├── ExploitSearchWidget/   # Widget modular (PADRÃO)
│   │   │   ├── ExploitSearchWidget.jsx
│   │   │   ├── ExploitSearchWidget.module.css
│   │   │   ├── components/
│   │   │   │   ├── SearchForm.jsx
│   │   │   │   ├── CVEInfo.jsx
│   │   │   │   └── ExploitList.jsx
│   │   │   ├── hooks/
│   │   │   │   └── useExploitSearch.js
│   │   │   └── index.js
│   │   ├── NetworkMonitor/
│   │   └── ThreatMap/
│   │
│   ├── osint/                       # Módulo OSINT
│   │   ├── OSINTDashboard.jsx
│   │   ├── OSINTHeader.jsx
│   │   ├── SocialMediaWidget/
│   │   ├── BreachDataWidget/
│   │   └── DarkWebModule/
│   │
│   ├── analytics/                   # Módulo Analytics
│   │   ├── AnomalyDetectionWidget/
│   │   └── MetricsPanel/
│   │
│   ├── terminal/                    # Módulo Terminal/CLI
│   │   ├── TerminalDashboard.jsx
│   │   └── TerminalEmulator/
│   │
│   └── admin/                       # Módulo Admin
│       └── AdminDashboard.jsx
│
├── hooks/                           # Custom hooks compartilhados
│   ├── useApi.js
│   ├── useDebounce.js
│   ├── useLocalStorage.js
│   ├── useKeyPress.js
│   └── index.js
│
├── api/                             # Camada de API
│   ├── worldClassTools.js          # World-class tools API
│   ├── sinesp.js                   # SINESP API
│   └── config.js                   # Configurações de API
│
├── utils/                           # Utilitários puros
│   ├── formatters.js               # Formatação de dados
│   ├── validators.js               # Validações
│   └── constants.js                # Constantes da aplicação
│
├── styles/                          # Sistema de Design
│   ├── tokens/                     # Design Tokens (NÃO MODIFICAR sem aprovação)
│   │   ├── colors.css              # Paleta de cores
│   │   ├── spacing.css             # Escala de espaçamento
│   │   └── typography.css          # Tipografia
│   ├── themes/                     # Temas específicos
│   │   ├── cyber.css
│   │   ├── osint.css
│   │   └── analytics.css
│   ├── base/                       # Estilos globais
│   │   ├── reset.css               # CSS Reset
│   │   ├── global.css              # Estilos globais
│   │   └── utilities.css           # Classes utilitárias
│   └── mixins/                     # Mixins e animações
│       └── animations.css
│
├── App.jsx                          # Componente raiz
├── main.jsx                         # Entry point
└── index.css                        # Importações globais de CSS
```

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERACTION                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               COMPONENT (Presentation)                   │
│  - Renderiza UI                                         │
│  - Delega lógica para hooks                             │
│  - Usa componentes shared                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CUSTOM HOOK (Business Logic)                │
│  - Gerencia estado                                      │
│  - Chama APIs                                           │
│  - Processa dados                                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   API LAYER                              │
│  - Faz requisições HTTP                                 │
│  - Trata erros                                          │
│  - Retorna dados formatados                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND APIs                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 DESIGN SYSTEM

### Paleta de Cores

#### Cores Primárias
```css
/* CYBER - Cyan/Blue */
--color-cyber-primary: #00ffff;      /* Neon Cyan */
--color-cyber-secondary: #0088ff;    /* Electric Blue */
--color-cyber-accent: #00aaff;       /* Sky Blue */

/* OSINT - Purple/Pink */
--color-osint-primary: #a855f7;      /* Vivid Purple */
--color-osint-secondary: #ec4899;    /* Hot Pink */
--color-osint-accent: #d946ef;       /* Magenta */

/* ANALYTICS - Blue/Cyan */
--color-analytics-primary: #3b82f6;  /* Royal Blue */
--color-analytics-secondary: #06b6d4; /* Cyan */
--color-analytics-accent: #8b5cf6;   /* Violet */
```

#### Cores Semânticas
```css
--color-success: #10b981;   /* Green */
--color-warning: #f59e0b;   /* Amber */
--color-error: #ef4444;     /* Red */
--color-info: #06b6d4;      /* Cyan */
```

#### Cores de Severidade (Vulnerabilidades)
```css
--color-critical: #ff0040;  /* Critical Red */
--color-high: #ff4000;      /* High Orange */
--color-medium: #ffaa00;    /* Medium Yellow */
--color-low: #00aa00;       /* Low Green */
```

#### Backgrounds
```css
--bg-primary: #000000;      /* Pure Black */
--bg-secondary: #0a0a0a;    /* Almost Black */
--bg-tertiary: #1a1a1a;     /* Dark Gray */
--bg-overlay: rgba(0, 0, 0, 0.8);
```

### Escala de Espaçamento

```css
--space-1: 0.25rem;   /* 4px  - Micro */
--space-2: 0.5rem;    /* 8px  - Tiny */
--space-3: 0.75rem;   /* 12px - Small */
--space-4: 1rem;      /* 16px - Base */
--space-5: 1.5rem;    /* 24px - Medium */
--space-6: 2rem;      /* 32px - Large */
--space-8: 3rem;      /* 48px - XLarge */
--space-10: 4rem;     /* 64px - XXLarge */
```

**Quando usar:**
- `space-1, space-2`: Espaçamento interno de badges, tags
- `space-3, space-4`: Padding de inputs, buttons
- `space-5, space-6`: Gaps entre seções, cards
- `space-8, space-10`: Margens de layout, separação de módulos

### Tipografia

```css
/* Font Families */
--font-mono: 'Courier New', monospace;  /* Para interface cyber */
--font-sans: -apple-system, system-ui;  /* Para texto legível */

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px - Tags, badges */
--text-sm: 0.875rem;   /* 14px - Hints, secondary text */
--text-base: 1rem;     /* 16px - Body text */
--text-lg: 1.125rem;   /* 18px - Subtítulos */
--text-xl: 1.25rem;    /* 20px - Títulos */
--text-2xl: 1.5rem;    /* 24px - Headers */
--text-3xl: 1.875rem;  /* 30px - Page titles */
```

### Componentes do Design System

#### 1. Button Variants
```jsx
<Button variant="primary">Primary Action</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="danger">Delete</Button>
<Button variant="success">Confirm</Button>
<Button variant="osint">OSINT Action</Button>
<Button variant="analytics">Analytics</Button>
```

#### 2. Input Variants
```jsx
<Input variant="cyber" />      {/* Cyan border/glow */}
<Input variant="osint" />      {/* Purple border/glow */}
<Input variant="analytics" />  {/* Blue border/glow */}
<Input variant="minimal" />    {/* Subtle border */}
```

#### 3. Card Variants
```jsx
<Card variant="cyber">Cyber content</Card>
<Card variant="osint">OSINT content</Card>
<Card variant="analytics">Analytics</Card>
<Card variant="success">Success message</Card>
<Card variant="warning">Warning</Card>
<Card variant="error">Error</Card>
<Card variant="glass">Glassmorphism</Card>
```

---

## 📝 PADRÕES DE CÓDIGO

### 1. Nomenclatura

#### Componentes (PascalCase)
```jsx
✅ BOM
- Button.jsx
- ExploitSearchWidget.jsx
- CVEInfo.jsx

❌ RUIM
- button.jsx
- exploitSearchWidget.jsx
- cve-info.jsx
```

#### Hooks (camelCase com prefixo "use")
```jsx
✅ BOM
- useApi.js
- useExploitSearch.js
- useDebounce.js

❌ RUIM
- Api.js
- exploitSearch.js
- debounce.js
```

#### CSS Modules (camelCase)
```css
✅ BOM
.container { }
.searchForm { }
.cveHeader { }

❌ RUIM
.Container { }
.search-form { }
.cve_header { }
```

#### Constantes (SCREAMING_SNAKE_CASE)
```js
✅ BOM
const API_BASE_URL = 'http://localhost:8000';
const MAX_RETRIES = 3;

❌ RUIM
const apiBaseUrl = 'http://localhost:8000';
const maxRetries = 3;
```

### 2. Estrutura de Componente

```jsx
/**
 * ComponentName - Breve descrição
 *
 * Descrição mais detalhada do que o componente faz,
 * quando usar, e qualquer detalhe importante.
 *
 * @example
 * <ComponentName prop1="value" prop2={func} />
 */

import React from 'react';
import { SharedComponent } from '../../shared';
import { useCustomHook } from './hooks/useCustomHook';
import styles from './ComponentName.module.css';

export const ComponentName = ({
  prop1,
  prop2 = 'default',
  onEvent,
  children,
  className = '',
  ...props
}) => {
  // 1. Hooks customizados
  const { data, loading, error } = useCustomHook();

  // 2. State local
  const [localState, setLocalState] = useState(null);

  // 3. Efeitos
  useEffect(() => {
    // Efeito aqui
  }, [dependencies]);

  // 4. Handlers
  const handleEvent = useCallback(() => {
    // Handler logic
  }, [dependencies]);

  // 5. Computed values
  const computedValue = useMemo(() => {
    return expensiveCalculation(data);
  }, [data]);

  // 6. Early returns (loading, error, empty states)
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  // 7. Render
  return (
    <div className={`${styles.container} ${className}`} {...props}>
      {/* JSX aqui */}
    </div>
  );
};

export default ComponentName;
```

### 3. Props Destructuring

```jsx
✅ BOM - Destructure props com defaults
const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  ...props
}) => { };

❌ RUIM - Acessar via props.
const Button = (props) => {
  return <button onClick={props.onClick}>{props.children}</button>
};
```

### 4. Conditional Rendering

```jsx
✅ BOM - Use early returns
if (!data) return null;
if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;

return <DataDisplay data={data} />;

❌ RUIM - Nested ternaries
return (
  <div>
    {loading ? (
      <Spinner />
    ) : error ? (
      <Error />
    ) : data ? (
      <Display />
    ) : null}
  </div>
);
```

### 5. Event Handlers

```jsx
✅ BOM - Use callbacks para evitar re-renders
const handleClick = useCallback(() => {
  console.log('clicked');
}, []);

✅ BOM - Nome descritivo
const handleSearchSubmit = () => { };
const handleInputChange = () => { };

❌ RUIM - Arrow function inline
<button onClick={() => console.log('click')}>

❌ RUIM - Nome genérico
const onClick = () => { };
const onChange = () => { };
```

### 6. CSS Modules

```css
/* ✅ BOM - Organizado e semântico */
.container {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--space-4);

  /* Tamanho */
  width: 100%;
  max-width: var(--widget-max-width);

  /* Espaçamento */
  padding: var(--space-5);
  margin: 0 auto;

  /* Visual */
  background: var(--bg-secondary);
  border: var(--border-1) solid var(--border-primary);
  border-radius: var(--radius-lg);

  /* Transições */
  transition: all var(--duration-base) var(--ease-out);
}

/* ❌ RUIM - Hardcoded e desorganizado */
.container {
  background: #0a0a0a;
  padding: 20px;
  border: 1px solid rgba(255,255,255,0.2);
  display: flex;
  transition: 0.2s;
  border-radius: 8px;
}
```

---

## 🧩 GUIA DE COMPONENTES

### Anatomia de um Widget Completo

Vamos usar o **ExploitSearchWidget** como exemplo de referência:

```
ExploitSearchWidget/
├── ExploitSearchWidget.jsx          # Componente principal (80 linhas)
├── ExploitSearchWidget.module.css   # Estilos do container
├── components/                       # Subcomponentes
│   ├── SearchForm.jsx                # Formulário de busca
│   ├── SearchForm.module.css
│   ├── CVEInfo.jsx                   # Informações do CVE
│   ├── CVEInfo.module.css
│   ├── ExploitList.jsx               # Lista de exploits
│   ├── ExploitList.module.css
│   ├── RecommendationsList.jsx       # Recomendações
│   └── RecommendationsList.module.css
├── hooks/
│   └── useExploitSearch.js           # Lógica de negócio
└── index.js                          # Export central
```

#### Componente Principal
```jsx
// ExploitSearchWidget.jsx
import React from 'react';
import { Card } from '../../shared/Card';
import { SearchForm } from './components/SearchForm';
import { CVEInfo } from './components/CVEInfo';
import { ExploitList } from './components/ExploitList';
import { RecommendationsList } from './components/RecommendationsList';
import { useExploitSearch } from './hooks/useExploitSearch';
import styles from './ExploitSearchWidget.module.css';

export const ExploitSearchWidget = () => {
  // Hook customizado encapsula TODA a lógica
  const { result, loading, error, search } = useExploitSearch();

  return (
    <Card
      title="CVE EXPLOIT SEARCH"
      badge="NSA-GRADE"
      variant="cyber"
      className={styles.widget}
    >
      <div className={styles.container}>
        {/* Subcomponente: Form */}
        <SearchForm
          onSearch={search}
          loading={loading}
          error={error}
        />

        {/* Subcomponente: Resultados */}
        {result && (
          <div className={styles.results}>
            <CVEInfo data={result} />
            <ExploitList exploits={result.exploits} />
            <RecommendationsList
              recommendations={result.recommendations}
              affectedSystems={result.affected_systems}
              warnings={result.warnings}
            />
          </div>
        )}
      </div>
    </Card>
  );
};
```

#### Hook Customizado
```jsx
// hooks/useExploitSearch.js
import { useState, useCallback } from 'react';
import { searchExploits } from '../../../../api/worldClassTools';

export const useExploitSearch = () => {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (cveId) => {
    // Validação
    if (!cveId?.trim()) {
      setError('CVE ID é obrigatório');
      return;
    }

    if (!/^CVE-\d{4}-\d{4,}$/i.test(cveId.trim())) {
      setError('Formato inválido. Use: CVE-YYYY-NNNN');
      return;
    }

    // Execução
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await searchExploits(cveId.toUpperCase(), {
        includePoc: true,
        includeMetasploit: true
      });
      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao buscar exploits');
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
    setLoading(false);
  }, []);

  return { result, loading, error, search, reset };
};
```

#### Subcomponente
```jsx
// components/SearchForm.jsx
import React, { useState } from 'react';
import { Button } from '../../../shared/Button';
import { Input } from '../../../shared/Input';
import styles from './SearchForm.module.css';

export const SearchForm = ({ onSearch, loading, error }) => {
  const [cveId, setCveId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(cveId);
  };

  return (
    <div className={styles.searchSection}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <Input
          type="text"
          placeholder="CVE-2024-1234"
          value={cveId}
          onChange={(e) => setCveId(e.target.value)}
          disabled={loading}
          variant="cyber"
          size="lg"
          icon={<i className="fas fa-bug"></i>}
          error={error}
        />
        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={loading}
          disabled={!cveId.trim()}
          icon={<i className="fas fa-search"></i>}
        >
          BUSCAR
        </Button>
      </form>
      <p className={styles.hint}>
        Busca em 40K+ exploits (Exploit-DB, Metasploit, NVD)
      </p>
    </div>
  );
};
```

### Quando Criar um Componente Compartilhado?

**✅ CRIE quando:**
- Usado em 3+ lugares diferentes
- Representa um padrão de UI comum (Button, Input, Card)
- Pode ser parametrizado facilmente
- Não tem lógica de negócio específica

**❌ NÃO CRIE quando:**
- Usado em apenas 1 lugar
- Tem lógica muito específica de um módulo
- Difícil de parametrizar sem tornar complexo

### Checklist para Componentes Shared

Antes de adicionar um componente em `/shared`:

- [ ] É usado (ou será usado) em 3+ lugares?
- [ ] É genérico o suficiente?
- [ ] Tem testes?
- [ ] Tem documentação JSDoc?
- [ ] Usa design tokens (não hardcode)?
- [ ] Suporta variantes necessárias?
- [ ] É acessível (a11y)?

---

## 🎨 GUIA DE ESTILIZAÇÃO

### Hierarquia de Estilos

```
1. Design Tokens (--color-cyber-primary)
   ↓
2. Base/Reset CSS (reset.css, global.css)
   ↓
3. Themes (cyber.css, osint.css)
   ↓
4. Component Modules (Button.module.css)
   ↓
5. Inline styles (APENAS quando absolutamente necessário)
```

### Usando CSS Modules

```jsx
// ✅ BOM
import styles from './Component.module.css';

<div className={styles.container}>
  <h1 className={styles.title}>Title</h1>
  <p className={styles.description}>Text</p>
</div>
```

```css
/* Component.module.css */
.container {
  padding: var(--space-5);
  background: var(--bg-secondary);
}

.title {
  font-size: var(--text-2xl);
  color: var(--color-cyber-primary);
}

.description {
  font-size: var(--text-base);
  color: var(--text-secondary);
}
```

### Combinando Classes

```jsx
// ✅ BOM - Usando template literals
const buttonClasses = [
  styles.button,
  styles[variant],
  styles[size],
  loading && styles.loading,
  className
].filter(Boolean).join(' ');

<button className={buttonClasses}>Click</button>

// ✅ BOM - Inline simples
<div className={`${styles.card} ${styles.hoverable}`}>

// ❌ RUIM - Strings concatenadas confusas
<div className={styles.card + ' ' + styles.hoverable + ' ' + (active ? styles.active : '')}>
```

### Responsividade

```css
/* Mobile First Approach */
.container {
  /* Mobile styles (default) */
  padding: var(--space-3);
  grid-template-columns: 1fr;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    padding: var(--space-5);
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .container {
    padding: var(--space-6);
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### Animações

```css
/* Use tokens para duração */
.fadeIn {
  animation: fadeIn var(--duration-base) var(--ease-out);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Transições suaves */
.button {
  transition: all var(--duration-base) var(--ease-out);
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 20px var(--color-cyber-primary);
}
```

### Estados Interativos

```css
/* Sempre defina todos os estados */
.button {
  /* Default */
  background: var(--color-cyber-primary);
  cursor: pointer;
  transition: all var(--duration-base);
}

.button:hover {
  /* Hover */
  background: var(--color-cyber-secondary);
  transform: translateY(-2px);
}

.button:active {
  /* Click */
  transform: translateY(0);
}

.button:focus-visible {
  /* Teclado navigation */
  outline: 2px solid var(--color-cyber-primary);
  outline-offset: 2px;
}

.button:disabled {
  /* Disabled */
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

---

## 🪝 HOOKS CUSTOMIZADOS

### Hooks Disponíveis

#### 1. `useApi` - Gerenciamento de chamadas API
```jsx
import { useApi } from '../hooks';

const { data, loading, error, execute, reset } = useApi(searchExploits);

// Executar
const handleSearch = async () => {
  try {
    const result = await execute('CVE-2024-1234');
    console.log(result);
  } catch (err) {
    console.error(err);
  }
};

// Reset
reset();
```

#### 2. `useDebounce` - Debounce de valores
```jsx
import { useDebounce } from '../hooks';

const [searchTerm, setSearchTerm] = useState('');
const debouncedSearchTerm = useDebounce(searchTerm, 500);

useEffect(() => {
  if (debouncedSearchTerm) {
    performSearch(debouncedSearchTerm);
  }
}, [debouncedSearchTerm]);
```

#### 3. `useLocalStorage` - Persistência local
```jsx
import { useLocalStorage } from '../hooks';

const [user, setUser, removeUser] = useLocalStorage('user', null);

// Salvar
setUser({ name: 'John', role: 'admin' });

// Remover
removeUser();
```

#### 4. `useKeyPress` - Detecção de teclas
```jsx
import { useKeyPress } from '../hooks';

const escapePressed = useKeyPress('Escape');
const enterPressed = useKeyPress('Enter');

useEffect(() => {
  if (escapePressed) {
    closeModal();
  }
}, [escapePressed]);
```

### Criando Novos Hooks

**Regras:**
1. Nome deve começar com `use`
2. Deve usar hooks do React internamente
3. Deve ser reutilizável
4. Deve ter documentação JSDoc

**Template:**
```jsx
import { useState, useEffect, useCallback } from 'react';

/**
 * Hook description
 *
 * @param {Type} param1 - Description
 * @param {Type} param2 - Description
 * @returns {Object} - Return value description
 *
 * @example
 * const { value, action } = useCustomHook(param);
 */
export const useCustomHook = (param1, param2 = defaultValue) => {
  const [state, setState] = useState(initialValue);

  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const action = useCallback(() => {
    // Action logic
  }, [dependencies]);

  return {
    state,
    action
  };
};

export default useCustomHook;
```

---

## 🧪 TESTES

### Estrutura de Testes

```
Component/
├── Component.jsx
├── Component.module.css
└── __tests__/
    ├── Component.test.jsx
    ├── useComponent.test.js
    └── integration.test.jsx
```

### Teste de Componente

```jsx
// Button.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders children correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    fireEvent.click(screen.getByText('Click'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when loading', () => {
    render(<Button loading>Click</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies variant styles', () => {
    const { container } = render(<Button variant="primary">Click</Button>);
    expect(container.firstChild).toHaveClass('primary');
  });
});
```

### Teste de Hook

```jsx
// useApi.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { useApi } from './useApi';

const mockApiFunction = jest.fn();

describe('useApi', () => {
  it('initializes with null data', () => {
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets loading state during execution', async () => {
    mockApiFunction.mockResolvedValue({ data: 'test' });
    const { result } = renderHook(() => useApi(mockApiFunction));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);
  });

  it('sets data on successful execution', async () => {
    const mockData = { data: 'test' };
    mockApiFunction.mockResolvedValue(mockData);

    const { result, waitForNextUpdate } = renderHook(() => useApi(mockApiFunction));

    act(() => {
      result.current.execute();
    });

    await waitForNextUpdate();

    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
```

### Cobertura Mínima

- **Componentes Shared**: 80%+ coverage
- **Hooks**: 90%+ coverage
- **Widgets**: 60%+ coverage
- **Utils**: 100% coverage

---

## 🔧 TROUBLESHOOTING

### Problemas Comuns

#### 1. CSS Modules não funcionando

**Sintoma:** Classes não aplicadas, estilos não aparecem

**Solução:**
```jsx
// ❌ ERRADO
import styles from './Component.css';

// ✅ CORRETO
import styles from './Component.module.css';
```

#### 2. Design tokens não funcionam

**Sintoma:** `var(--color-cyber-primary)` não resolve

**Solução:**
```css
/* Importe os tokens no topo do CSS Module */
@import '../../../styles/tokens/colors.css';
@import '../../../styles/tokens/spacing.css';
@import '../../../styles/tokens/typography.css';
```

#### 3. Re-renders infinitos

**Sintoma:** Componente renderiza continuamente

**Solução:**
```jsx
// ❌ ERRADO - Cria nova função a cada render
<button onClick={() => handleClick()} />

// ✅ CORRETO - useCallback
const handleClick = useCallback(() => {
  // logic
}, [dependencies]);

<button onClick={handleClick} />
```

#### 4. Estado não atualiza

**Sintoma:** `setState` não reflete mudanças

**Solução:**
```jsx
// ❌ ERRADO - Mutação direta
state.push(item);
setState(state);

// ✅ CORRETO - Novo array
setState([...state, item]);

// ✅ CORRETO - Functional update
setState(prev => [...prev, item]);
```

#### 5. Memory leaks

**Sintoma:** Warnings de "Can't perform a React state update on unmounted component"

**Solução:**
```jsx
useEffect(() => {
  let isMounted = true;

  async function fetchData() {
    const data = await api.fetch();
    if (isMounted) {
      setData(data);
    }
  }

  fetchData();

  return () => {
    isMounted = false;
  };
}, []);
```

---

## 📘 BLUEPRINT PARA NOVAS FEATURES

### Checklist Completo

Quando implementar uma nova feature, siga este checklist:

#### 1. Planejamento
- [ ] Entendi completamente o requisito?
- [ ] A feature se encaixa em qual módulo? (Cyber/OSINT/Analytics)
- [ ] Posso reutilizar componentes shared existentes?
- [ ] Preciso criar novos componentes shared?
- [ ] Qual variante usar? (cyber/osint/analytics)

#### 2. Estrutura
- [ ] Criar pasta do componente em `components/<modulo>/<Feature>`
- [ ] Criar subpasta `components/` para subcomponentes
- [ ] Criar subpasta `hooks/` para lógica de negócio
- [ ] Criar arquivo `index.js` para exports

#### 3. Implementação
- [ ] Componente principal usa Card ou componente shared adequado
- [ ] Lógica isolada em hook customizado
- [ ] CSS em módulos separados (zero inline styles)
- [ ] Usa design tokens (zero hardcode)
- [ ] Props com defaults e destructuring
- [ ] JSDoc documentation

#### 4. Estilo
- [ ] Importa tokens necessários
- [ ] Usa variáveis CSS
- [ ] Responsive (mobile-first)
- [ ] Estados interativos (hover, active, focus, disabled)
- [ ] Animações suaves

#### 5. Qualidade
- [ ] Componente < 200 linhas
- [ ] Sem warnings no console
- [ ] Acessibilidade básica (labels, aria-*)
- [ ] Performance (useMemo, useCallback quando necessário)
- [ ] Testes básicos

#### 6. Integração
- [ ] Export no index.js do módulo
- [ ] Importado no dashboard correspondente
- [ ] Testado em desenvolvimento
- [ ] Documentado no README se necessário

### Template de Nova Feature

```jsx
// 1. Criar estrutura
frontend/src/components/<modulo>/<FeatureName>/
├── <FeatureName>.jsx
├── <FeatureName>.module.css
├── components/
│   ├── Subcomponent1.jsx
│   ├── Subcomponent1.module.css
│   ├── Subcomponent2.jsx
│   └── Subcomponent2.module.css
├── hooks/
│   └── use<FeatureName>.js
└── index.js

// 2. Componente Principal
/**
 * FeatureName - Descrição breve
 *
 * Descrição detalhada da feature, quando usar, etc.
 */

import React from 'react';
import { Card } from '../../shared';
import { Subcomponent1 } from './components/Subcomponent1';
import { Subcomponent2 } from './components/Subcomponent2';
import { useFeatureName } from './hooks/useFeatureName';
import styles from './FeatureName.module.css';

export const FeatureName = ({ variant = 'cyber', ...props }) => {
  const { data, loading, error, action } = useFeatureName();

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return (
    <Card
      title="FEATURE TITLE"
      badge="BADGE"
      variant={variant}
      className={styles.widget}
    >
      <div className={styles.container}>
        <Subcomponent1 data={data} onAction={action} />
        <Subcomponent2 data={data} />
      </div>
    </Card>
  );
};

export default FeatureName;

// 3. Hook
import { useState, useCallback } from 'react';

export const useFeatureName = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const action = useCallback(async () => {
    setLoading(true);
    try {
      // Logic here
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, action };
};

// 4. CSS Module
@import '../../../styles/tokens/colors.css';
@import '../../../styles/tokens/spacing.css';
@import '../../../styles/tokens/typography.css';

.widget {
  width: 100%;
  max-width: var(--widget-max-width);
}

.container {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

// 5. Export
export { FeatureName } from './FeatureName';
export default FeatureName;
```

---

## 🔄 MANUTENÇÃO E EVOLUÇÃO

### Atualizando Componentes Existentes

#### Antes de Modificar
1. **Entenda o impacto**: Onde este componente é usado?
2. **Verifique testes**: Há testes que quebrarão?
3. **Considere breaking changes**: A mudança é retrocompatível?
4. **Documente**: Atualize JSDoc e README se necessário

#### Modificação Segura
```jsx
// ✅ BOM - Adicionar nova prop com default
const Button = ({
  children,
  variant = 'primary',
  newProp = defaultValue,  // Nova prop não quebra código existente
  ...props
}) => { };

// ❌ RUIM - Remover/renomear prop existente
const Button = ({
  children,
  type,  // Era "variant" - BREAKING CHANGE!
  ...props
}) => { };
```

### Refatoração Segura

**Processo:**
1. Criar nova versão em paralelo
2. Migrar componentes um por um
3. Deprecar versão antiga (com aviso)
4. Remover após confirmação

```jsx
// Old component
export const OldComponent = (props) => {
  console.warn('OldComponent is deprecated. Use NewComponent instead.');
  return <NewComponent {...props} />;
};
```

### Adicionando ao Design System

**Quando adicionar novo token:**
```css
/* 1. Adicione em styles/tokens/<categoria>.css */
:root {
  --new-color: #value;
}

/* 2. Documente no FRONTEND_MANIFESTO.md */
/* 3. Use em pelo menos 2 lugares antes de adicionar */
```

**Quando criar novo componente shared:**
1. Usado em 3+ lugares
2. Tem testes completos
3. Documentação JSDoc
4. Aprovado em code review

### Versionamento de Componentes

```
components/shared/Button/
├── Button.jsx           # v3 (current)
├── Button.v2.jsx        # deprecated
├── Button.v1.jsx        # legacy (to be removed)
└── CHANGELOG.md         # Histórico de mudanças
```

### Code Review Checklist

Ao revisar PR de frontend:

**Código:**
- [ ] Componente < 200 linhas
- [ ] CSS em módulos (zero hardcode)
- [ ] Usa design tokens
- [ ] Props com destructuring e defaults
- [ ] Hooks customizados para lógica
- [ ] Sem warnings no console

**Estilo:**
- [ ] Segue nomenclatura padrão
- [ ] Responsivo
- [ ] Acessibilidade básica
- [ ] Animações suaves

**Qualidade:**
- [ ] Testes passando
- [ ] Sem duplicação de código
- [ ] Performance adequada
- [ ] Documentação atualizada

---

## 🎓 ONBOARDING RÁPIDO

### Para Novos Desenvolvedores

#### Dia 1: Setup e Conceitos
1. Clone o repositório
2. `npm install`
3. `npm run dev`
4. Leia este manifesto (sim, tudo!)
5. Explore `/components/shared`
6. Rode os testes: `npm test`

#### Dia 2-3: Primeiro Componente
1. Escolha um componente simples para refatorar
2. Siga o template de "Nova Feature"
3. Use ExploitSearchWidget como referência
4. Faça PR pequeno e peça review

#### Semana 1: Dominando o Design System
1. Crie 3+ componentes usando shared components
2. Experimente todos os variants (cyber/osint/analytics)
3. Crie 1 hook customizado
4. Escreva testes para seus componentes

#### Semana 2+: Contribuindo
1. Refatore 1 componente grande
2. Adicione feature nova
3. Melhore documentação
4. Ajude outros desenvolvedores

### Recursos de Aprendizado

**Documentação Oficial:**
- React: https://react.dev
- Vite: https://vitejs.dev
- CSS Modules: https://github.com/css-modules/css-modules

**Exemplos no Código:**
- Melhor exemplo: `/components/cyber/ExploitSearchWidget`
- Componentes shared: `/components/shared`
- Hooks: `/hooks`

---

## 📊 MÉTRICAS E MONITORAMENTO

### Performance Benchmarks

```yaml
Carregamento Inicial: < 2s
Time to Interactive: < 2.5s
Tamanho do Bundle: < 500KB (gzipped)
Lighthouse Score: > 90

Por Componente:
  Render Time: < 16ms (60fps)
  Re-renders: Mínimo necessário
  Memory Usage: < 50MB por dashboard
```

### Auditoria de Qualidade

Execute periodicamente:
```bash
# Bundle size
npm run build
npx vite-bundle-visualizer

# Lint
npm run lint

# Tests + coverage
npm run test:coverage

# Performance
npx lighthouse http://localhost:5173
```

### Red Flags

**🚨 Problemas Críticos:**
- Componente > 500 linhas
- CSS inline/hardcoded
- Re-renders infinitos
- Memory leaks
- Bundle > 1MB

**⚠️ Problemas Médios:**
- Componente > 200 linhas
- Código duplicado
- Falta de testes
- Props drilling > 3 níveis

---

## 🎯 CONCLUSÃO

### Princípios Fundamentais (TL;DR)

1. **Componentes Pequenos**: < 200 linhas
2. **Separação de Responsabilidades**: JSX + CSS + Lógica separados
3. **Design Tokens**: Zero hardcode
4. **Reutilização**: Shared components first
5. **Performance**: useMemo, useCallback, code splitting
6. **Qualidade**: Testes, documentação, code review

### Manutenção Contínua

**Diariamente:**
- Code reviews
- Corrigir warnings
- Atualizar testes

**Semanalmente:**
- Refatorar 1 componente grande
- Auditar bundle size
- Melhorar documentação

**Mensalmente:**
- Atualizar dependências
- Performance audit
- Review design system

### Contato e Suporte

**Problemas?**
1. Verifique este manifesto
2. Explore código de referência (ExploitSearchWidget)
3. Pergunte no canal da equipe
4. Crie issue no repositório

---

## 📚 APÊNDICES

### A. Glossário

**CSS Modules**: CSS com escopo local ao componente
**Design Tokens**: Variáveis CSS centralizadas (cores, espaçamentos, etc)
**Hook Customizado**: Função que usa hooks do React para lógica reutilizável
**Props Drilling**: Passar props por múltiplos níveis de componentes
**Memoization**: Cache de valores computados (useMemo, useCallback)

### B. Atalhos e Snippets

```jsx
// rfc - React Functional Component
import React from 'react';

export const ComponentName = () => {
  return (
    <div>ComponentName</div>
  );
};

// hook - Custom Hook
import { useState, useCallback } from 'react';

export const useCustomHook = () => {
  const [state, setState] = useState(null);

  const action = useCallback(() => {
    // logic
  }, []);

  return { state, action };
};
```

### C. Design Tokens Completo

Ver arquivos:
- `/styles/tokens/colors.css`
- `/styles/tokens/spacing.css`
- `/styles/tokens/typography.css`

### D. Changelog

**v1.0 (2025-09-30)**
- ✅ Design System completo
- ✅ Componentes shared (Button, Input, Card)
- ✅ Hooks customizados
- ✅ ExploitSearchWidget refatorado
- ✅ Documentação completa

**Próximos Passos:**
- Refatorar todos os dashboards
- Refatorar widgets grandes (MapPanel, TerminalEmulator, etc)
- Adicionar mais componentes shared
- Implementar testes E2E

---

**Última atualização:** 2025-09-30
**Versão:** 1.0
**Mantido por:** Equipe Vértice Frontend

---

> 🎯 **"Um frontend bem arquitetado é como uma operação OSINT bem planejada: organizado, eficiente e escalável."**

**BEM-VINDO À SELVA. AGORA VOCÊ TEM O MAPA.** 🗺️
