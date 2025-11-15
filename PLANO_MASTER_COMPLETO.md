# PLANO MASTER COMPLETO - VÉRTICE FRONTEND v3.3.1

**Data de Criação**: 2025-01-16
**Última Atualização**: 2025-01-16 (18:32 PM)
**Versão**: 2.1
**Status**: PRIORIDADE 2 COMPLETA - Opção B Implementada (65-70 páginas)
**Filosofia**: "Cada pixel importa. Cada transição encanta."

---

## ÍNDICE

1. [Visão Geral do Projeto](#visão-geral)
2. [Filosofia de Design (Claude Code Inspired)](#filosofia-de-design)
3. [Design System Completo](#design-system)
4. [Stack Tecnológica](#stack-tecnológica)
5. [Arquitetura Frontend](#arquitetura-frontend)
6. [Mapeamento Backend → Frontend](#mapeamento-backend-frontend)
7. [Estrutura de Páginas (65-70 páginas - Opção B)](#estrutura-de-páginas)
8. [Componentes Principais](#componentes-principais)
9. [Plano de Implementação por Fases](#plano-de-implementação)
10. [Progresso Atual](#progresso-atual)
11. [Checklist Completo de Features](#checklist-completo)
12. [Guia de Estilo - Manter Sempre](#guia-de-estilo)
13. [Referências](#referências)

---

## <a name="visão-geral"></a>1. VISÃO GERAL DO PROJETO

### Objetivo

Construir um frontend **COMPLETO E REFINADO** que:

- ✅ Seja **CLEAN, SÓBRIO e MINIMALISTA** inspirado no Claude Web App
- ✅ Tenha **ATENÇÃO CIRÚRGICA AOS DETALHES** em cada pixel
- ✅ Utilize **VERDE** (#10b981) como cor de acento principal
- ✅ Represente **TODAS** as funcionalidades do backend (250+ endpoints, 100+ serviços)
- ✅ Mantenha animações **SUTIS, INTENCIONAIS e SMOOTH**
- ✅ Tenha **ALMA** - cada detalhe é milimetricamente pensado

### Princípios Fundamentais

> "Esse tipo de cuidado encanta. Esse tipo de cuidado existe no Claude web app. Cada transição, cada microanimação, a formação do quadro de código no chat, tudo é milimetricamente detalhado."

1. **Cuidado Cirúrgico** - Cada pixel importa, cada espaçamento é intencional
2. **Micro-animações Intencionais** - Feedback visual preciso e suave (150-200ms)
3. **Tipografia Precisa** - `leading-none`, `tracking-wider`, `tabular-nums`
4. **Profundidade Sutil** - Rings, shadows e contornos bem dosados
5. **Minimalismo com Alma** - Clean, mas com identidade única
6. **Verde sobre Tudo** - #10b981 como cor primária (não vermelho/laranja)

---

## <a name="filosofia-de-design"></a>2. FILOSOFIA DE DESIGN (CLAUDE CODE INSPIRED)

### Inspiração: Claude Web App

O Claude Web App é o padrão de qualidade. Observar:

- **Tipografia**: Fonte sans-serif, tamanhos exatos, leading preciso
- **Espaçamentos**: Fibonacci-inspired, consistentes em todo o app
- **Animações**: Sutis, intencionais, nunca chamativas
- **Contornos**: Linhas finas brancas que definem elementos sem drama
- **Shadows**: Ultra-sutis, apenas para dar profundidade
- **Feedback**: Cada interação tem resposta visual milimétrica

### Detalhes que Encantam

#### Micro-animações (150-200ms)

```tsx
// Botões
hover:scale-105 active:scale-95 transition-all duration-200

// Cards
hover:-translate-y-px hover:shadow-md transition-all duration-200 ease-out

// Nav Items
hover:translate-x-0.5 active:scale-[0.98] transition-all duration-200
```

#### Tipografia Cirúrgica

```tsx
// Títulos de cards - exatamente 10px
text-[10px] font-semibold uppercase tracking-wider leading-none

// Números principais - tabular para alinhamento perfeito
text-3xl font-bold tabular-nums leading-none

// Labels pequenos
text-[10px] tracking-wider font-medium leading-none
```

#### Contornos Definidos

```tsx
// PieChart
stroke="#ffffff" strokeWidth={2}

// BarChart
stroke="#ffffff" strokeWidth={1.5}

// LineChart/AreaChart
strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round"
```

#### Profundidade Sutil

```tsx
// Círculos de status com ring
ring-1 ring-primary-500/20

// Cards
shadow-sm hover:shadow-md

// Tooltips
boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
```

#### Grid Ultra-Fino

```tsx
// Recharts - grid quase invisível
<CartesianGrid strokeWidth={0.5} stroke="#e5e7eb" vertical={false} />
```

---

## <a name="design-system"></a>3. DESIGN SYSTEM COMPLETO

### 3.1 Paleta de Cores

```css
/* MODO CLARO (Primary) */
--background: #fafafa; /* Off-white neutro */
--foreground: #09090b; /* Nearly black */

--primary: #10b981; /* Verde Emerald-500 */
--primary-hover: #059669; /* Verde Emerald-600 */
--primary-active: #047857; /* Verde Emerald-700 */

--card: #ffffff; /* Pure white cards */
--card-border: #e5e7eb; /* Subtle gray border */

--text-primary: #09090b; /* Main text - zinc-950 */
--text-secondary: #64748b; /* Secondary text - slate-500 */
--text-tertiary: #94a3b8; /* Tertiary text - slate-400 */

--border: #e5e7eb; /* Border color */

--success: #10b981; /* Verde */
--warning: #f59e0b; /* Amber */
--danger: #ef4444; /* Red */
--info: #3b82f6; /* Blue */
```

```css
/* MODO ESCURO */
--background: #09090b; /* Deep black */
--foreground: #fafaf9; /* Light gray */

--primary: #34d399; /* Verde Emerald-400 (mais claro) */
--primary-hover: #10b981; /* Verde Emerald-500 */

--card: #18181b; /* Dark card */
--card-border: #27272a; /* Dark border */

--text-primary: #fafaf9; /* Light text */
--text-secondary: #94a3b8; /* Gray text */
--text-tertiary: #64748b; /* Darker muted */
```

### 3.2 Tipografia

```css
/* Font Families */
--font-sans:
  ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
  Roboto, sans-serif;
--font-mono:
  ui-monospace, "Cascadia Code", "Source Code Pro", Menlo, Consolas, monospace;

/* Tamanhos - Modular Scale */
--text-xs: 0.75rem; /* 12px - badges, captions */
--text-sm: 0.875rem; /* 14px - small body */
--text-base: 1rem; /* 16px - body text */
--text-lg: 1.125rem; /* 18px - large body */
--text-xl: 1.25rem; /* 20px - subtitle */
--text-2xl: 1.5rem; /* 24px - h3 */
--text-3xl: 1.875rem; /* 30px - h2 */
--text-4xl: 2.25rem; /* 36px - h1 */

/* Pesos */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### 3.3 Espaçamento Preciso

```css
/* Fibonacci-inspired spacing */
--space-xs: 0.25rem; /* 4px */
--space-sm: 0.5rem; /* 8px */
--space-md: 1rem; /* 16px */
--space-lg: 1.5rem; /* 24px */
--space-xl: 2.5rem; /* 40px */
--space-2xl: 4rem; /* 64px */

/* Gaps específicos do Dashboard */
--gap-dashboard: 1.5rem; /* 24px - space-y-6 */
--gap-grid: 0.875rem; /* 14px - gap-3.5 */
--gap-card-internal: 1rem; /* 16px - gap-4 */
--gap-legends: 0.5rem; /* 8px - space-y-2 */
```

### 3.4 Border Radius

```css
--radius-sm: 0.25rem; /* 4px - small elements */
--radius-md: 0.5rem; /* 8px - cards, buttons */
--radius-lg: 0.75rem; /* 12px - large cards */
--radius-full: 9999px; /* Circular */
```

### 3.5 Shadows

```css
/* Sutis, elegantes */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

/* Verde glow (sutil) */
--shadow-glow-green: 0 0 20px rgba(16, 185, 129, 0.2);

/* Tooltips */
--shadow-tooltip: 0 2px 8px rgba(0, 0, 0, 0.08);
```

### 3.6 Animações

```css
/* Transições sutis */
--transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 200ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

/* Sempre usar ease-out para movimento natural */
transition-all duration-200 ease-out
```

---

## <a name="stack-tecnológica"></a>4. STACK TECNOLÓGICA

### 4.1 Core

```json
{
  "framework": "React 18",
  "build": "Vite",
  "language": "TypeScript",
  "routing": "React Router v6"
}
```

### 4.2 Estilo

```json
{
  "styling": "Tailwind CSS",
  "icons": "Lucide React",
  "charts": "Recharts",
  "toasts": "Sonner"
}
```

### 4.3 Estado & Dados

```json
{
  "client-state": "Zustand",
  "forms": "React Hook Form + Zod",
  "websockets": "Native WebSocket API"
}
```

### 4.4 Utilities

```json
{
  "cn": "clsx + tailwind-merge",
  "variants": "class-variance-authority"
}
```

---

## <a name="arquitetura-frontend"></a>5. ARQUITETURA FRONTEND

### 5.1 Estrutura de Diretórios Atual

```
frontend/
├── src/
│   ├── components/
│   │   ├── charts/              # Componentes de gráfico
│   │   │   ├── PieChart.tsx
│   │   │   ├── BarChart.tsx
│   │   │   ├── LineChart.tsx
│   │   │   └── AreaChart.tsx
│   │   ├── layout/              # Header, Sidebar, Footer
│   │   │   ├── Header/
│   │   │   ├── Sidebar/
│   │   │   └── Footer/
│   │   └── ui/                  # Componentes base
│   │       ├── Card/
│   │       ├── Button/
│   │       └── Toast/
│   │
│   ├── hooks/                   # Custom hooks
│   │   ├── useToast.ts
│   │   └── useWebSocket.ts
│   │
│   ├── lib/                     # Utilities
│   │   ├── auth/                # Context de autenticação
│   │   └── utils.ts             # cn() e outros
│   │
│   ├── pages/                   # Páginas da aplicação
│   │   └── Dashboard/
│   │       └── DashboardPage.tsx
│   │
│   ├── stores/                  # Zustand stores
│   │   └── themeStore.ts
│   │
│   ├── App.tsx                  # App principal
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles + design tokens
│
├── public/
├── .claude/
│   └── commands/
│       └── retomar.md
├── PLANO_MESTRE_FRONTEND.md      # Plano anterior (fase 1)
├── PLANO_MASTER_COMPLETO.md      # Este arquivo
└── package.json
```

### 5.2 Estrutura Completa (Objetivo Final)

```
frontend/
├── src/
│   ├── pages/                        # 45-50 páginas
│   │   ├── Home/
│   │   ├── Auth/
│   │   ├── Dashboard/                # ✅ COMPLETA
│   │   ├── Offensive/
│   │   │   ├── OffensivePage.tsx
│   │   │   ├── NetworkScanner.tsx
│   │   │   ├── VulnScanner.tsx
│   │   │   ├── SocialEng.tsx
│   │   │   ├── C2Sessions.tsx
│   │   │   └── MalwareAnalysis.tsx
│   │   ├── Defensive/
│   │   │   ├── DefensivePage.tsx
│   │   │   ├── BehavioralAnalysis.tsx
│   │   │   ├── TrafficMonitor.tsx
│   │   │   └── AlertsDashboard.tsx
│   │   ├── OSINT/
│   │   │   ├── OSINTPage.tsx
│   │   │   ├── GoogleOSINT.tsx
│   │   │   ├── EmailAnalysis.tsx
│   │   │   ├── PhoneAnalysis.tsx
│   │   │   ├── SocialMedia.tsx
│   │   │   ├── ImageAnalysis.tsx
│   │   │   ├── UsernameSearch.tsx
│   │   │   └── ComprehensiveInvestigation.tsx
│   │   ├── Maximus/
│   │   │   ├── MaximusPage.tsx
│   │   │   ├── Orchestrator.tsx
│   │   │   ├── Eureka.tsx
│   │   │   ├── Oraculo.tsx
│   │   │   ├── AIChat.tsx
│   │   │   └── ConsciousnessMonitor.tsx
│   │   ├── Immunis/
│   │   │   ├── ImmunisPage.tsx
│   │   │   ├── ThreatsDashboard.tsx
│   │   │   ├── ImmuneAgents.tsx
│   │   │   ├── Homeostasis.tsx
│   │   │   └── MemoryBank.tsx
│   │   ├── ReactiveFabric/
│   │   │   ├── ReactiveFabricPage.tsx
│   │   │   ├── ThreatTimeline.tsx
│   │   │   ├── IntelligenceFusion.tsx
│   │   │   ├── HITLConsole.tsx
│   │   │   └── HoneypotGrid.tsx
│   │   ├── SINESP/
│   │   │   ├── SINESPPage.tsx
│   │   │   ├── VehicleQuery.tsx
│   │   │   └── CrimeHeatmap.tsx
│   │   ├── Admin/
│   │   │   ├── AdminPage.tsx
│   │   │   ├── Users.tsx
│   │   │   └── Roles.tsx
│   │   └── Settings/
│   │       ├── SettingsPage.tsx
│   │       ├── Profile.tsx
│   │       └── Preferences.tsx
│   │
│   ├── features/                     # Domain-driven features
│   │   ├── offensive/
│   │   ├── defensive/
│   │   ├── osint/
│   │   └── ...
│   │
│   ├── components/
│   │   ├── charts/                   # ✅ COMPLETO
│   │   ├── layout/                   # ✅ COMPLETO
│   │   └── ui/                       # Base components
│   │
│   └── ...
```

---

## <a name="mapeamento-backend-frontend"></a>6. MAPEAMENTO BACKEND → FRONTEND

### 6.1 Backend Summary

**Total de Endpoints**: 250+
**Total de Serviços**: 100+
**API Version**: v3.3.1
**Base URL**: `http://localhost:8000`

### 6.2 Categorias e Páginas (REVISADO - OPÇÃO B)

**NOTA**: Plano revisado para **65-70 páginas** após análise detalhada do backend (100+ serviços).

| Backend Category              | Frontend Page/Feature | Endpoints/Serviços    | Páginas   | Prioridade  |
| ----------------------------- | --------------------- | --------------------- | --------- | ----------- |
| **Auth**                      | `/login`, `/auth`     | 5 endpoints           | 2         | ✅ FASE 2   |
| **Dashboard**                 | `/dashboard`          | Métricas agregadas    | 1         | ✅ COMPLETO |
| **Offensive Security**        | `/offensive`          | 11 endpoints          | 7         | FASE 5-6    |
| **Defensive Security**        | `/defensive`          | 9 endpoints           | 4         | FASE 7-8    |
| **OSINT**                     | `/osint`              | 17 endpoints          | 8         | FASE 9-10   |
| **Maximus AI Ecosystem** ⭐   | `/maximus`            | 8 serviços + WS       | **9**     | FASE 11-12  |
| **Adaptive Immune System** ⭐ | `/immunis`            | 12 serviços, 14 endp. | **10**    | FASE 13-14  |
| **HCL/HITL Workflow** ⭐      | `/hitl`               | 6 serviços            | **5**     | FASE 15     |
| **Reactive Fabric** ⭐        | `/reactive-fabric`    | WebSocket RT          | **6**     | FASE 16     |
| **Aurora Orchestrator** ⭐    | `/aurora`             | 4 endpoints           | **3**     | FASE 17     |
| **Digital Thalamus** ⭐       | `/thalamus`           | 1 serviço             | **2**     | FASE 18     |
| **Narrative Analysis** ⭐     | `/narrative`          | 4 serviços            | **3**     | FASE 19     |
| **Wargaming/Simulation** ⭐   | `/wargaming`          | 3 serviços            | **2**     | FASE 20     |
| **SINESP (Brasil)**           | `/sinesp`             | 3 endpoints           | 2         | FASE 21     |
| **Admin**                     | `/admin`              | User/Roles CRUD       | 2         | FASE 22     |
| **Settings**                  | `/settings`           | Profile/Preferences   | 3         | FASE 22     |
|                               |                       | **TOTAL**             | **65-70** | 22 fases    |

⭐ = Expandido ou Novo na Revisão

### 6.3 Detalhamento de Endpoints (Principais)

#### Offensive Security (11 endpoints)

```
POST /cyber/network-scan                    # Network scan
POST /api/nmap/scan                         # Nmap scan
POST /api/vuln-scanner/scan                 # Vulnerability scan
GET  /api/vuln-scanner/exploits             # List exploits
POST /api/social-eng/campaign               # Social eng campaign
GET  /api/social-eng/templates              # Templates
POST /api/malware/analyze-file              # Malware analysis
POST /api/malware/analyze-hash
POST /api/malware/analyze-url
GET  /api/vuln-scanner/scan/{id}            # Scan status
```

#### Defensive Security (9 endpoints)

```
POST /api/defensive/behavioral/analyze              # Behavioral analysis
POST /api/defensive/behavioral/analyze-batch
POST /api/defensive/behavioral/train-baseline
GET  /api/defensive/behavioral/baseline-status
GET  /api/defensive/behavioral/metrics
POST /api/defensive/traffic/analyze                 # Traffic analysis
POST /api/defensive/traffic/analyze-batch
GET  /api/defensive/traffic/metrics
GET  /api/defensive/health
```

#### OSINT (17 endpoints total)

```
# Google OSINT (8)
POST /api/google/search/basic
POST /api/google/search/advanced
POST /api/google/search/documents
POST /api/google/search/images
POST /api/google/search/social
GET  /api/google/dorks/patterns
GET  /api/google/stats

# General OSINT (9)
POST /api/email/analyze
POST /api/phone/analyze
POST /api/image/analyze
POST /api/social/profile
POST /api/username/search
POST /api/search/comprehensive
POST /api/investigate/auto
POST /api/ip/analyze
POST /api/domain/analyze
```

#### Maximus AI (4 + WebSocket)

```
POST /api/ai/chat                  # AI Chat
GET  /api/ai/tools                 # Tools list
POST /api/aurora/investigate       # Start investigation
GET  /api/aurora/investigation/{id}
WS   /ws/predictions               # Real-time predictions
WS   /ws/threats                   # Threat alerts
```

#### Immunis System (14 endpoints)

```
POST /api/immune/threats/detect
GET  /api/immune/threats
GET  /api/immune/threats/{id}
GET  /api/immune/agents
GET  /api/immune/agents/{id}
POST /api/immune/homeostasis/adjust
GET  /api/immune/homeostasis
GET  /api/immune/lymphnodes
GET  /api/immune/lymphnodes/{id}
GET  /api/immune/memory/antibodies
GET  /api/immune/memory/search
GET  /api/immune/metrics
GET  /api/immune/stats
GET  /api/immune/health
```

#### SINESP (3 endpoints)

```
GET  /veiculos/{placa}             # Vehicle lookup
GET  /ocorrencias/tipos            # Crime types
GET  /ocorrencias/heatmap          # Crime heatmap
```

---

## <a name="estrutura-de-páginas"></a>7. ESTRUTURA DE PÁGINAS (45-50 TOTAL)

### 7.1 Layout Base (COMPLETO)

```tsx
<AppLayout>
  <Sidebar /> {/* ✅ COMPLETO com micro-animações */}
  <MainContent>
    <Header /> {/* ✅ COMPLETO com micro-animações */}
    <PageContent>{children}</PageContent>
    <Footer /> {/* ✅ COMPLETO */}
  </MainContent>
</AppLayout>
```

### 7.2 Páginas por Módulo (REVISADO - OPÇÃO B)

**TOTAL REVISADO: 65-70 PÁGINAS**

```
📊 DASHBOARD (1 página)
✅ Dashboard Overview                    # COMPLETO - Refinado com atenção cirúrgica

🔐 AUTH (2 páginas)
⬜ Login
⬜ Callback OAuth

🎯 OFFENSIVE SECURITY (7 páginas)
⬜ Offensive Overview
⬜ Network Scanner
⬜ Vulnerability Scanner
⬜ Social Engineering
⬜ C2 Sessions
⬜ Malware Analysis
⬜ Exploit Database

🛡️ DEFENSIVE SECURITY (4 páginas)
⬜ Defensive Overview
⬜ Behavioral Analysis
⬜ Traffic Monitor
⬜ Alerts Dashboard

🔍 OSINT (8 páginas)
⬜ OSINT Overview
⬜ Google OSINT
⬜ Email Analysis
⬜ Phone Analysis
⬜ Social Media Search
⬜ Image Analysis
⬜ Username Search
⬜ Comprehensive Investigation

🧠 MAXIMUS AI ECOSYSTEM (9 páginas) ⭐ EXPANDIDO
⬜ Maximus Core Dashboard               # Central hub
⬜ AI Orchestrator                      # Workflow orchestration
⬜ Eureka Service Discovery             # Services mesh
⬜ Oráculo V2 Predictions               # Advanced AI predictions
⬜ Aurora Predict (ML)                  # Machine learning forecasting
⬜ Integration Layer                    # Service integration status
⬜ DLQ Monitor                          # Dead Letter Queue monitoring
⬜ AI Chat Interface                    # Chat with MAXIMUS
⬜ Consciousness Monitor                # Arousal, ESGT events (WebSocket)

🦠 ADAPTIVE IMMUNE SYSTEM (10 páginas) ⭐ EXPANDIDO
⬜ Immunis Main Dashboard               # Overview do sistema inteiro
⬜ Threats Detection & Response         # Threat lifecycle completo
⬜ Immune Agents Overview               # Todos os 7 tipos de células
⬜ B-Cells Dashboard                    # Antibody production específica
⬜ T-Cells Dashboard                    # Helper, Cytotoxic, Regulatory
⬜ Dendritic Cells Dashboard            # Antigen presentation
⬜ Phagocytes Dashboard                 # Macrophages + Neutrophils
⬜ Homeostasis Control                  # System balance
⬜ Memory Bank & Antibodies             # Immunological memory
⬜ Lymph Nodes Network                  # Communication network

👤 HCL/HITL WORKFLOW (5 páginas) ⭐ NOVA
⬜ HITL Main Dashboard                  # Workflow overview
⬜ Analysis Queue                       # Tasks for analysis
⬜ Planning & Execution                 # Automated plans + execution
⬜ Human Decision Console               # Approval/rejection interface
⬜ Knowledge Base                       # Historical decisions, patterns

⚡ REACTIVE FABRIC (6 páginas) ⭐ EXPANDIDO
⬜ Reactive Fabric Main                 # Orchestration hub
⬜ Threat Timeline (WebSocket)          # Real-time threats
⬜ Intelligence Fusion                  # Multi-source correlation
⬜ HITL Decision Console                # Human decisions (link to HITL)
⬜ Honeypot Grid                        # Honeypot status
⬜ Decoy Bayou Map                      # Decoy network visualization

🌅 AURORA ORCHESTRATOR (3 páginas) ⭐ NOVA
⬜ Aurora Main Dashboard                # Investigation orchestration
⬜ Active Investigations                # Running investigations
⬜ Services Mesh                        # Available services for orchestration

🧠 DIGITAL THALAMUS (2 páginas) ⭐ NOVA
⬜ Thalamus Dashboard                   # Neural routing overview
⬜ Signal Routing Map                   # Real-time signal flow

📰 NARRATIVE ANALYSIS (3 páginas) ⭐ NOVA
⬜ Narrative Dashboard                  # Manipulation detection
⬜ Propaganda Techniques                # Detected techniques
⬜ Seriema Graph Viz                    # Graph visualization

🎮 WARGAMING & SIMULATION (2 páginas) ⭐ NOVA
⬜ Wargaming Dashboard                  # Scenario simulation
⬜ Strategic Planning                   # Strategic decisions

🇧🇷 SINESP (2 páginas)
⬜ Vehicle Query
⬜ Crime Heatmap

⚙️ ADMIN (2 páginas)
⬜ User Management
⬜ Roles & Permissions

⚙️ SETTINGS (3 páginas)
⬜ Profile
⬜ Preferences
⬜ API Keys

TOTAL: 65-70 páginas (22 fases de implementação)
⭐ = Expandido ou Novo na Revisão
```

---

## <a name="componentes-principais"></a>8. COMPONENTES PRINCIPAIS

### 8.1 Charts (COMPLETO - Refinado)

#### PieChart.tsx

```tsx
// Características refinadas:
- innerRadius={35} outerRadius={50}      // Ajustado para não cortar
- stroke="#ffffff" strokeWidth={2}        // Contorno branco definido
- isAnimationActive={false}               // Sem animações
- Cores: #10b981 (verde), #6b7280 (cinza)
- Legendas manuais com rings: ring-1 ring-[color]/20
```

#### BarChart.tsx

```tsx
// Características refinadas:
- stroke="#ffffff" strokeWidth={1.5}      // Contorno branco nas barras
- radius={[3, 3, 0, 0]}                   // Cantos arredondados no topo
- barGap={6} barCategoryGap="20%"         // Espaçamento preciso
- Grid: strokeWidth={0.5}                 // Ultra-sutil
- Axes: fontSize={10} fontWeight={500}    // Tipografia precisa
- Margins: top: 10, right: 10, left: -10, bottom: 0
```

#### LineChart.tsx

```tsx
// Características refinadas:
- strokeWidth={2.5}                       // Linha definida
- strokeLinecap="round"                   // Pontas arredondadas
- strokeLinejoin="round"                  // Junções suaves
- dot={false}                             // Sem pontos
- isAnimationActive={false}
```

#### AreaChart.tsx

```tsx
// Características refinadas:
- strokeWidth={2.5}
- strokeLinecap="round" strokeLinejoin="round"
- fillOpacity={0.15}                      // Preenchimento sutil
- isAnimationActive={false}
```

### 8.2 Layout (COMPLETO - Refinado)

#### Header.tsx (h-14)

```tsx
// Micro-animações:
- Buttons: h-8 w-8 hover:scale-105 active:scale-95
- transition-all duration-200
- Icons: strokeWidth={2} (definidos)
- Badge notificação: animate-pulse
- Avatar: ring-1 ring-primary-500/20
- Username: text-xs font-semibold leading-none
```

#### Sidebar.tsx (w-64)

```tsx
// Micro-animações:
- Nav items: hover:translate-x-0.5 active:scale-[0.98]
- transition-all duration-200
- Icons: h-4 w-4 strokeWidth={2.5}
- Logo: h-7 w-7 com ring-1 ring-primary-500/20
- Indicador ativo: w-1 h-4 (mais visível)
```

#### Footer.tsx

```tsx
// Simplificado:
- Centralizado, single line
- text-xs com elementos ocultos em mobile
- Separator bullet (•) sutil
- Heart icon: fill-primary-500
```

### 8.3 UI Components Base

#### Card.tsx (COMPLETO)

```tsx
// Refinado:
- rounded-lg border bg-[rgb(var(--card))]
- hover:-translate-y-px hover:shadow-md
- hover:border-[rgb(var(--border))]/50
- transition-all duration-200 ease-out
- CardHeader: px-6 pt-6 pb-4
- CardContent: px-6 pb-5
- Padding padrão: none (controlado por subcomponents)
```

#### Button.tsx

```tsx
// Variants: primary, secondary, ghost, outline, danger
// Sizes: sm, md, lg
// Micro-animações:
- hover:scale-105 active:scale-95
- transition-all duration-200
```

#### Toast.tsx (COMPLETO)

```tsx
// Usando Sonner
- Variants: success, error, info, warning
- Position: top-right
- Auto-dismiss configurável
- Animações suaves
```

---

## <a name="plano-de-implementação"></a>9. PLANO DE IMPLEMENTAÇÃO POR FASES

### ✅ FASE 1: FUNDAÇÃO (Semana 1) - **COMPLETO**

#### 1.1 Setup do Projeto

- ✅ Projeto Vite + React + TypeScript
- ✅ ESLint + Prettier
- ✅ Tailwind CSS
- ✅ Path aliases (@/)

#### 1.2 Design System Base

- ✅ `index.css` com design tokens
- ✅ ThemeProvider + useTheme hook

#### 1.3 Componentes UI Base

- ✅ Button
- ✅ Card (Header, Content, Footer)
- ✅ Toast (Sonner)
- ✅ LoadingSpinner
- ⬜ Input
- ⬜ Badge
- ⬜ Modal
- ⬜ Dropdown
- ⬜ Alert

---

### ✅ FASE 1.5: DASHBOARD INICIAL (Semanas 2-3) - **COMPLETO COM REFINAMENTOS**

#### 1.4 Layout Base

- ✅ Sidebar component (micro-animações)
- ✅ Header component (micro-animações)
- ✅ Footer component (simplificado)
- ✅ AppLayout wrapper

#### 1.5 Dashboard com Visualização de Dados

- ✅ Grid responsivo (md:grid-cols-3) com cards densos
- ✅ PieCharts para Threats/Scans
- ✅ BarCharts para Severity/Activity/Service Usage
- ✅ LineChart para Threat Timeline
- ✅ Card de System Health

#### 1.6 Charts Refinados (Recharts)

- ✅ PieChart com stroke branco (strokeWidth=2)
- ✅ BarChart com contornos (strokeWidth=1.5)
- ✅ LineChart com strokeLinecap="round"
- ✅ AreaChart implementado
- ✅ Grid ultra-sutil (strokeWidth=0.5)
- ✅ Sem animações (isAnimationActive={false})

#### 1.7 Design Refinado (Atenção Cirúrgica)

- ✅ Tipografia precisa (text-[10px], leading-none, tabular-nums)
- ✅ Micro-animações (hover:-translate-y-px, scale-105/95)
- ✅ Profundidade sutil (ring-1 ring-[color]/20)
- ✅ Espaçamentos precisos (gap-3.5, space-y-6, etc)
- ✅ Circles com rings para profundidade

#### 1.8 WebSocket Hook

- ✅ `useWebSocket.ts` com reconnect automático

**Entrega FASE 1.5**: Dashboard inicial COMPLETA com refinamentos cirúrgicos

---

### ⬜ FASE 2: AUTENTICAÇÃO & NAVEGAÇÃO (Semana 4)

#### 2.1 Autenticação

- [ ] AuthContext
- [ ] SecureTokenStore
- [ ] Página `/login`
- [ ] Página `/auth/callback` (OAuth2)
- [ ] Protected routes
- [ ] Testes de auth flow

#### 2.2 Navegação

- [ ] React Router setup completo
- [ ] Route configuration para todas as 45 páginas
- [ ] Navigation menu
- [ ] Active state highlighting
- [ ] Mobile responsive sidebar

**Entrega**: Login funcional + Navegação completa

---

### ⬜ FASE 3: INFRAESTRUTURA DE DADOS (Semana 5)

#### 3.1 HTTP Client

- [ ] `api/client.ts` (retry, auth interceptor)
- [ ] `api/typedClient.ts` (OpenAPI)
- [ ] `endpoints.ts` com todos os 250+ endpoints
- [ ] Setup React Query (se necessário)

#### 3.2 State Management

- [ ] Zustand stores para cada módulo
- [ ] Persistence

**Entrega**: Infraestrutura de dados completa

---

### ⬜ FASE 4: COMPONENTES UI RESTANTES (Semana 6)

#### 4.1 Formulários

- [ ] Input (text, password, email)
- [ ] Select
- [ ] Checkbox, Radio
- [ ] DatePicker, TimePicker
- [ ] File Upload com preview
- [ ] React Hook Form + Zod setup

#### 4.2 Tabelas

- [ ] DataTable genérico (TanStack Table)
- [ ] Paginação
- [ ] Sorting/Filtering
- [ ] Export CSV/JSON

#### 4.3 Outros UI

- [ ] Modal (Header, Content, Footer)
- [ ] Badge (variants)
- [ ] Alert (variants)
- [ ] Dropdown
- [ ] Pagination

**Entrega**: Biblioteca completa de componentes UI

---

### ⬜ FASE 5-6: OFFENSIVE SECURITY (Semanas 7-8)

#### 5.1 Overview Page

- [ ] `/offensive` - Dashboard overview
- [ ] Metrics (scans, vulns, c2, payloads)
- [ ] Recent scans table
- [ ] Quick actions panel

#### 5.2 Network Scanner

- [ ] `/offensive/network-scanner`
- [ ] Form para configurar scan
- [ ] Start scan button
- [ ] Results table
- [ ] Scan details modal

#### 5.3 Vulnerability Scanner

- [ ] `/offensive/vuln-scanner`
- [ ] Scan configuration
- [ ] Results grid
- [ ] Exploit suggestions

#### 5.4 Social Engineering

- [ ] `/offensive/social-eng`
- [ ] Campaign creation
- [ ] Template library
- [ ] Analytics dashboard

#### 5.5 C2 Sessions

- [ ] `/offensive/c2`
- [ ] Active sessions list
- [ ] Session details

#### 5.6 Malware Analysis

- [ ] `/offensive/malware`
- [ ] File upload analyzer
- [ ] Hash lookup
- [ ] URL analyzer

**Entrega**: Módulo Offensive completo (7 páginas)

---

### ⬜ FASE 7-8: DEFENSIVE SECURITY (Semanas 9-10)

#### 7.1 Overview Page

- [ ] `/defensive` - Dashboard overview
- [ ] Alerts summary
- [ ] Behavioral metrics

#### 7.2 Behavioral Analysis

- [ ] `/defensive/behavioral`
- [ ] Event analyzer
- [ ] Batch analysis
- [ ] Baseline training interface

#### 7.3 Traffic Monitor

- [ ] `/defensive/traffic`
- [ ] Real-time traffic graph
- [ ] Anomaly detection

#### 7.4 Alerts Dashboard

- [ ] `/defensive/alerts`
- [ ] Alerts table (filterable)
- [ ] Alert details modal

**Entrega**: Módulo Defensive completo (4 páginas)

---

### ⬜ FASE 9-10: OSINT (Semanas 11-12)

#### 9.1 Overview

- [ ] `/osint` - Dashboard overview

#### 9.2 Google OSINT

- [ ] `/osint/google`
- [ ] 5 tipos de busca
- [ ] Dork patterns library

#### 9.3 Análises Específicas

- [ ] `/osint/email` - Email analysis
- [ ] `/osint/phone` - Phone analysis
- [ ] `/osint/social` - Social media
- [ ] `/osint/image` - Image analysis
- [ ] `/osint/username` - Username search

#### 9.4 Investigation

- [ ] `/osint/investigate` - Comprehensive investigation

**Entrega**: Módulo OSINT completo (8 páginas)

---

### ⬜ FASE 11-12: MAXIMUS AI (Semanas 13-14)

#### 11.1 Core Dashboard

- [ ] `/maximus` - Main dashboard
- [ ] Orchestrator status
- [ ] Eureka discovery
- [ ] Oráculo predictions

#### 11.2 AI Chat

- [ ] `/maximus/chat`
- [ ] Chat interface (estilo Claude.ai)
- [ ] Message history
- [ ] Tools display

#### 11.3 Consciousness Monitor

- [ ] `/maximus/consciousness`
- [ ] Arousal level display
- [ ] ESGT events stream (WebSocket)

#### 11.4 Predictions

- [ ] `/maximus/predictions`
- [ ] Threat predictions
- [ ] Confidence scores

**Entrega**: Módulo Maximus completo (6 páginas)

---

### ⬜ FASE 13-14: IMMUNIS SYSTEM (Semanas 15-16)

#### 13.1 Overview

- [ ] `/immunis` - Dashboard
- [ ] System health
- [ ] Active threats

#### 13.2 Threats Dashboard

- [ ] `/immunis/threats`
- [ ] Threats table
- [ ] Detection timeline

#### 13.3 Immune Agents

- [ ] `/immunis/agents`
- [ ] Agents grid (B-cell, T-cell, etc)
- [ ] Activity logs

#### 13.4 Homeostasis

- [ ] `/immunis/homeostasis`
- [ ] Balance indicators
- [ ] Adjustment controls

#### 13.5 Memory Bank

- [ ] `/immunis/memory`
- [ ] Antibodies library
- [ ] Pattern recognition

**Entrega**: Módulo Immunis completo (5 páginas)

---

### ⬜ FASE 15: REACTIVE FABRIC (Semana 17)

#### 15.1 Overview

- [ ] `/reactive-fabric` - Dashboard

#### 15.2 Threat Timeline

- [ ] Real-time threat timeline (WebSocket)
- [ ] Event filtering

#### 15.3 Intelligence Fusion

- [ ] Multi-source intelligence
- [ ] Correlation engine

#### 15.4 HITL Console

- [ ] Decision queue
- [ ] Approval interface

**Entrega**: Módulo Reactive Fabric completo (4 páginas)

---

### ⬜ FASE 16: SINESP (Semana 18)

#### 16.1 Vehicle Query

- [ ] `/sinesp/veiculos`
- [ ] Plate input
- [ ] Results display

#### 16.2 Crime Heatmap

- [ ] `/sinesp/heatmap`
- [ ] Interactive map

**Entrega**: Módulo SINESP completo (2 páginas)

---

### ⬜ FASE 17: ADMIN & SETTINGS (Semana 19)

#### 17.1 Admin

- [ ] `/admin/users` - User management
- [ ] `/admin/roles` - Roles & permissions

#### 17.2 Settings

- [ ] `/settings/profile` - Profile edit
- [ ] `/settings/preferences` - Preferences
- [ ] `/settings/api-keys` - API keys

**Entrega**: Admin + Settings completo (5 páginas)

---

### ⬜ FASE 18: POLIMENTO & OTIMIZAÇÃO (Semana 20)

#### 18.1 Performance

- [ ] Code splitting por rota
- [ ] Lazy loading
- [ ] Image optimization
- [ ] Bundle size analysis
- [ ] Lighthouse audit (95+ score)

#### 18.2 Acessibilidade

- [ ] WCAG 2.1 AA compliance
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Focus management

#### 18.3 Testes

- [ ] Unit tests (components)
- [ ] Integration tests
- [ ] E2E tests (critical flows)
- [ ] Coverage > 80%

**Entrega**: App production-ready

---

## <a name="progresso-atual"></a>10. PROGRESSO ATUAL

### Status: PRIORIDADE 2 COMPLETA ✅ | Opção B Implementada (65-70 páginas)

**Última Atualização**: 2025-01-16 (18:32 PM)

#### Completado

##### Dashboard Inicial (Refinado)

- ✅ Grid responsivo (md:grid-cols-3) com cards densos
- ✅ PieCharts para Threats e Scans com legendas manuais
- ✅ BarCharts para Threat Severity, Weekly Activity, Service Usage
- ✅ LineChart para Threat Timeline
- ✅ Card de System Health com latências
- ✅ Recharts configurado (sem animações)
- ✅ Cores consistentes: #10b981 (verde), #6b7280 (cinza)

##### Refinamentos de Design (Atenção Cirúrgica)

- ✅ **Contornos brancos finos** em todos os gráficos
  - PieChart: strokeWidth={2}
  - BarChart: strokeWidth={1.5}
  - LineChart/AreaChart: strokeWidth={2.5} com strokeLinecap="round"
- ✅ **Grid ultra-sutil**: strokeWidth={0.5}
- ✅ **Tipografia precisa**:
  - Títulos: text-[10px] uppercase tracking-wider leading-none
  - Números: text-3xl font-bold tabular-nums leading-none
  - Labels: text-[10px] tracking-wider font-medium leading-none
- ✅ **Micro-animações**:
  - Cards: hover:-translate-y-px hover:shadow-md
  - Buttons: hover:scale-105 active:scale-95
  - Nav items: hover:translate-x-0.5 active:scale-[0.98]
- ✅ **Profundidade sutil**:
  - Status circles: ring-1 ring-[color]/20
  - Icons: strokeWidth={2-2.5}
  - Tooltips: boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
- ✅ **Espaçamentos precisos**:
  - Dashboard: space-y-6
  - Grid: gap-3.5
  - Cards internos: gap-4 sm:gap-5
  - Legendas: space-y-2

##### Layout Components (Refinado)

- ✅ Header (h-14) com micro-animações
- ✅ Sidebar (w-64) com micro-animações
- ✅ Footer simplificado e centralizado

##### Sistema de Notificações

- ✅ Toast notifications com Sonner
- ✅ Variantes: success, error, info, warning

##### WebSocket Hook

- ✅ `useWebSocket.ts` com reconnect automático

##### 5 Novos Módulos Críticos (PRIORIDADE 2) - **COMPLETO** ✅

- ✅ **HITL Workflow** (`/hitl`) - Human-in-the-Loop
  - Página principal criada com 4 cards de estatísticas
  - Backend: 6 serviços (Analysis, Planning, Execution, KB, LLM Integration, RAG)
  - Próximo: 5 sub-páginas (Analysis, Planning, Execution, KB, Decisions)

- ✅ **Aurora Orchestrator** (`/aurora`) - Automated Investigation
  - Página principal com 3 cards de estatísticas
  - Backend: 4 endpoints para orquestração de OSINT
  - Próximo: 3 sub-páginas (Active, History, Services)

- ✅ **Digital Thalamus** (`/thalamus`) - Neural Gatekeeper
  - Página principal com latency display
  - Backend: 1 serviço core de roteamento
  - Próximo: 2 sub-páginas (Routes, Metrics)

- ✅ **Narrative Analysis** (`/narrative`) - Manipulation Detection
  - Página principal com detection metrics
  - Backend: 4 serviços (BERTimbau, credibility, propaganda)
  - Próximo: 3 sub-páginas (Detection, Techniques, Reports)

- ✅ **Wargaming & Simulation** (`/wargaming`) - Strategic Planning
  - Página principal com simulation stats
  - Backend: 3 serviços (Crisol, Strategic Planning)
  - Próximo: 2 sub-páginas (Scenarios, Results)

##### Navegação & Routing Expandido

- ✅ **Sidebar reorganizada** por prioridade:
  - P0 Critical: Dashboard, Offensive, Defensive, OSINT, Maximus, Immunis
  - P1 High Priority: HITL, Reactive Fabric, Aurora, Thalamus
  - P2 Medium Priority: Narrative, Wargaming, SINESP
  - Admin: Admin, Settings
- ✅ **6 novos ícones** (Users, Radar, Zap, FileText, Gamepad2)
- ✅ **Router.tsx atualizado** com 5 novas rotas lazy-loaded
- ✅ **Todos os módulos navegáveis** via sidebar

##### Documentação

- ✅ PLANO_MESTRE_FRONTEND.md criado
- ✅ .claude/commands/retomar.md atualizado
- ✅ PLANO_MASTER_COMPLETO.md (este arquivo) - v2.1
- ✅ DASHBOARDS_PROPOSAL.md criado (análise Opção B)

#### Arquivos Criados/Modificados (PRIORIDADE 2)

```
src/pages/HITL/
- HITLPage.tsx          # NOVO - Página principal HITL Workflow

src/pages/Aurora/
- AuroraPage.tsx        # NOVO - Página principal Aurora Orchestrator

src/pages/Thalamus/
- ThalamusPage.tsx      # NOVO - Página principal Digital Thalamus

src/pages/Narrative/
- NarrativePage.tsx     # NOVO - Página principal Narrative Analysis

src/pages/Wargaming/
- WargamingPage.tsx     # NOVO - Página principal Wargaming

src/components/layout/Sidebar/
- Sidebar.tsx           # MODIFICADO - 6 novos itens, reorganizado por prioridade

src/app/
- Router.tsx            # MODIFICADO - 5 novas rotas lazy-loaded

PLANO_MASTER_COMPLETO.md  # MODIFICADO - v2.1 com progresso
DASHBOARDS_PROPOSAL.md    # NOVO - Análise Opção B (65-70 páginas)
```

#### Arquivos Modificados (PRIORIDADE 1)

```
src/components/charts/
- PieChart.tsx          # Ajustado radius, adicionado stroke branco
- BarChart.tsx          # Adicionado stroke branco, refinado grid
- LineChart.tsx         # strokeLinecap/join round
- AreaChart.tsx         # strokeLinecap/join round

src/components/ui/Card/
- Card.tsx              # Micro-animações, padding preciso

src/components/layout/
- Header/Header.tsx     # Micro-animações, sizing preciso
- Sidebar/Sidebar.tsx   # Micro-animações, nav items refinados (P1)
- Footer/Footer.tsx     # Simplificado, centralizado

src/pages/Dashboard/
- DashboardPage.tsx     # Tipografia precisa, espaçamentos, rings

src/index.css           # Design tokens refinados
```

### Próximas Tarefas (PRIORIDADE 3)

**Conforme PLANO_MASTER_COMPLETO v2.1 - Opção B (65-70 páginas)**

#### FASE 11-12: Expandir Maximus AI (1→9 páginas)

1. Maximus Overview (já existe)
2. AI Chat Interface
3. Tool Calling
4. Oracle Predictions
5. Adaptive Security
6. Sentinel Real-time
7. Threat Intelligence
8. Analytics
9. Settings

#### FASE 13-14: Expandir Immunis (1→10 páginas)

1. Immunis Overview (já existe)
2. Threat Detection
3. Behavioral Analysis
4. Anomaly Detection
5. Pattern Recognition
6. ML Models
7. Response Actions
8. Vaccines (Auto-remediation)
9. System Health
10. Reports

#### FASE 15: Implementar HITL Sub-páginas (5 páginas)

1. HITL Overview (✅ já existe)
2. Analysis Queue
3. Planning Board
4. Execution Monitor
5. Knowledge Base
6. Decision History

#### FASE 16: Expandir Reactive Fabric (1→6 páginas)

1. Fabric Overview (já existe)
2. Event Stream
3. Triggers & Rules
4. Orchestration
5. Playbooks
6. Metrics

#### FASE 17-20: Implementar Sub-páginas dos Novos Módulos

- Aurora: Active, History, Services (3 páginas)
- Thalamus: Routes, Metrics (2 páginas)
- Narrative: Detection, Techniques, Reports (3 páginas)
- Wargaming: Scenarios, Results (2 páginas)

---

## <a name="checklist-completo"></a>11. CHECKLIST COMPLETO DE FEATURES

### ✅ Autenticação & Autorização

- [ ] Login com OAuth2 (Google)
- [ ] JWT token management
- [ ] Auto-refresh tokens
- [ ] Protected routes
- [ ] Role-based access (admin, analyst, offensive)
- [ ] Permission checks
- [ ] Cross-tab sync

### ✅ Temas & Design

- ✅ Light mode
- ✅ Dark mode
- ✅ Sistema de design completo
- ✅ Animações sutis e smooth
- ✅ Verde como cor primária (#10b981)
- ✅ Responsive design
- [ ] Accessibility (WCAG 2.1 AA)

### ⬜ Offensive Security (11 endpoints)

- [ ] Network scanning (Nmap)
- [ ] Vulnerability scanning
- [ ] Exploit database search
- [ ] Social engineering campaigns
- [ ] C2 session management
- [ ] Malware analysis (file, hash, URL)
- [ ] Payload generation

### ⬜ Defensive Security (9 endpoints)

- [ ] Behavioral analysis
- [ ] Traffic monitoring
- [ ] Alerts dashboard
- [ ] Baseline training
- [ ] Batch analysis
- [ ] Metrics display

### ⬜ OSINT (17 endpoints total)

- [ ] Google search (5 tipos)
- [ ] Google dorks library
- [ ] Email analysis
- [ ] Phone analysis
- [ ] Social media search
- [ ] Image analysis
- [ ] Username search
- [ ] Comprehensive investigation
- [ ] IP intelligence
- [ ] Domain intelligence

### ⬜ Maximus AI

- [ ] Core dashboard
- [ ] Orchestrator status
- [ ] Eureka service discovery
- [ ] Oráculo predictions
- [ ] AI chat interface
- [ ] Consciousness monitor

### ⬜ Immunis System (14 endpoints)

- [ ] Threats dashboard
- [ ] Immune agents
- [ ] Homeostasis control
- [ ] Lymph nodes
- [ ] Memory bank
- [ ] Metrics & stats

### ⬜ Reactive Fabric

- [ ] Threat timeline (real-time)
- [ ] Intelligence fusion
- [ ] HITL decision console
- [ ] Honeypot status grid

### ⬜ SINESP (Brasil)

- [ ] Consulta de veículos
- [ ] Tipos de ocorrências
- [ ] Heatmap criminal

### ⬜ Admin & Settings

- [ ] User management (CRUD)
- [ ] Role management
- [ ] Permissions matrix
- [ ] Profile settings
- [ ] Preferences
- [ ] API keys

### ✅ Real-time (WebSockets)

- ✅ WebSocket hook implementado
- [ ] Consciousness stream
- [ ] Threat alerts
- [ ] Auto-reconnect

### ⬜ Infraestrutura

- [ ] HTTP client (retry, auth)
- [ ] Type-safe API
- [ ] React Query (opcional)
- [ ] Zustand stores
- [ ] Error boundary
- [ ] Loading states
- [ ] Empty states
- ✅ Toast notifications

---

## <a name="guia-de-estilo"></a>12. GUIA DE ESTILO - MANTER SEMPRE

### Micro-animações Padrão

```tsx
// Botões
className = "transition-all duration-200 hover:scale-105 active:scale-95";

// Cards
className =
  "transition-all duration-200 ease-out hover:-translate-y-px hover:shadow-md";

// Nav Items
className =
  "transition-all duration-200 hover:translate-x-0.5 active:scale-[0.98]";
```

### Tipografia Padrão

```tsx
// Títulos de Card
className = "text-[10px] font-semibold uppercase tracking-wider leading-none";

// Números Grandes
className = "text-3xl font-bold tabular-nums leading-none";

// Labels Pequenos
className = "text-[10px] tracking-wider font-medium leading-none";

// Texto Normal
className = "text-xs font-medium leading-none";
```

### Profundidade Padrão

```tsx
// Círculos/Badges
className = "ring-1 ring-primary-500/20 shadow-sm";

// Cards
className = "shadow-sm hover:shadow-md";

// Tooltips
boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)";
```

### Espaçamentos Padrão

```tsx
// Entre seções
className = "space-y-6";

// Grid de cards
className = "gap-3.5";

// Elementos internos
className = "gap-2.5";

// Padding de cards
CardHeader: "px-6 pt-6 pb-4";
CardContent: "px-6 pb-5";
```

### Gráficos - Configuração Padrão

```tsx
// Grid
<CartesianGrid strokeWidth={0.5} stroke="#e5e7eb" vertical={false} />

// Axes
<XAxis fontSize={10} dy={6} tick={{ fill: '#9ca3af', fontWeight: 500 }} />
<YAxis fontSize={10} dx={-6} width={30} tick={{ fill: '#9ca3af', fontWeight: 500 }} />

// Margins
margin={{ top: 10, right: 10, left: -10, bottom: 0 }}

// Tooltips
contentStyle={{
  backgroundColor: '#ffffff',
  border: '1px solid #e5e7eb',
  borderRadius: '6px',
  fontSize: '12px',
  padding: '6px 10px',
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)'
}}
```

---

## <a name="referências"></a>13. REFERÊNCIAS

### Documentação

- [Recharts Docs](https://recharts.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [React Router](https://reactrouter.com/)
- [Zustand](https://zustand-demo.pmnd.rs/)
- [Sonner (Toasts)](https://sonner.emilkowal.ski/)

### Backend

- **Base URL**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs` (Swagger UI)
- **OpenAPI**: `http://localhost:8000/openapi.json`
- **Total de Endpoints**: 250+
- **Total de Serviços**: 100+

### Análise Completa do Backend

Veja os arquivos na pasta Desktop:

- `BACKEND_COMPLETE_ANALYSIS.md` (977 linhas)
- `ENDPOINTS_DETAILED.md` (459 linhas)
- `BACKEND_ANALYSIS_INDEX.md` (324 linhas)

---

## COMANDOS ÚTEIS

```bash
# Desenvolvimento
npm run dev

# Build
npm run build

# Preview build
npm run preview

# Type check
npm run type-check

# Lint
npm run lint
```

---

## RESUMO EXECUTIVO

### Números do Projeto (REVISADO - OPÇÃO B)

| Métrica                         | Valor Anterior  | **Valor Revisado**   | Diferença  |
| ------------------------------- | --------------- | -------------------- | ---------- |
| **Total de Páginas Planejadas** | 45-50 páginas   | **65-70 páginas** ⭐ | +20 págs   |
| **Backend Endpoints Mapeados**  | 250+ endpoints  | 250+ endpoints       | -          |
| **Backend Services Integrados** | 100+ serviços   | 100+ serviços        | -          |
| **Componentes UI Planejados**   | 30+ componentes | 30+ componentes      | -          |
| **Features Principais**         | 9 módulos       | **15 módulos** ⭐    | +6 módulos |
| **Páginas Completas**           | 1 (Dashboard)   | 1 (Dashboard)        | -          |
| **Fases Totais**                | 18 fases        | **22 fases** ⭐      | +4 fases   |
| **Tempo Estimado Total**        | 20 semanas      | **26-28 semanas** ⭐ | +6-8 sem   |
| **Progresso Atual**             | ~5%             | **~2%** (proporc.)   | -          |

⭐ = Alterado na Revisão (OPÇÃO B escolhida)

### Stack Final

```
Frontend: React 18 + TypeScript + Vite
Styling: Tailwind CSS
UI Base: Custom components
Charts: Recharts
State: Zustand
Auth: OAuth2 + JWT
HTTP: Fetch API
WebSocket: Native API
Icons: Lucide React
Toasts: Sonner
Forms: React Hook Form + Zod (futuro)
Tables: TanStack Table (futuro)
```

### Design Philosophy

```
✅ Clean, Calm, Focused (Claude.ai inspired)
✅ Verde (#10b981) como cor primária
✅ Sans-serif typography
✅ Animações sutis (150-200ms)
✅ Shadows sutis, sem drama
✅ Minimalismo extremo
✅ Atenção cirúrgica aos detalhes
✅ Cada pixel importa
✅ Cada transição encanta
```

---

## PRÓXIMOS PASSOS IMEDIATOS

1. ✅ **COMPLETO**: Dashboard inicial refinado (PRIORIDADE 1)
2. ✅ **COMPLETO**: Documentação master plan
3. ✅ **COMPLETO**: Análise e revisão de dashboards (OPÇÃO B escolhida)
4. ✅ **COMPLETO**: 5 novos módulos criados (HITL, Aurora, Thalamus, Narrative, Wargaming) - PRIORIDADE 2
5. ✅ **COMPLETO**: Sidebar reorganizada por prioridade
6. ✅ **COMPLETO**: Router atualizado com novas rotas
7. **PRÓXIMO**: Expandir Maximus AI (1→9 páginas - FASE 11-12)
8. **PRÓXIMO**: Expandir Immunis (1→10 páginas - FASE 13-14)
9. **PRÓXIMO**: Implementar sub-páginas HITL (5 páginas - FASE 15)

---

## HISTÓRICO DE VERSÕES

### v2.1 - PRIORIDADE 2 COMPLETA (2025-01-16 18:32)

#### Implementado:

- ✅ **5 novos módulos criados** com páginas principais:
  - HITL Workflow (`/hitl`) - Human-in-the-Loop workflow
  - Aurora Orchestrator (`/aurora`) - Automated OSINT investigations
  - Digital Thalamus (`/thalamus`) - Neural signal routing
  - Narrative Analysis (`/narrative`) - Propaganda detection
  - Wargaming & Simulation (`/wargaming`) - Strategic scenarios
- ✅ **Sidebar reorganizada** por prioridade (P0, P1, P2, Admin)
- ✅ **Router atualizado** com 5 novas rotas lazy-loaded
- ✅ **Todos módulos navegáveis** e compilando sem erros

#### Commit:

- `26c03264` - feat(frontend): add 5 new critical modules

### v2.0 - OPÇÃO B ESCOLHIDA (2025-01-16)

#### Planejado:

- ⭐ **+20 páginas** para melhor representação do backend (45-50 → 65-70)
- ⭐ **6 novos módulos** identificados: HITL, Aurora, Thalamus, Narrative, Wargaming, ReactiveFabric expansion
- ⭐ **Expansões**: Maximus (6→9), Immunis (5→10), Reactive Fabric (4→6)
- ⭐ **+4 fases** de implementação adicionadas
- ⭐ **DASHBOARDS_PROPOSAL.md** criado com análise detalhada

#### Justificativa:

O Vértice possui **100+ serviços** e sistemas extremamente complexos como:

- Adaptive Immune System (12 serviços especializados)
- Maximus AI (8 serviços distintos)
- HCL/HITL (6 serviços de workflow)

Dashboards genéricas não fariam jus à arquitetura. A filosofia **"Cada pixel importa"** se aplica também à **arquitetura de dashboards** - cada sistema complexo merece sua dashboard especializada.

#### Commit:

- `b6ca05fc` - docs: add DASHBOARDS_PROPOSAL and update master plan to v2.1

---

**Versão**: 2.1 (PRIORIDADE 2 COMPLETA)
**Data**: 2025-01-16 (18:32 PM)
**Autor**: Claude + Juan
**Status**: 5 novos módulos implementados | 65-70 páginas planejadas | Sidebar reorganizada | Router atualizado
**Filosofia**: "Cada pixel importa. Cada transição encanta. Cada dashboard representa fielmente seu sistema."
**SOLI DEO GLORIA**
