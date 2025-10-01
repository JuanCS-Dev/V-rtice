# 🎯 FRONTEND VÉRTICE

> **Sistema de Interface Cyberpunk para Operações OSINT, Cyber Security e Analytics**

[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite)](https://vitejs.dev)
[![CSS Modules](https://img.shields.io/badge/CSS-Modules-000000?logo=css3)](https://github.com/css-modules/css-modules)
[![Status](https://img.shields.io/badge/Refatoração-58%25-green)](#)

---

## 📚 DOCUMENTAÇÃO COMPLETA

### 🏗️ Para Desenvolvedores

| Documento | Descrição | Status |
|-----------|-----------|--------|
| [**FRONTEND_MANIFESTO.md**](./FRONTEND_MANIFESTO.md) | 📘 **Guia Completo** - Arquitetura, padrões, design system, blueprint | ✅ Completo |
| [**DEBUGGING_GUIDE.md**](./DEBUGGING_GUIDE.md) | 🔍 **Troubleshooting** - React, CSS, Performance, API | ✅ Completo |
| [**REFACTORING_PLAN.md**](./REFACTORING_PLAN.md) | 🗺️ **Plano de Refatoração** - Roadmap detalhado | ✅ Completo |
| [**REFACTORING_STATUS.md**](./REFACTORING_STATUS.md) | 📊 **Status Atual** - Progresso, métricas, próximos passos | ✅ Atualizado |

### 🎓 Início Rápido

```bash
# 1. Leia PRIMEIRO (obrigatório para todos):
cat FRONTEND_MANIFESTO.md

# 2. Se for debugar algo:
cat DEBUGGING_GUIDE.md

# 3. Se for refatorar:
cat REFACTORING_PLAN.md

# 4. Para ver status da refatoração:
cat REFACTORING_STATUS.md
```

---

## 🚀 SETUP E DESENVOLVIMENTO

### Pré-requisitos

```bash
Node.js >= 18
npm >= 9
```

### Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd vertice-dev/frontend

# Instale dependências
npm install

# Inicie o servidor de desenvolvimento
npm run dev
```

### Scripts Disponíveis

```bash
npm run dev          # Servidor desenvolvimento (http://localhost:5173)
npm run build        # Build para produção
npm run preview      # Preview do build
npm run lint         # Verificar problemas de código
npm run lint:fix     # Corrigir automaticamente
npm run test         # Rodar testes (quando implementado)
```

---

## 🏗️ ARQUITETURA

### Estrutura de Diretórios

```
frontend/src/
├── components/
│   ├── shared/              ⭐ Componentes reutilizáveis (Button, Input, Card)
│   ├── cyber/               🔵 Módulo Cyber Security
│   ├── osint/               🟣 Módulo OSINT
│   ├── analytics/           🔷 Módulo Analytics
│   ├── terminal/            💻 Terminal/CLI
│   └── admin/               ⚙️ Administração
│
├── hooks/                   🪝 Custom hooks compartilhados
│   ├── useApi.js
│   ├── useDebounce.js
│   ├── useLocalStorage.js
│   └── useKeyPress.js
│
├── api/                     🌐 Camada de API
│   ├── worldClassTools.js
│   ├── sinesp.js
│   └── config.js
│
├── styles/                  🎨 Design System
│   ├── tokens/              Design Tokens (cores, espaçamento, tipografia)
│   ├── themes/              Temas específicos (cyber, osint, analytics)
│   ├── base/                Reset, global, utilities
│   └── mixins/              Animações
│
├── utils/                   🔧 Utilitários
├── App.jsx                  📱 Componente raiz
└── main.jsx                 🚪 Entry point
```

### Design System

```css
/* 🎨 Paleta de Cores */
--color-cyber-primary: #00ffff      /* Cyber (Cyan) */
--color-osint-primary: #a855f7      /* OSINT (Purple) */
--color-analytics-primary: #3b82f6  /* Analytics (Blue) */

/* 📏 Espaçamento */
--space-1: 4px   --space-4: 16px   --space-8: 48px
--space-2: 8px   --space-5: 24px   --space-10: 64px
--space-3: 12px  --space-6: 32px

/* 📝 Tipografia */
--text-xs: 12px    --text-lg: 18px    --text-3xl: 30px
--text-sm: 14px    --text-xl: 20px
--text-base: 16px  --text-2xl: 24px
```

### Componentes Shared Disponíveis

```jsx
import { Button, Input, Card } from './components/shared';

// Button - 9 variantes, 5 tamanhos
<Button variant="primary" size="md" loading={false}>
  Click Me
</Button>

// Input - 4 variantes, validação, icons
<Input
  variant="cyber"
  placeholder="Digite..."
  icon={<i className="fas fa-search" />}
  error="Mensagem de erro"
/>

// Card - 9 variantes, customizável
<Card
  title="TÍTULO"
  badge="BADGE"
  variant="cyber"
  padding="md"
>
  Conteúdo
</Card>
```

### Hooks Disponíveis

```jsx
import { useApi, useDebounce, useLocalStorage, useKeyPress } from './hooks';

// useApi - Gerenciamento de API calls
const { data, loading, error, execute } = useApi(apiFunction);

// useDebounce - Debounce de valores
const debouncedValue = useDebounce(searchTerm, 500);

// useLocalStorage - Persistência local
const [user, setUser, removeUser] = useLocalStorage('user', null);

// useKeyPress - Detecção de teclas
const escapePressed = useKeyPress('Escape');
```

---

## 📊 STATUS DA REFATORAÇÃO

### Progresso Geral

```
████████████████████░░░░░░░░░░░░░ 58% Completo

FASE 1: Fundação                    ✅ 100% COMPLETO
FASE 2: Refatoração de Referência   ✅ 100% COMPLETO
FASE 3: Refatoração em Massa        🟡 75% EM PROGRESSO
FASE 4: Grandes Componentes         🔲 0% PENDENTE
FASE 5: Polimento                   🔲 0% PENDENTE
```

### O Que Foi Feito ✅

- ✅ **Design System Completo** (tokens, spacing, typography, animations)
- ✅ **7 Componentes Shared** (Button, Input, Card, Badge, Alert, LoadingSpinner, Modal)
- ✅ **4 Custom Hooks** (useApi, useDebounce, useLocalStorage, useKeyPress)
- ✅ **9 Widgets Refatorados** (~1.755 linhas eliminadas, 85% redução média):
  - ExploitSearchWidget (645 → 80 linhas, 88% redução)
  - SocialMediaWidget (760 → 120 linhas, 84% redução)
  - BreachDataWidget (762 → 120 linhas, 84% redução)
  - ThreatMap (621 → 150 linhas, 76% redução)
  - NetworkMonitor (271 → 50 linhas, 81% redução)
  - IpIntelligence (412 → 65 linhas, 84% redução)
  - VulnerabilityScanner (368 → 60 linhas, 84% redução)
  - DomainAnalyzer (278 → 48 linhas, 83% redução)
  - NmapScanner (426 → 45 linhas, 89% redução)
- ✅ **Documentação Completa** (4 documentos, ~3500 linhas)

### O Que Falta 🔲

- 🔲 **27 Componentes** para refatorar (9 concluídos!)
- 🔲 **MapPanel** (1070 linhas) - Componente mais complexo
- 🔲 **TerminalEmulator** (928 linhas)
- 🔲 **15+ Widgets OSINT/Analytics** restantes
- 🔲 **Testes Automatizados**
- 🔲 **Storybook** para componentes

👉 **Ver detalhes completos:** [REFACTORING_STATUS.md](./REFACTORING_STATUS.md)

---

## 🎯 PADRÕES E BOAS PRÁTICAS

### ✅ SEMPRE Faça

```jsx
// ✅ Use componentes shared
import { Button, Input, Card } from './components/shared';

// ✅ Use design tokens (nunca hardcode)
.container {
  background: var(--bg-secondary);
  padding: var(--space-5);
  color: var(--color-cyber-primary);
}

// ✅ CSS Modules (nunca inline)
import styles from './Component.module.css';

// ✅ Hooks customizados para lógica
const { data, loading } = useCustomHook();

// ✅ Componentes < 200 linhas
// ✅ Props com defaults e destructuring
const Component = ({ prop1, prop2 = 'default', ...props }) => { };
```

### ❌ NUNCA Faça

```jsx
// ❌ CSS inline/hardcoded
<div style={{ background: '#0a0a0a', padding: '20px' }}>

// ❌ Cores/espaçamentos hardcoded
.container {
  background: #0a0a0a;
  padding: 20px;
  color: #00ffff;
}

// ❌ Componentes gigantes (> 500 linhas)
// ❌ Lógica misturada com UI
// ❌ Código duplicado
// ❌ Props sem defaults
```

### 📘 Exemplo de Componente Ideal

```jsx
/**
 * ComponentName - Descrição breve
 */
import React from 'react';
import { Card, Button } from '../../shared';
import { useCustomHook } from './hooks/useCustomHook';
import styles from './ComponentName.module.css';

export const ComponentName = ({ variant = 'cyber', ...props }) => {
  const { data, loading, action } = useCustomHook();

  if (loading) return <LoadingSpinner />;
  if (!data) return null;

  return (
    <Card title="TÍTULO" variant={variant} className={styles.widget}>
      <div className={styles.container}>
        <p className={styles.text}>{data.message}</p>
        <Button variant="primary" onClick={action}>
          Action
        </Button>
      </div>
    </Card>
  );
};

export default ComponentName;
```

---

## 🔍 DEBUGGING

### Ferramentas Essenciais

- **React DevTools** - Chrome/Firefox extension
- **Vite DevServer** - HMR + error overlay
- **Browser DevTools** - Console, Network, Performance

### Problemas Comuns

```jsx
// ❌ Props não chegam
console.log('Props recebidas:', props);

// ❌ Estado não atualiza
useEffect(() => {
  console.log('Estado mudou:', state);
}, [state]);

// ❌ Re-renders infinitos
const callback = useCallback(() => { }, []);  // Use useCallback

// ❌ CSS não aplica
import styles from './Component.module.css';  // .module.css!
console.log('CSS Module:', styles);
```

👉 **Ver guia completo:** [DEBUGGING_GUIDE.md](./DEBUGGING_GUIDE.md)

---

## 🧪 TESTES (Em Desenvolvimento)

```bash
# Rodar testes
npm run test

# Cobertura
npm run test:coverage

# Watch mode
npm run test:watch
```

**Meta de Cobertura:**
- Componentes Shared: 80%+
- Hooks: 90%+
- Utils: 100%

---

## 📦 BUILD E DEPLOY

### Build de Produção

```bash
# Build
npm run build

# Preview local
npm run preview

# Analisar bundle
npx vite-bundle-visualizer
```

### Métricas de Performance

```yaml
Bundle Size: < 500KB (gzipped)
Time to Interactive: < 2s
Lighthouse Score: > 90
First Contentful Paint: < 1.5s
```

---

## 🎓 ONBOARDING

### Para Novos Desenvolvedores

**Dia 1:**
1. ✅ Setup do projeto (`npm install`, `npm run dev`)
2. ✅ Ler [FRONTEND_MANIFESTO.md](./FRONTEND_MANIFESTO.md) (obrigatório!)
3. ✅ Explorar `/components/shared`
4. ✅ Ver código de referência: `ExploitSearchWidget`

**Semana 1:**
1. ✅ Criar componente simples usando shared components
2. ✅ Usar todos os design tokens
3. ✅ Criar 1 hook customizado
4. ✅ Fazer PR pequeno e pedir review

**Semana 2+:**
1. ✅ Refatorar 1 componente existente
2. ✅ Adicionar feature nova
3. ✅ Contribuir com documentação

---

## 🤝 CONTRIBUINDO

### Code Review Checklist

Antes de fazer PR:

- [ ] Componente < 200 linhas
- [ ] 100% CSS Modules (zero inline)
- [ ] 100% design tokens (zero hardcode)
- [ ] Props com defaults e destructuring
- [ ] Lógica em hooks customizados
- [ ] Sem warnings no console
- [ ] Segue padrão do ExploitSearchWidget
- [ ] Documentação JSDoc
- [ ] Testes (quando implementado)

### Estrutura de PR

```markdown
## Descrição
Breve descrição da mudança

## Tipo
- [ ] Nova feature
- [ ] Refatoração
- [ ] Bug fix
- [ ] Documentação

## Checklist
- [ ] Segue FRONTEND_MANIFESTO.md
- [ ] Usa componentes shared
- [ ] CSS Modules + design tokens
- [ ] Componente < 200 linhas
- [ ] Sem warnings
```

---

## 📞 SUPORTE E RECURSOS

### Documentação Interna

- 📘 [FRONTEND_MANIFESTO.md](./FRONTEND_MANIFESTO.md) - **LEIA PRIMEIRO**
- 🔍 [DEBUGGING_GUIDE.md](./DEBUGGING_GUIDE.md) - Troubleshooting
- 🗺️ [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) - Plano de refatoração
- 📊 [REFACTORING_STATUS.md](./REFACTORING_STATUS.md) - Status atual

### Código de Referência

- 🌟 `/components/cyber/ExploitSearchWidget/` - **Exemplo perfeito**
- 🧩 `/components/shared/` - Componentes base
- 🪝 `/hooks/` - Hooks reutilizáveis
- 🎨 `/styles/tokens/` - Design system

### Links Úteis

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [CSS Modules](https://github.com/css-modules/css-modules)
- [Leaflet (Maps)](https://leafletjs.com)

---

## 📄 LICENÇA

Copyright © 2025 Projeto Vértice

---

## 🎯 DEFINIÇÃO DE SUCESSO

A refatoração estará completa quando:

- ✅ 100% CSS Modules (zero inline)
- ✅ 100% design tokens (zero hardcode)
- ✅ Todos componentes < 200 linhas
- ✅ 15+ componentes shared
- ✅ 80%+ code coverage
- ✅ Bundle < 500KB
- ✅ Lighthouse > 90
- ✅ Zero warnings

---

> 🎯 **"Um frontend bem arquitetado é como uma operação OSINT bem planejada: organizado, eficiente e escalável."**

**BEM-VINDO À SELVA. AGORA VOCÊ TEM O MAPA.** 🗺️

---

**Status:** 🟢 EM PROGRESSO ACELERADO (58% completo - 9 widgets refatorados!)
**Última Atualização:** 2025-09-30
**Mantido por:** Equipe Frontend Vértice
