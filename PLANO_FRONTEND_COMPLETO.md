# 🎯 PLANO COMPLETO DE IMPLEMENTAÇÃO - FRONTEND VÉRTICE DO ZERO

**Data**: 2025-11-15
**Versão**: 1.0
**Status**: Ready to Implement
**Estilo**: Claude.ai (Clean, Sóbrio, Minimalista)

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Design System](#design-system)
3. [Stack Tecnológica](#stack-tecnológica)
4. [Arquitetura Frontend](#arquitetura-frontend)
5. [Mapeamento Backend → Frontend](#mapeamento-backend-frontend)
6. [Estrutura de Páginas](#estrutura-de-páginas)
7. [Componentes Principais](#componentes-principais)
8. [Plano de Implementação por Fases](#plano-de-implementação)
9. [Checklist de Features](#checklist-de-features)

---

## <a name="visão-geral"></a>1. VISÃO GERAL

### Objetivo
Construir um frontend **DO ZERO** que:
- ✅ Seja **CLEAN, SÓBRIO e MINIMALISTA** como Claude.ai
- ✅ Utilize **VERDE** (#10b981) como cor de acento principal
- ✅ Represente **TODAS** as funcionalidades do backend (250+ endpoints, 100+ serviços)
- ✅ Mantenha a lógica de conexão atual (React Query, WebSockets, etc)
- ✅ Tenha animações **SUTIS e SMOOTH**

### Princípios de Design
1. **Minimalismo** - Cada pixel tem um propósito
2. **Clareza** - Informação apresentada de forma limpa
3. **Performance** - Rápido, responsivo, otimizado
4. **Acessibilidade** - WCAG 2.1 AA compliance
5. **Consistência** - Design system rigoroso

---

## <a name="design-system"></a>2. DESIGN SYSTEM

### 2.1 Paleta de Cores

```css
/* MODO CLARO (Primary) */
--background: #FDFDF7;              /* Off-white warm */
--foreground: #0E0E0E;              /* Nearly black */

--primary: #10b981;                 /* Verde Emerald-500 */
--primary-hover: #059669;           /* Verde Emerald-600 */
--primary-active: #047857;          /* Verde Emerald-700 */

--card: #FFFFFF;                    /* Pure white cards */
--card-border: #E5E7EB;             /* Subtle gray border */

--text-primary: #0E0E0E;            /* Main text */
--text-secondary: #6B7280;          /* Secondary text */
--text-muted: #9CA3AF;              /* Muted text */

--success: #10b981;                 /* Verde */
--warning: #F59E0B;                 /* Amber */
--danger: #EF4444;                  /* Red */
--info: #3B82F6;                    /* Blue */
```

```css
/* MODO ESCURO */
--background: #09090B;              /* Deep black */
--foreground: #E5E7EB;              /* Light gray */

--primary: #34D399;                 /* Verde Emerald-400 (mais claro) */
--primary-hover: #10b981;           /* Verde Emerald-500 */

--card: #18181B;                    /* Dark card */
--card-border: #27272A;             /* Dark border */

--text-primary: #F9FAFB;            /* Light text */
--text-secondary: #9CA3AF;          /* Gray text */
--text-muted: #6B7280;              /* Darker muted */
```

### 2.2 Tipografia

```css
/* Font Families */
--font-serif: ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
--font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: ui-monospace, "Cascadia Code", "Source Code Pro", Menlo, Consolas, monospace;

/* Uso Principal */
--font-primary: var(--font-sans);   /* UI = Sans-serif */
--font-display: var(--font-sans);   /* Headings = Sans-serif */
--font-code: var(--font-mono);      /* Code = Monospace */

/* Tamanhos - Modular Scale */
--text-xs: 0.75rem;      /* 12px - badges, captions */
--text-sm: 0.875rem;     /* 14px - small body */
--text-base: 1rem;       /* 16px - body text */
--text-lg: 1.125rem;     /* 18px - large body */
--text-xl: 1.25rem;      /* 20px - subtitle */
--text-2xl: 1.5rem;      /* 24px - h3 */
--text-3xl: 1.875rem;    /* 30px - h2 */
--text-4xl: 2.25rem;     /* 36px - h1 */
--text-5xl: 3rem;        /* 48px - hero */

/* Pesos */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 2.3 Espaçamento

```css
/* Fibonacci-inspired spacing */
--space-xs: 0.25rem;     /* 4px */
--space-sm: 0.5rem;      /* 8px */
--space-md: 1rem;        /* 16px */
--space-lg: 1.5rem;      /* 24px */
--space-xl: 2.5rem;      /* 40px */
--space-2xl: 4rem;       /* 64px */
--space-3xl: 6.5rem;     /* 104px */
```

### 2.4 Border Radius

```css
--radius-sm: 0.25rem;    /* 4px - small elements */
--radius-md: 0.5rem;     /* 8px - cards, buttons */
--radius-lg: 0.75rem;    /* 12px - large cards */
--radius-full: 9999px;   /* Circular */
```

### 2.5 Shadows

```css
/* Sutis, elegantes */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* Verde glow (sutil) */
--shadow-glow-green: 0 0 20px rgba(16, 185, 129, 0.2);
```

### 2.6 Animações

```css
/* Transições sutis */
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

/* Keyframes principais */
@keyframes fadeIn { /* opacity 0 → 1 */ }
@keyframes slideUp { /* translateY(8px) → 0 */ }
@keyframes scaleIn { /* scale(0.95) → 1 */ }
@keyframes shimmer { /* loading skeleton */ }
```

---

## <a name="stack-tecnológica"></a>3. STACK TECNOLÓGICA

### 3.1 Core
```json
{
  "framework": "React 18",
  "build": "Vite",
  "language": "TypeScript",
  "routing": "React Router v6"
}
```

### 3.2 Estilo
```json
{
  "styling": "Tailwind CSS v4 (ou CSS Modules)",
  "design-system": "Radix UI Primitives (headless)",
  "icons": "Lucide React",
  "animations": "CSS Animations + Framer Motion (seletivo)"
}
```

### 3.3 Estado & Dados
```json
{
  "server-state": "TanStack Query (React Query v5)",
  "client-state": "Zustand",
  "forms": "React Hook Form + Zod",
  "websockets": "Custom WebSocket Manager (já existe)"
}
```

### 3.4 HTTP & Auth
```json
{
  "http": "openapi-fetch (type-safe)",
  "auth": "OAuth2 + JWT",
  "storage": "SecureTokenStore (já existe)"
}
```

### 3.5 Qualidade
```json
{
  "linting": "ESLint + Prettier",
  "testing": "Vitest + Testing Library",
  "types": "TypeScript Strict Mode",
  "a11y": "axe-core + eslint-plugin-jsx-a11y"
}
```

---

## <a name="arquitetura-frontend"></a>4. ARQUITETURA FRONTEND

### 4.1 Estrutura de Diretórios (DO ZERO)

```
frontend-novo/
├── public/
│   └── assets/
├── src/
│   ├── app/                          # App root
│   │   ├── App.tsx
│   │   ├── Router.tsx
│   │   └── providers/                # Context providers
│   │       ├── AuthProvider.tsx
│   │       ├── ThemeProvider.tsx
│   │       └── QueryProvider.tsx
│   │
│   ├── pages/                        # Pages (uma por rota)
│   │   ├── Home/
│   │   ├── Auth/
│   │   ├── Dashboard/
│   │   ├── Offensive/
│   │   ├── Defensive/
│   │   ├── OSINT/
│   │   ├── Maximus/
│   │   ├── Immunis/
│   │   ├── ReactiveFabric/
│   │   ├── Admin/
│   │   └── Settings/
│   │
│   ├── features/                     # Features (domain-driven)
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types/
│   │   ├── offensive/
│   │   ├── defensive/
│   │   ├── osint/
│   │   ├── maximus/
│   │   ├── immunis/
│   │   └── reactive-fabric/
│   │
│   ├── components/                   # Shared components
│   │   ├── ui/                       # Design system components
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Badge/
│   │   │   ├── Alert/
│   │   │   ├── Dropdown/
│   │   │   └── ...
│   │   ├── layout/                   # Layout components
│   │   │   ├── Header/
│   │   │   ├── Sidebar/
│   │   │   ├── Footer/
│   │   │   └── Container/
│   │   └── shared/                   # Shared components
│   │       ├── LoadingSpinner/
│   │       ├── EmptyState/
│   │       ├── ErrorBoundary/
│   │       └── ...
│   │
│   ├── lib/                          # Core library code
│   │   ├── api/
│   │   │   ├── client.ts             # HTTP client
│   │   │   ├── typedClient.ts        # OpenAPI client
│   │   │   └── endpoints.ts          # Endpoint config
│   │   ├── websocket/
│   │   │   ├── WebSocketManager.ts
│   │   │   └── hooks.ts
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx
│   │   │   └── SecureTokenStore.ts
│   │   └── utils/
│   │       ├── security.ts
│   │       ├── validation.ts
│   │       └── formatting.ts
│   │
│   ├── hooks/                        # Global hooks
│   │   ├── useApi.ts
│   │   ├── useWebSocket.ts
│   │   ├── useAuth.ts
│   │   ├── useTheme.ts
│   │   └── ...
│   │
│   ├── stores/                       # Zustand stores
│   │   ├── offensiveStore.ts
│   │   ├── defensiveStore.ts
│   │   ├── themeStore.ts
│   │   └── ...
│   │
│   ├── styles/                       # Global styles
│   │   ├── globals.css
│   │   ├── design-tokens.css
│   │   ├── animations.css
│   │   └── themes/
│   │       ├── light.css
│   │       └── dark.css
│   │
│   ├── types/                        # TypeScript types
│   │   ├── api.ts
│   │   ├── models.ts
│   │   └── index.ts
│   │
│   └── config/                       # Configuration
│       ├── constants.ts
│       ├── env.ts
│       └── routes.ts
│
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

### 4.2 Padrões de Arquitetura

#### Feature-Based Organization
Cada feature (offensive, defensive, etc) é **self-contained**:
- `components/` - Componentes específicos da feature
- `hooks/` - Hooks customizados da feature
- `services/` - Lógica de negócio e chamadas API
- `types/` - TypeScript types da feature

#### Component Composition Pattern
```tsx
// Exemplo: Card component
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
  <CardFooter>
    <Button>Action</Button>
  </CardFooter>
</Card>
```

#### Service Layer Pattern (já existe)
```typescript
// services/offensiveService.ts
class OffensiveService extends BaseService {
  async scanNetwork(target: string, scanType: string) {
    return this.post('/api/offensive/scan', { target, scanType });
  }
}
```

---

## <a name="mapeamento-backend-frontend"></a>5. MAPEAMENTO BACKEND → FRONTEND

### 5.1 Áreas Principais do Sistema

| Backend Area | Frontend Page/Feature | Endpoints Mapeados |
|--------------|----------------------|-------------------|
| **Auth** | `/login`, `/auth` | `/auth/token`, `/auth/me`, `/auth/logout` |
| **Offensive Security** | `/offensive` | 11 endpoints (scans, exploits, c2, etc) |
| **Defensive Security** | `/defensive` | 9 endpoints (behavioral, traffic, alerts) |
| **OSINT** | `/osint` | 9 endpoints (email, phone, image, social, etc) |
| **Google OSINT** | `/osint/google` | 8 endpoints (5 tipos de busca + dorks) |
| **Network Scanning** | `/offensive/network` | 3 endpoints (nmap, profiles) |
| **IP Intelligence** | `/osint/ip` | 4 endpoints (analyze, geo, whois) |
| **Domain Intelligence** | `/osint/domain` | 2 endpoints (analyze, whois) |
| **Malware Analysis** | `/offensive/malware` | 4 endpoints (file, hash, url) |
| **Threat Intelligence** | `/threat-intel` | 2 endpoints (check IOC) |
| **SSL Monitoring** | `/ssl` | 2 endpoints (check cert) |
| **AI Agent** | `/ai` | 4 endpoints (chat, tools, info) |
| **Aurora Orchestrator** | `/aurora` | 4 endpoints (investigate, status) |
| **Immunis System** | `/immunis` | 14 endpoints (threats, agents, homeostasis) |
| **Reactive Fabric** | `/reactive-fabric` | Dashboard com WebSocket real-time |
| **Maximus Core** | `/maximus` | Dashboard principal (orchestrator, eureka, oraculo) |
| **SINESP (Brasil)** | `/sinesp` | 3 endpoints (veículos, ocorrências) |
| **Admin** | `/admin` | User management, roles, permissions |

### 5.2 Total de Páginas Necessárias

```
├── 🏠 Home (Landing Page)
├── 🔐 Auth (Login/Logout)
├── 📊 Dashboard (Overview geral)
│
├── 🎯 Offensive Security
│   ├── Overview
│   ├── Network Scanner
│   ├── Vulnerability Scanner
│   ├── Exploit Database
│   ├── Social Engineering
│   ├── C2 Sessions
│   └── Malware Analysis
│
├── 🛡️ Defensive Security
│   ├── Overview
│   ├── Behavioral Analysis
│   ├── Traffic Monitor
│   ├── Alerts Dashboard
│   └── Baseline Training
│
├── 🔍 OSINT
│   ├── Overview
│   ├── Google Search
│   ├── Email Analysis
│   ├── Phone Analysis
│   ├── Social Media
│   ├── Image Analysis
│   ├── Username Search
│   └── Comprehensive Investigation
│
├── 🧠 Maximus AI
│   ├── Core Dashboard
│   ├── Orchestrator
│   ├── Eureka (Discovery)
│   ├── Oráculo (Predictions)
│   ├── AI Chat
│   └── Consciousness Monitor
│
├── 🦠 Immunis System
│   ├── Overview
│   ├── Threats Dashboard
│   ├── Immune Agents
│   ├── Homeostasis Control
│   ├── Memory Bank
│   └── Lymph Nodes
│
├── ⚡ Reactive Fabric
│   ├── Threat Timeline
│   ├── Intelligence Fusion
│   ├── HITL Decision Console
│   ├── Honeypot Grid
│   └── Decoy Bayou Map
│
├── 🇧🇷 SINESP (Brasil)
│   ├── Consulta Veículos
│   ├── Ocorrências
│   └── Heatmap Criminal
│
├── ⚙️ Admin
│   ├── Users
│   ├── Roles & Permissions
│   ├── System Settings
│   └── Logs
│
└── ⚙️ Settings
    ├── Profile
    ├── Preferences
    ├── API Keys
    └── Theme
```

**Total estimado**: ~45-50 páginas/views

---

## <a name="estrutura-de-páginas"></a>6. ESTRUTURA DE PÁGINAS

### 6.1 Layout Base

Todas as páginas internas seguem o mesmo layout:

```tsx
<AppLayout>
  <Sidebar />
  <MainContent>
    <Header />
    <PageContent>
      {children}
    </PageContent>
    <Footer />
  </MainContent>
</AppLayout>
```

#### Sidebar (Estilo Claude.ai)
```
┌─────────────────────┐
│  Logo               │
├─────────────────────┤
│  🏠 Dashboard       │
│  🎯 Offensive       │
│  🛡️ Defensive       │
│  🔍 OSINT           │
│  🧠 Maximus         │
│  🦠 Immunis         │
│  ⚡ Reactive Fabric │
│  🇧🇷 SINESP          │
├─────────────────────┤
│  ⚙️ Settings        │
│  👤 Profile         │
│  🌓 Theme Toggle    │
└─────────────────────┘
```

Características:
- Background: `#FDFDF7` (light) / `#18181B` (dark)
- Largura: `280px` (desktop), collapsible em mobile
- Items com hover verde sutil
- Active state com verde accent
- Animações sutis (150ms)

#### Header
```
┌─────────────────────────────────────────────────────────┐
│  Breadcrumb  │  [Search]  │  Notifications  │  Avatar  │
└─────────────────────────────────────────────────────────┘
```

Características:
- Background: `transparent` com backdrop blur
- Sticky top
- Shadow sutil quando scrolling
- Search global com Cmd+K

### 6.2 Exemplo de Página: Offensive Dashboard

```tsx
// pages/Offensive/Overview.tsx

export default function OffensiveOverview() {
  return (
    <PageContainer>
      {/* Hero Section */}
      <PageHeader
        title="Offensive Security"
        description="Network scanning, vulnerability assessment, and penetration testing"
        icon={<Crosshair className="text-primary" />}
      />

      {/* Metrics Row */}
      <MetricsRow>
        <MetricCard
          label="Active Scans"
          value={metrics.activeScans}
          trend="+12%"
          icon={<Activity />}
        />
        <MetricCard
          label="Vulnerabilities"
          value={metrics.vulnsFound}
          severity="high"
          icon={<AlertTriangle />}
        />
        <MetricCard
          label="C2 Sessions"
          value={metrics.c2Sessions}
          icon={<Terminal />}
        />
        <MetricCard
          label="Payloads"
          value={metrics.payloads}
          icon={<Code />}
        />
      </MetricsRow>

      {/* Main Content Grid */}
      <ContentGrid>
        {/* Left Column - 2/3 width */}
        <Column span={2}>
          {/* Recent Scans Table */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Scans</CardTitle>
              <Button variant="ghost" size="sm">
                View All
              </Button>
            </CardHeader>
            <CardContent>
              <ScansTable data={recentScans} />
            </CardContent>
          </Card>

          {/* Vulnerability Timeline */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Vulnerability Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <VulnTimeline data={vulnHistory} />
            </CardContent>
          </Card>
        </Column>

        {/* Right Column - 1/3 width */}
        <Column span={1}>
          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <QuickActionButton
                icon={<Scan />}
                label="New Scan"
                onClick={handleNewScan}
              />
              <QuickActionButton
                icon={<Search />}
                label="Search Exploits"
                onClick={handleSearchExploits}
              />
              <QuickActionButton
                icon={<Terminal />}
                label="C2 Console"
                onClick={handleC2}
              />
            </CardContent>
          </Card>

          {/* Active Targets */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Active Targets</CardTitle>
            </CardHeader>
            <CardContent>
              <TargetList targets={activeTargets} />
            </CardContent>
          </Card>
        </Column>
      </ContentGrid>
    </PageContainer>
  );
}
```

---

## <a name="componentes-principais"></a>7. COMPONENTES PRINCIPAIS

### 7.1 Design System Components (ui/)

#### Button
```tsx
<Button variant="primary" size="md">
  Click me
</Button>

// Variants: primary, secondary, ghost, outline, danger
// Sizes: sm, md, lg
// States: default, hover, active, disabled, loading
```

Estilo:
- Primary: verde (#10b981) background, white text
- Hover: translateY(-1px) + shadow-md
- Active: translateY(0) + shadow-sm
- Border radius: 8px
- Transition: 150ms

#### Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

Estilo:
- Background: white (light) / #18181B (dark)
- Border: 1px solid #E5E7EB
- Border radius: 12px
- Shadow: subtle (0 1px 3px rgba(0,0,0,0.1))
- Hover: shadow-md transition

#### Input
```tsx
<Input
  type="text"
  placeholder="Search..."
  icon={<Search />}
/>
```

Estilo:
- Border: 1px solid #E5E7EB
- Focus: verde ring (0 0 0 3px rgba(16,185,129,0.1))
- Height: 40px
- Padding: 12px
- Border radius: 8px

#### Badge
```tsx
<Badge variant="success">Active</Badge>

// Variants: success, warning, danger, info, neutral
```

Estilo:
- Small, rounded-full
- Padding: 4px 12px
- Font size: 12px
- Success: verde background + darker green text

#### Modal
```tsx
<Modal open={isOpen} onClose={handleClose}>
  <ModalHeader>
    <ModalTitle>Title</ModalTitle>
  </ModalHeader>
  <ModalContent>Content</ModalContent>
  <ModalFooter>
    <Button variant="ghost" onClick={handleClose}>
      Cancel
    </Button>
    <Button onClick={handleConfirm}>
      Confirm
    </Button>
  </ModalFooter>
</Modal>
```

Animações:
- Backdrop: fadeIn 200ms
- Content: scaleIn 250ms
- Exit: reverse animations

### 7.2 Layout Components

#### Header
- Sticky positioning
- Backdrop blur quando scrolling
- Breadcrumbs
- Global search (Cmd+K)
- Notifications dropdown
- User avatar dropdown

#### Sidebar
- Fixed left, collapsible
- Navigation items com ícones
- Active state verde
- Hover state sutil
- Animações smooth (150ms)

#### Container
- Max width: 1280px (desktop)
- Padding lateral: 24px
- Centralizado

### 7.3 Shared Components

#### LoadingSpinner
```tsx
<LoadingSpinner size="md" color="primary" />
```

Estilo:
- Circular spinner verde
- Animation: spin 1s linear infinite
- Sizes: sm (16px), md (24px), lg (32px)

#### EmptyState
```tsx
<EmptyState
  icon={<Inbox />}
  title="No data yet"
  description="Start by creating your first scan"
  action={<Button>Create Scan</Button>}
/>
```

Estilo:
- Centered layout
- Icon grande e sutil
- Text muted
- CTA button verde

#### ErrorBoundary
```tsx
<ErrorBoundary fallback={<ErrorFallback />}>
  {children}
</ErrorBoundary>
```

---

## <a name="plano-de-implementação"></a>8. PLANO DE IMPLEMENTAÇÃO POR FASES

### FASE 1: FUNDAÇÃO (Semana 1)
**Objetivo**: Setup inicial + Design System

#### 1.1 Setup do Projeto
- [ ] Criar novo projeto Vite + React + TypeScript
- [ ] Configurar ESLint + Prettier
- [ ] Configurar Tailwind CSS v4
- [ ] Setup Vitest + Testing Library
- [ ] Configurar path aliases (@/, @/components, etc)

#### 1.2 Design System Base
- [ ] Criar `design-tokens.css` com todas as variáveis
- [ ] Criar `themes/light.css` e `themes/dark.css`
- [ ] Criar `animations.css` com todas as keyframes
- [ ] Implementar ThemeProvider + useTheme hook

#### 1.3 Componentes UI Base
- [ ] Button (todos os variants)
- [ ] Card (Header, Content, Footer)
- [ ] Input (text, password, email)
- [ ] Badge (todos os variants)
- [ ] Modal (Header, Content, Footer)
- [ ] Dropdown
- [ ] Alert
- [ ] LoadingSpinner
- [ ] EmptyState

**Entrega**: Storybook com todos os componentes + documentação

---

### FASE 2: AUTENTICAÇÃO & LAYOUT (Semana 2)
**Objetivo**: Auth flow + Layout base

#### 2.1 Autenticação
- [ ] Migrar `AuthContext` do projeto atual
- [ ] Migrar `SecureTokenStore`
- [ ] Criar página `/login`
- [ ] Criar página `/auth/callback` (OAuth2)
- [ ] Implementar protected routes
- [ ] Testes de auth flow

#### 2.2 Layout Base
- [ ] Sidebar component
- [ ] Header component
- [ ] Footer component
- [ ] AppLayout wrapper
- [ ] Breadcrumbs
- [ ] Global search (Cmd+K)

#### 2.3 Navegação
- [ ] React Router setup
- [ ] Route configuration
- [ ] Navigation menu
- [ ] Active state highlighting
- [ ] Mobile responsive sidebar

**Entrega**: Login funcional + Layout completo

---

### FASE 3: INFRAESTRUTURA DE DADOS (Semana 3)
**Objetivo**: HTTP client + WebSocket + State

#### 3.1 HTTP Client
- [ ] Migrar `api/client.ts` (retry, auth interceptor)
- [ ] Migrar `api/typedClient.ts` (OpenAPI)
- [ ] Configurar `endpoints.ts` com todos os endpoints
- [ ] Setup React Query
- [ ] Criar query keys factory

#### 3.2 WebSocket
- [ ] Migrar `WebSocketManager`
- [ ] Criar `useWebSocket` hook
- [ ] Testar conexão real-time
- [ ] Implementar reconnect logic

#### 3.3 State Management
- [ ] Migrar Zustand stores (offensive, defensive)
- [ ] Criar novos stores se necessário
- [ ] Implementar persistence

**Entrega**: Infraestrutura de dados completa + testes

---

### FASE 4: DASHBOARD PRINCIPAL (Semana 4)
**Objetivo**: Dashboard overview + métricas

#### 4.1 Home Dashboard
- [ ] Página `/dashboard`
- [ ] Metrics cards (scans, threats, alerts, sessions)
- [ ] Activity timeline
- [ ] System health indicators
- [ ] Quick actions panel

#### 4.2 Componentes de Dashboard
- [ ] MetricCard component
- [ ] ActivityTimeline component
- [ ] SystemHealthIndicator
- [ ] QuickActionsPanel
- [ ] Charts (se necessário)

#### 4.3 Real-time Updates
- [ ] WebSocket connection para métricas
- [ ] Auto-refresh a cada 30s
- [ ] Optimistic updates

**Entrega**: Dashboard principal funcional

---

### FASE 5: OFFENSIVE SECURITY (Semanas 5-6)
**Objetivo**: Módulo completo de Offensive

#### 5.1 Overview Page
- [ ] `/offensive` - Dashboard overview
- [ ] Metrics (scans, vulns, c2, payloads)
- [ ] Recent scans table
- [ ] Vulnerability timeline

#### 5.2 Network Scanner
- [ ] `/offensive/network-scanner`
- [ ] Form para configurar scan (target, ports, type)
- [ ] Start scan button
- [ ] Scan results table
- [ ] Scan details modal

#### 5.3 Vulnerability Scanner
- [ ] `/offensive/vuln-scanner`
- [ ] Scan configuration
- [ ] Results grid
- [ ] Exploit suggestions
- [ ] Severity filtering

#### 5.4 Social Engineering
- [ ] `/offensive/social-eng`
- [ ] Campaign creation
- [ ] Template library
- [ ] Analytics dashboard

#### 5.5 C2 Sessions
- [ ] `/offensive/c2`
- [ ] Active sessions list
- [ ] Session details
- [ ] Framework selection

#### 5.6 Malware Analysis
- [ ] `/offensive/malware`
- [ ] File upload analyzer
- [ ] Hash lookup
- [ ] URL analyzer
- [ ] Results display

**Entrega**: Módulo Offensive completo (6 páginas)

---

### FASE 6: DEFENSIVE SECURITY (Semanas 7-8)
**Objetivo**: Módulo completo de Defensive

#### 6.1 Overview Page
- [ ] `/defensive` - Dashboard overview
- [ ] Alerts summary
- [ ] Behavioral metrics
- [ ] Traffic analysis

#### 6.2 Behavioral Analysis
- [ ] `/defensive/behavioral`
- [ ] Event analyzer
- [ ] Batch analysis
- [ ] Baseline training interface
- [ ] Metrics dashboard

#### 6.3 Traffic Monitor
- [ ] `/defensive/traffic`
- [ ] Real-time traffic graph
- [ ] Anomaly detection
- [ ] Alert creation

#### 6.4 Alerts Dashboard
- [ ] `/defensive/alerts`
- [ ] Alerts table (filterable, sortable)
- [ ] Alert details modal
- [ ] Mark as resolved
- [ ] Severity badges

**Entrega**: Módulo Defensive completo (4 páginas)

---

### FASE 7: OSINT (Semanas 9-10)
**Objetivo**: Módulo completo de OSINT

#### 7.1 Overview
- [ ] `/osint` - Dashboard overview
- [ ] Recent investigations
- [ ] Stats

#### 7.2 Google OSINT
- [ ] `/osint/google`
- [ ] 5 tipos de busca (basic, advanced, documents, images, social)
- [ ] Dork patterns library
- [ ] Results display

#### 7.3 Email Analysis
- [ ] `/osint/email`
- [ ] Email input form
- [ ] Analysis results (breach, reputation, etc)

#### 7.4 Phone Analysis
- [ ] `/osint/phone`
- [ ] Phone input
- [ ] Results (carrier, location, etc)

#### 7.5 Social Media
- [ ] `/osint/social`
- [ ] Profile search
- [ ] Results aggregation

#### 7.6 Image Analysis
- [ ] `/osint/image`
- [ ] Image upload/URL
- [ ] Reverse search results

#### 7.7 Username Search
- [ ] `/osint/username`
- [ ] Username input
- [ ] Cross-platform search

#### 7.8 Comprehensive Investigation
- [ ] `/osint/investigate`
- [ ] Automated workflow
- [ ] Multi-source results

**Entrega**: Módulo OSINT completo (8 páginas)

---

### FASE 8: MAXIMUS AI (Semanas 11-12)
**Objetivo**: Dashboard do Maximus (core AI)

#### 8.1 Core Dashboard
- [ ] `/maximus` - Main dashboard
- [ ] Orchestrator status
- [ ] Eureka discovery
- [ ] Oráculo predictions

#### 8.2 AI Chat
- [ ] `/maximus/chat`
- [ ] Chat interface (estilo Claude.ai)
- [ ] Message history
- [ ] Tools display

#### 8.3 Consciousness Monitor
- [ ] `/maximus/consciousness`
- [ ] Arousal level display
- [ ] ESGT events stream (WebSocket)
- [ ] System health

#### 8.4 Predictions
- [ ] `/maximus/predictions`
- [ ] Threat predictions
- [ ] Confidence scores
- [ ] Historical accuracy

**Entrega**: Módulo Maximus completo (4 páginas)

---

### FASE 9: IMMUNIS SYSTEM (Semanas 13-14)
**Objetivo**: Sistema imunológico biológico

#### 9.1 Overview
- [ ] `/immunis` - Dashboard
- [ ] System health
- [ ] Active threats
- [ ] Agents status

#### 9.2 Threats Dashboard
- [ ] `/immunis/threats`
- [ ] Threats table
- [ ] Threat details
- [ ] Detection timeline

#### 9.3 Immune Agents
- [ ] `/immunis/agents`
- [ ] Agents grid (B-cell, T-cell, etc)
- [ ] Agent details
- [ ] Activity logs

#### 9.4 Homeostasis
- [ ] `/immunis/homeostasis`
- [ ] System balance indicators
- [ ] Adjustment controls
- [ ] Historical data

#### 9.5 Memory Bank
- [ ] `/immunis/memory`
- [ ] Antibodies library
- [ ] Memory search
- [ ] Pattern recognition

**Entrega**: Módulo Immunis completo (5 páginas)

---

### FASE 10: REACTIVE FABRIC (Semana 15)
**Objetivo**: Orquestração e resposta

#### 10.1 Threat Timeline
- [ ] `/reactive-fabric/timeline`
- [ ] Real-time threat timeline (WebSocket)
- [ ] Event filtering

#### 10.2 Intelligence Fusion
- [ ] `/reactive-fabric/fusion`
- [ ] Multi-source intelligence
- [ ] Correlation engine

#### 10.3 HITL Console
- [ ] `/reactive-fabric/hitl`
- [ ] Decision queue
- [ ] Approval interface
- [ ] Auth check (offensive role)

#### 10.4 Honeypot Grid
- [ ] `/reactive-fabric/honeypot`
- [ ] Honeypot status grid
- [ ] Interactions log

**Entrega**: Módulo Reactive Fabric completo (4 páginas)

---

### FASE 11: SINESP (Semana 16)
**Objetivo**: Integração brasileira

#### 11.1 Consulta Veículos
- [ ] `/sinesp/veiculos`
- [ ] Input de placa
- [ ] Resultado formatado
- [ ] Cache de 1h

#### 11.2 Ocorrências
- [ ] `/sinesp/ocorrencias`
- [ ] Tipos de crime
- [ ] Heatmap interativo

**Entrega**: Módulo SINESP completo (2 páginas)

---

### FASE 12: ADMIN & SETTINGS (Semana 17)
**Objetivo**: Administração e configurações

#### 12.1 Admin - Users
- [ ] `/admin/users`
- [ ] Users table
- [ ] Create/Edit user modal
- [ ] Role assignment

#### 12.2 Admin - Roles
- [ ] `/admin/roles`
- [ ] Roles grid
- [ ] Permissions matrix

#### 12.3 Settings - Profile
- [ ] `/settings/profile`
- [ ] User info edit
- [ ] Password change

#### 12.4 Settings - Preferences
- [ ] `/settings/preferences`
- [ ] Theme toggle
- [ ] Language selection

**Entrega**: Admin + Settings completo (4 páginas)

---

### FASE 13: POLIMENTO & OTIMIZAÇÃO (Semana 18)
**Objetivo**: Performance, acessibilidade, testes

#### 13.1 Performance
- [ ] Code splitting por rota
- [ ] Lazy loading de componentes pesados
- [ ] Image optimization
- [ ] Bundle size analysis
- [ ] Lighthouse audit (95+ score)

#### 13.2 Acessibilidade
- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Focus management
- [ ] ARIA labels

#### 13.3 Testes
- [ ] Unit tests (components)
- [ ] Integration tests (features)
- [ ] E2E tests (critical flows)
- [ ] Coverage > 80%

#### 13.4 Documentação
- [ ] Storybook completo
- [ ] README.md
- [ ] Contributing guide
- [ ] Architecture docs

**Entrega**: App production-ready

---

## <a name="checklist-de-features"></a>9. CHECKLIST DE FEATURES

### ✅ Autenticação & Autorização
- [ ] Login com OAuth2 (Google)
- [ ] JWT token management
- [ ] Auto-refresh tokens (5min antes de expirar)
- [ ] Protected routes
- [ ] Role-based access (admin, analyst, offensive)
- [ ] Permission checks
- [ ] Cross-tab sync (logout em uma aba → logout em todas)

### ✅ Temas & Design
- [ ] Light mode
- [ ] Dark mode
- [ ] Sistema de design completo (50+ tokens)
- [ ] Animações sutis e smooth
- [ ] Verde como cor primária (#10b981)
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility (WCAG 2.1 AA)

### ✅ Offensive Security (11 endpoints)
- [ ] Network scanning (Nmap)
- [ ] Vulnerability scanning
- [ ] Exploit database search
- [ ] Social engineering campaigns
- [ ] C2 session management
- [ ] Malware analysis (file, hash, URL)
- [ ] Payload generation

### ✅ Defensive Security (9 endpoints)
- [ ] Behavioral analysis
- [ ] Traffic monitoring
- [ ] Alerts dashboard
- [ ] Baseline training
- [ ] Batch analysis
- [ ] Metrics display

### ✅ OSINT (17 endpoints total)
- [ ] Google search (5 tipos)
- [ ] Google dorks library
- [ ] Email analysis
- [ ] Phone analysis
- [ ] Social media search
- [ ] Image analysis
- [ ] Username search
- [ ] Comprehensive investigation
- [ ] IP intelligence (analyze, geo, whois, my-ip)
- [ ] Domain intelligence (analyze, whois)

### ✅ Maximus AI (múltiplos serviços)
- [ ] Core dashboard
- [ ] Orchestrator status
- [ ] Eureka service discovery
- [ ] Oráculo predictions
- [ ] AI chat interface
- [ ] Consciousness monitor (arousal, ESGT events)
- [ ] Tools display

### ✅ Immunis System (14 endpoints)
- [ ] Threats dashboard (detect, list, details)
- [ ] Immune agents (list, details)
- [ ] Homeostasis control (adjust, status)
- [ ] Lymph nodes (list, details)
- [ ] Memory bank (antibodies, search)
- [ ] Metrics & stats

### ✅ Reactive Fabric
- [ ] Threat timeline (real-time)
- [ ] Intelligence fusion
- [ ] HITL decision console
- [ ] Honeypot status grid
- [ ] Decoy bayou map

### ✅ SINESP (Brasil)
- [ ] Consulta de veículos por placa
- [ ] Tipos de ocorrências
- [ ] Heatmap criminal

### ✅ Admin & Settings
- [ ] User management (CRUD)
- [ ] Role management
- [ ] Permissions matrix
- [ ] Profile settings
- [ ] Preferences
- [ ] API keys
- [ ] System logs

### ✅ Real-time (WebSockets)
- [ ] Consciousness stream
- [ ] Maximus predictions
- [ ] Threat alerts
- [ ] Execution status
- [ ] Auto-reconnect
- [ ] Fallback SSE/polling

### ✅ Infraestrutura
- [ ] HTTP client (retry logic, auth interceptor, CSRF)
- [ ] Type-safe API (OpenAPI fetch)
- [ ] React Query (cache, refetch, mutations)
- [ ] Zustand stores (offline persistence)
- [ ] WebSocket manager (pub/sub, heartbeat)
- [ ] Error boundary
- [ ] Loading states
- [ ] Empty states
- [ ] Toast notifications

### ✅ Performance
- [ ] Code splitting
- [ ] Lazy loading
- [ ] Image optimization
- [ ] Bundle size < 300KB (gzipped)
- [ ] Lighthouse score > 95
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s

### ✅ Qualidade
- [ ] TypeScript strict mode
- [ ] ESLint + Prettier
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests
- [ ] E2E tests (critical flows)
- [ ] Storybook completo

---

## 📊 RESUMO EXECUTIVO

### Números do Projeto

| Métrica | Valor |
|---------|-------|
| **Total de Páginas** | ~50 páginas/views |
| **Backend Endpoints Mapeados** | 250+ endpoints |
| **Backend Services Integrados** | 100+ serviços |
| **Componentes UI** | 30+ componentes base |
| **Features Principais** | 9 módulos completos |
| **Tempo Estimado** | 18 semanas (4.5 meses) |
| **Fases de Implementação** | 13 fases |

### Stack Final

```
Frontend: React 18 + TypeScript + Vite
Styling: Tailwind CSS v4 + CSS Modules
UI: Radix UI Primitives (headless)
State: React Query + Zustand
Auth: OAuth2 + JWT
HTTP: openapi-fetch (type-safe)
WebSocket: Custom manager (pub/sub)
Icons: Lucide React
Animations: CSS + Framer Motion
Testing: Vitest + Testing Library + Playwright
```

### Design Philosophy

```
✅ Clean, Calm, Focused (Claude.ai inspired)
✅ Verde (#10b981) como cor primária
✅ Sans-serif typography
✅ Animações sutis (150-350ms)
✅ Shadows sutis, sem drama
✅ Minimalismo extremo
✅ Performance obsessiva
✅ Acessibilidade WCAG 2.1 AA
```

---

## 🚀 PRÓXIMOS PASSOS

1. **Revisar este plano** com a equipe
2. **Aprovar design system** (cores, tipografia, animações)
3. **Criar repo novo** `frontend-vertice-v2`
4. **Iniciar FASE 1** - Setup + Design System
5. **Setup CI/CD** - Deploy preview em cada PR
6. **Documentar decisões** - ADRs para decisões importantes

---

## 📝 NOTAS FINAIS

### Decisões de Design

1. **Por que Verde ao invés de Vermelho/Laranja?**
   - Mais calmo, profissional
   - Associado a segurança ("verde = seguro")
   - Diferenciação visual
   - Já implementado no design system atual

2. **Por que Sans-serif ao invés de Serif?**
   - Melhor legibilidade em telas (especialmente dashboards com muitos dados)
   - Mais moderno e clean
   - Melhor para UI/dashboards técnicos
   - Claude.ai usa sans-serif para UI

3. **Por que Radix UI?**
   - Headless (controle total do estilo)
   - Acessibilidade built-in
   - Composable components
   - Sem opiniões de design

4. **Por que manter React Query + Zustand?**
   - Já funciona bem
   - React Query para server state (cache, refetch)
   - Zustand para client state (UI, preferences)
   - Separação de responsabilidades clara

### Riscos & Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Escopo muito grande | Alta | Implementar por fases, MVP primeiro |
| Performance issues | Média | Code splitting, lazy loading, otimizações |
| Inconsistência de design | Média | Design system rigoroso, code review |
| Bugs de integração | Média | Testes E2E, staging environment |

---

**PLANO CRIADO POR**: Claude Code
**DATA**: 2025-11-15
**VERSÃO**: 1.0
**STATUS**: ✅ Ready to Implement

---

_"Clean, calm, focused - com verde ao invés de laranja"_
_SOLI DEO GLORIA_
