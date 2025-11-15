# PLANO MESTRE - Frontend Vértice v3.3.1

**Última atualização:** 2025-01-16
**Status:** Dashboard inicial completa com refinamentos de design

---

## FILOSOFIA DE DESIGN

> "Cada transição, cada microanimação, a formação do quadro de código no chat, tudo é milimetricamente detalhado" - Inspirado no Claude Web App

### Princípios Fundamentais

1. **Cuidado Cirúrgico** - Cada pixel importa, cada espaçamento é intencional
2. **Micro-animações Intencionais** - Feedback visual preciso e suave
3. **Tipografia Precisa** - leading-none, tracking calculado, tamanhos exatos
4. **Profundidade Sutil** - Rings, shadows e contornos bem dosados
5. **Minimalismo com Alma** - Clean, mas com identidade única

---

## ✅ PRIORIDADE 1 - COMPLETA

### 1.1 Dashboard com Visualização de Dados

**Arquivos:**

- `src/pages/Dashboard/DashboardPage.tsx`
- `src/components/charts/PieChart.tsx`
- `src/components/charts/BarChart.tsx`
- `src/components/charts/LineChart.tsx`
- `src/components/charts/AreaChart.tsx`

**Implementado:**

- ✅ Grid responsivo (md:grid-cols-3) com cards densos
- ✅ PieCharts para Threats e Scans com legendas manuais
- ✅ BarCharts para Threat Severity, Weekly Activity, Service Usage
- ✅ LineChart para Threat Timeline
- ✅ Card de System Health com latências
- ✅ Recharts como biblioteca principal
- ✅ Sem animações (isAnimationActive={false})
- ✅ Cores consistentes: #10b981 (verde), #6b7280 (cinza)

**Detalhes de Design:**

- Contornos brancos finos em todos os gráficos (stroke="#ffffff")
- PieChart: strokeWidth={2}
- BarChart: strokeWidth={1.5}
- LineChart: strokeWidth={2.5} com strokeLinecap="round"
- Grid com strokeWidth={0.5} (super sutil)
- Tooltips com shadow-sm e border suave

### 1.2 Sistema de Notificações

**Arquivos:**

- `src/components/ui/Toast/Toast.tsx`
- `src/hooks/useToast.ts`

**Implementado:**

- ✅ Toast notifications com Sonner
- ✅ Variantes: success, error, info, warning
- ✅ Auto-dismiss configurável
- ✅ Posicionamento: top-right
- ✅ Animações suaves de entrada/saída

### 1.3 WebSocket Hook

**Arquivos:**

- `src/hooks/useWebSocket.ts`

**Implementado:**

- ✅ Conexão WebSocket com reconnect automático
- ✅ Event listeners tipados
- ✅ Estado de conexão (connecting, connected, disconnected)
- ✅ Cleanup automático no unmount

### 1.4 Design System Refinado

**Arquivos Modificados:**

- `src/components/ui/Card/Card.tsx`
- `src/components/layout/Header/Header.tsx`
- `src/components/layout/Sidebar/Sidebar.tsx`
- `src/components/layout/Footer/Footer.tsx`
- `src/index.css`

**Refinamentos Aplicados:**

#### Cards

- `rounded-lg` (mais preciso que xl)
- `hover:-translate-y-px` (movimento sutil 1px)
- `hover:shadow-md` com `ease-out`
- `hover:border-[rgb(var(--border))]/50`
- CardHeader: `px-6 pt-6 pb-4` (padding consistente)
- CardContent: `px-6 pb-5`
- Padding padrão: `none` (controlado pelos subcomponentes)

#### Tipografia Dashboard

- Títulos dos cards: `text-[10px] uppercase tracking-wider leading-none`
- Números principais: `text-3xl font-bold tabular-nums leading-none`
- Labels: `text-[10px] tracking-wider leading-none`
- Legendas: `text-xs font-medium leading-none`
- Números em legendas: `font-semibold tabular-nums`

#### Círculos de Status

- Todos com `ring-1 ring-[cor]/20` (profundidade sutil)
- Tamanho preciso: `w-2 h-2`
- Sistema Health: `bg-primary-500 ring-1 ring-primary-500/20`

#### Header (h-14)

- Botões: `h-8 w-8` com micro-animações
- `hover:scale-105 active:scale-95` (feedback tátil)
- `transition-all duration-200`
- Ícones: `strokeWidth={2}` (mais definidos)
- Badge notificação: `animate-pulse` (atenção sutil)
- Avatar: `ring-1 ring-primary-500/20`
- Username: `text-xs font-semibold leading-none`

#### Sidebar (w-64)

- Altura alinhada com header: `h-14`
- Nav items: `text-xs font-semibold leading-none`
- `hover:translate-x-0.5` (movimento sutil)
- `active:scale-[0.98]` (feedback de clique)
- Indicador ativo: `w-1 h-4` (mais visível)
- Logo: `h-7 w-7` com `ring-1 ring-primary-500/20`
- Ícones: `h-4 w-4 strokeWidth={2.5}`

#### Footer

- Centralizado em linha única
- `text-xs` com elementos ocultos em mobile (`hidden sm:inline`)
- Separator bullet (•) com cor sutil
- Heart icon com `fill-primary-500`

#### Gráficos - Eixos e Grid

- Grid: `strokeWidth={0.5}` (ultra fino)
- Eixos: `fontSize={10} fontWeight={500}`
- Margens: `top: 10, right: 10, left: -10, bottom: 0`
- YAxis: `width={30}` (espaço preciso)
- Offsets: `dy={6} dx={-6}` (posicionamento milimétrico)
- BarChart: `barGap={6} barCategoryGap="20%"`

#### Espaçamentos Precisos

- Dashboard: `space-y-6`
- Grid: `gap-3.5`
- Cards internos: `gap-4 sm:gap-5`
- Legendas: `space-y-2`
- System Health: `space-y-2.5`

---

## 🔄 PRIORIDADE 2 - PRÓXIMAS TAREFAS

### 2.1 Páginas dos Serviços

**Estrutura:**

```
src/pages/
├── Offensive/
│   └── OffensivePage.tsx
├── Defensive/
│   └── DefensivePage.tsx
├── OSINT/
│   └── OSINTPage.tsx
├── MAXIMUS/
│   └── MAXIMUSPage.tsx
├── Immunis/
│   └── ImmunisPage.tsx
├── ReactiveFabric/
│   └── ReactiveFabricPage.tsx
└── SINESP/
    └── SINESPPage.tsx
```

**Requisitos:**

- Layout consistente com Dashboard
- Título + descrição do serviço
- Métricas específicas de cada serviço
- Logs em tempo real (usar useWebSocket)
- Actions/controls do serviço
- Mesmo nível de cuidado com detalhes

### 2.2 Admin & Settings

**Admin Page:**

- Gerenciamento de usuários
- Logs do sistema
- Configurações de serviços
- Monitoramento de recursos

**Settings Page:**

- Perfil do usuário
- Preferências de tema (já implementado)
- Notificações
- Configurações de segurança

### 2.3 Integrações WebSocket Real

**Tarefas:**

- Conectar Dashboard aos dados reais via WebSocket
- Implementar updates em tempo real nos gráficos
- Sistema de eventos do MAXIMUS
- Notificações push para eventos críticos

### 2.4 Tabelas de Dados

**Componentes Necessários:**

- DataTable genérico com sorting/filtering
- Paginação
- Export CSV/JSON
- Seleção múltipla
- Actions em linha

**Biblioteca Sugerida:**

- TanStack Table (React Table v8)

### 2.5 Formulários

**Componentes Necessários:**

- Form wrapper com validação (React Hook Form)
- Input, Select, Checkbox, Radio
- DatePicker, TimePicker
- File Upload com preview
- Form layouts responsivos

**Biblioteca Sugerida:**

- React Hook Form + Zod

---

## 🎨 GUIA DE ESTILO - MANTER SEMPRE

### Micro-animações Padrão

```tsx
// Botões
className = "transition-all duration-200 hover:scale-105 active:scale-95";

// Cards
className = "transition-all duration-200 hover:-translate-y-px hover:shadow-md";

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

---

## 📊 PALETA DE CORES

### Cores Principais

- **Verde Primary:** `#10b981` (emerald-500)
- **Verde Hover:** `#059669` (emerald-600)
- **Cinza:** `#6b7280` (gray-500)

### Cores de Texto

- **Primary:** `rgb(var(--text-primary))` - #09090B
- **Secondary:** `rgb(var(--text-secondary))` - #64748B (slate-500)
- **Tertiary:** `rgb(var(--text-tertiary))` - #94A3B8 (slate-400)

### Cores de Background

- **Background:** `rgb(var(--background))` - #FAFAFA
- **Card:** `rgb(var(--card))` - #FFFFFF
- **Border:** `rgb(var(--border))` - #E5E7EB

### Cores Semânticas

- **Success:** `#10b981` (verde)
- **Warning:** `#F59E0B` (amber)
- **Danger:** `#EF4444` (red)
- **Info:** `#3B82F6` (blue)

---

## 🛠️ STACK TÉCNICA

### Core

- React 18
- TypeScript
- Vite
- React Router v6

### UI

- Tailwind CSS
- Recharts (gráficos)
- Lucide React (ícones)
- Sonner (toasts)

### Estado

- Zustand (UI state)
- React Context (Auth)

### Networking

- Native WebSocket API
- Fetch API

### Utilities

- clsx + tailwind-merge (cn)
- class-variance-authority (variantes)

---

## 📁 ESTRUTURA DE PASTAS

```
frontend/
├── src/
│   ├── components/
│   │   ├── charts/          # Componentes de gráfico
│   │   ├── layout/          # Header, Sidebar, Footer
│   │   └── ui/              # Componentes base (Card, Button, etc)
│   ├── hooks/               # Custom hooks
│   ├── lib/                 # Utilities
│   │   ├── auth/            # Context de autenticação
│   │   └── utils.ts         # cn() e outros
│   ├── pages/               # Páginas da aplicação
│   ├── stores/              # Zustand stores
│   ├── App.tsx              # App principal
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles + design tokens
├── public/
├── .claude/
│   └── commands/
│       └── retomar.md       # Este comando
├── PLANO_MESTRE_FRONTEND.md # Este arquivo
└── package.json
```

---

## 🚀 COMANDOS ÚTEIS

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

## 📝 NOTAS IMPORTANTES

### Sobre Responsividade

- Mobile first approach
- Breakpoints: sm (640px), md (768px), lg (1024px)
- Grid: `grid-cols-1 md:grid-cols-3`
- Flex: `flex-col sm:flex-row`
- Texto: `text-xl sm:text-2xl`
- Hide/Show: `hidden sm:inline`

### Sobre Animações

- Sempre usar `transition-all duration-200 ease-out`
- Micro-animações sutis (scale, translate em px)
- Sem animações nos gráficos (performance)
- Feedback visual em todos os interativos

### Sobre Acessibilidade

- Sempre usar tags semânticas
- aria-labels quando necessário
- Focus states com ring-2
- Contrast ratio adequado
- Keyboard navigation

### Sobre Performance

- Lazy loading de páginas
- Memoização de componentes pesados
- Debounce em inputs
- Virtual scrolling em listas grandes
- Code splitting por rota

---

## 🎯 PRÓXIMOS MILESTONES

1. **Milestone 2:** Páginas de Serviços (Offensive, Defensive, OSINT, etc)
2. **Milestone 3:** Admin & Settings completos
3. **Milestone 4:** Integrações WebSocket reais
4. **Milestone 5:** Sistema de tabelas e formulários
5. **Milestone 6:** Testes E2E e otimizações finais

---

## 🔗 REFERÊNCIAS

- [Recharts Docs](https://recharts.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Lucide Icons](https://lucide.dev/)
- [React Router](https://reactrouter.com/)
- [Zustand](https://zustand-demo.pmnd.rs/)

---

**Versão:** 1.0
**Data:** 2025-01-16
**Autor:** Claude + Juan
**Filosofia:** "Cada pixel importa. Cada transição encanta."
