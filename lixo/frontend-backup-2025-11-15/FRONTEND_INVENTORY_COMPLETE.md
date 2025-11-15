# FRONTEND INVENTORY - MIGRAÇÃO DESIGN SYSTEM CLAUDE.AI GREEN

**Data**: 2025-11-14
**Projeto**: VÉRTICE-MAXIMUS
**Missão**: Migração Completa Design System - ZERO Atalhos
**Design Target**: Claude.ai Style com VERDE (não laranja)

---

## 📊 STATUS GERAL

- **Design System Novo**: ✅ CRIADO (`claude-design-green.css`)
- **Componentes UI Base**: ⏳ PENDENTE (reescrever)
- **Layout Components**: ⏳ PENDENTE (reescrever)
- **Widgets/Cards**: ⏳ PENDENTE (reescrever)
- **Pages/Dashboards**: ⏳ PENDENTE (reimplementar)
- **Animações**: ⏳ PENDENTE (recriar)
- **Estados/Feedback**: ⏳ PENDENTE (recriar)

---

## 🎨 DESIGN SYSTEM

### ✅ Criados (DO ZERO)

- `src/styles/claude-design-green.css` - Design system completo Claude.ai GREEN
  - OKLCH color space
  - Verde (#10b981) como primary
  - Typography serif-based
  - Spacing clean e minimalista
  - Shadows sutis
  - Transitions suaves
  - Dark mode support

### 📋 Arquivos Antigos (Para Substituir)

- `src/styles/design-tokens.css` - Sistema vermelho-laranja (SUBSTITUIR)
- `src/styles/themes.css` - Temas antigos (ADAPTAR)
- `src/styles/core-theme.css` - Core antigo (REVISAR)
- `src/styles/utilities.css` - Utilities antigas (ADAPTAR)

---

## 🧩 COMPONENTES UI BASE - PRIORIDADE 1

### CRITICAL: Estes componentes DEVEM ser REESCRITOS DO ZERO

**Localização típica**: `src/components/ui/` ou inline nos dashboards

### Componentes a REESCREVER:

#### ❌ Buttons
- [ ] Button Primary (CTA style Claude.ai)
- [ ] Button Secondary
- [ ] Button Ghost
- [ ] Button Outline
- [ ] Button Icon
- [ ] Button Loading State

#### ❌ Inputs & Forms
- [ ] Input Text
- [ ] Input Number
- [ ] Input Password
- [ ] Textarea
- [ ] Select/Dropdown
- [ ] Checkbox
- [ ] Radio
- [ ] Switch/Toggle
- [ ] Search Input
- [ ] Date Picker
- [ ] Form Labels
- [ ] Form Validation Display

#### ❌ Cards & Containers
- [ ] Card (base component)
- [ ] Card Header
- [ ] Card Body
- [ ] Card Footer
- [ ] StatCard
- [ ] MetricCard
- [ ] InfoCard
- [ ] DashboardCard

#### ❌ Badges & Pills
- [ ] Badge
- [ ] Pill
- [ ] Status Badge
- [ ] Severity Badge

#### ❌ Modals & Overlays
- [ ] Modal (base)
- [ ] Dialog
- [ ] Drawer
- [ ] Popover
- [ ] Tooltip
- [ ] Toast/Notification

#### ❌ Navigation
- [ ] Tabs
- [ ] Breadcrumbs
- [ ] Pagination
- [ ] Menu
- [ ] ContextMenu

#### ❌ Data Display
- [ ] Table
- [ ] DataGrid
- [ ] List
- [ ] Avatar
- [ ] Progress Bar
- [ ] Progress Circle
- [ ] Skeleton Loader

#### ❌ Feedback
- [ ] Alert
- [ ] Toast
- [ ] Spinner
- [ ] Loading Overlay
- [ ] Empty State
- [ ] Error State

---

## 🏗️ LAYOUT COMPONENTS - PRIORIDADE 2

### Componentes a REESCREVER:

#### ❌ Main Layout
- [ ] AppLayout
- [ ] DashboardLayout
- [ ] Container
- [ ] Grid System
- [ ] Flexbox Utilities

#### ❌ Navigation Components
- [ ] Navbar (REESCREVER estilo Claude.ai)
- [ ] Sidebar (REESCREVER estilo Claude.ai chat sidebar)
- [ ] TopBar
- [ ] Header
- [ ] Footer

#### ❌ Sections
- [ ] HeroSection
- [ ] ContentSection
- [ ] FeatureSection

---

## 📊 DASHBOARDS & PAGES - PRIORIDADE 3

### Dashboards a REIMPLEMENTAR:

#### ❌ Admin
- [ ] AdminDashboard
- [ ] HITLConsole
- [ ] AdminHeader

#### ❌ OSINT
- [ ] OSINTDashboard
- [ ] Components específicos

#### ❌ Cyber
- [ ] CyberDashboard
- [ ] Components específicos

#### ❌ Maximus
- [ ] MaximusDashboard
- [ ] ConsciousnessPanel
- [ ] Components específicos

#### ❌ Defensive
- [ ] DefensiveDashboard
- [ ] Components específicos

#### ❌ Offensive
- [ ] OffensiveDashboard
- [ ] Components específicos

#### ❌ Purple Team
- [ ] PurpleTeamDashboard
- [ ] Components específicos

#### ❌ Reactive Fabric
- [ ] ReactiveFabricDashboard
- [ ] Components específicos

#### ❌ MVP
- [ ] MVPDashboard
- [ ] NarrativeFeed
- [ ] StoryCard
- [ ] AnomalyHeatmap
- [ ] SystemPulseVisualization
- [ ] StatsOverview

#### ❌ Landing Page
- [ ] LandingPage
- [ ] HeroSection
- [ ] ModulesSection
- [ ] StatsSection
- [ ] ActivityFeedSection
- [ ] ThreatGlobe
- [ ] LoginModal
- [ ] ThemeToggle
- [ ] AuthBadge

---

## 📈 WIDGETS & SPECIALIZED COMPONENTS - PRIORIDADE 4

### ❌ Charts (Recharts config)
- [ ] LineChart (verde theme)
- [ ] BarChart (verde theme)
- [ ] PieChart (verde theme)
- [ ] AreaChart (verde theme)
- [ ] RadarChart (verde theme)

### ❌ Intelligence Components
- [ ] DeceptionMetricsCard
- [ ] ThreatIntelligenceWidget
- [ ] AlertsWidget

### ❌ Visualization
- [ ] ThreatGlobe
- [ ] NetworkGraph
- [ ] Heatmaps
- [ ] Timeline

---

## 🎭 ANIMAÇÕES & MICRO-INTERAÇÕES - PRIORIDADE 5

### Arquivos a ADAPTAR/RECRIAR:

- [ ] `src/styles/micro-interactions.css` - Adaptar para Claude.ai style
- [ ] Hover effects (subtle, não dramatic)
- [ ] Loading animations (spinner clean)
- [ ] Transition effects (smooth, fast)
- [ ] Skeleton loaders (shimmer effect)
- [ ] Page transitions

---

## 🎨 TEMAS & VARIAÇÕES - PRIORIDADE 6

### Dark Mode
- [ ] Configurar dark mode com OKLCH colors
- [ ] Testar transições smooth
- [ ] Garantir contraste adequado

### Responsive
- [ ] Mobile breakpoints
- [ ] Tablet layouts
- [ ] Desktop optimizations

---

## ✅ CRITÉRIOS DE SUCESSO

### Design Tokens
- [x] OKLCH color space implementado
- [x] Verde como primary (#10b981)
- [x] Serif typography
- [x] Claude.ai spacing
- [x] Subtle shadows
- [x] Smooth transitions
- [x] Dark mode support

### Componentes UI
- [ ] ZERO imports de CSS antigo
- [ ] ZERO referências a cores antigas (#ef4444, #f97316)
- [ ] 100% componentes usando novo design system
- [ ] Hover states Claude.ai style (subtle)
- [ ] Focus states com ring verde
- [ ] Loading states clean
- [ ] Empty states friendly
- [ ] Error states helpful

### Código
- [ ] ZERO hardcoded colors
- [ ] ZERO inline styles com cores antigas
- [ ] 100% CSS variables do novo sistema
- [ ] TypeScript sem erros
- [ ] Build sem warnings críticos

### Visual
- [ ] Indistinguível do Claude.ai (mas verde)
- [ ] Clean, calm, focused
- [ ] Serif typography elegante
- [ ] Spacing consistente
- [ ] Shadows sutis
- [ ] Animations smooth

### Performance
- [ ] Lighthouse Performance ≥95
- [ ] Lighthouse Accessibility ≥95
- [ ] Lighthouse Best Practices ≥95
- [ ] First Contentful Paint <1s
- [ ] Time to Interactive <2s

---

## 🚀 PLANO DE EXECUÇÃO

### FASE 1: ✅ PREPARAÇÃO (COMPLETO)
- [x] Backup
- [x] Branch criada
- [x] Design system criado

### FASE 2: ✅ DESIGN TOKENS (COMPLETO)
- [x] claude-design-green.css criado DO ZERO

### FASE 3: ⏳ COMPONENTES UI BASE (PRÓXIMO)
- [ ] Button → ButtonClaude
- [ ] Input → InputClaude
- [ ] Card → CardClaude
- [ ] Badge → BadgeClaude
- [ ] Modal → ModalClaude
- [ ] (continuar para TODOS)

### FASE 4: ⏳ LAYOUTS
- [ ] Navbar → NavbarClaude
- [ ] Sidebar → SidebarClaude
- [ ] Container → ContainerClaude

### FASE 5: ⏳ WIDGETS
- [ ] StatCard → StatCardClaude
- [ ] Charts → config verde
- [ ] Tables → TableClaude

### FASE 6: ⏳ PAGES
- [ ] Dashboard layouts reimplementados
- [ ] Landing Page atualizada

### FASE 7: ⏳ ANIMAÇÕES
- [ ] Micro-interações Claude.ai
- [ ] Skeleton loaders
- [ ] Transitions

### FASE 8: ⏳ ESTADOS
- [ ] Loading
- [ ] Empty
- [ ] Error

### FASE 9: ⏳ VALIDAÇÃO
- [ ] Visual QA
- [ ] Code review
- [ ] Lighthouse audit
- [ ] Accessibility check

### FASE 10: ⏳ CLEANUP
- [ ] Remover código antigo
- [ ] Commit
- [ ] Push
- [ ] Deploy

---

## 📝 NOTAS IMPORTANTES

### ⚠️ ANTI-PREGUIÇA

**NÃO FAZER:**
- ❌ Find/replace de cores
- ❌ Adaptar componentes antigos
- ❌ Manter estrutura antiga com cores novas
- ❌ Pular componentes "pequenos"
- ❌ Imports de CSS antigo

**FAZER:**
- ✅ REESCREVER componentes DO ZERO
- ✅ Seguir exatamente estilo Claude.ai
- ✅ Verde (#10b981), NÃO laranja (#f97316)
- ✅ Serif typography
- ✅ Clean, calm, focused
- ✅ TODOS componentes, sem exceção

### 🎯 FILOSOFIA

**"Não migre. REIMPLEMENTE."**

Cada componente = pensado do zero como:
"Se eu fosse criar isso no estilo Claude.ai com verde ao invés de laranja, como ficaria?"

NÃO adaptar. REESCREVER.

---

## 📊 TRACKING

Total de Componentes Estimados: **~150+**

- Design Tokens: 1/1 ✅
- UI Base: 0/30 ⏳
- Layouts: 0/10 ⏳
- Dashboards: 0/8 ⏳
- Widgets: 0/20 ⏳
- Pages: 0/15 ⏳
- Animações: 0/10 ⏳
- Estados: 0/5 ⏳

**Progresso Total: 1/~150 (0.67%)**

---

**VERDE, NÃO LARANJA - SOLI DEO GLORIA** 💚
