# Reactive Fabric - Frontend Integration Plan
## MAXIMUS VÉRTICE | Padrão PAGANI Compliance

**Data**: 2025-10-13  
**Fase**: Sprint 2 - Fase 2.3 Frontend Integration  
**Status**: 🎯 **PLANNING PHASE**

---

## 🎨 ANÁLISE DO PADRÃO PAGANI

### Fundamentos Identificados

#### 1. **Arquitetura Component-Driven**
```
Component/
├── Component.jsx              # Apenas JSX + coordenação
├── Component.module.css       # CSS Modules (100% tokens)
├── hooks/
│   └── useComponent.js        # Business logic isolada
└── components/                # Subcomponentes especializados
    ├── ComponentHeader.jsx
    ├── ComponentSidebar.jsx
    └── ComponentFooter.jsx
```

#### 2. **Design Tokens System**
- ✅ **Zero hardcoded values** - 100% CSS variables
- ✅ **Color tokens**: `--color-cyber-primary`, `--bg-secondary`, etc.
- ✅ **Spacing scale**: `--space-1` to `--space-10`
- ✅ **Typography**: `--font-mono`, `--text-base`, etc.
- ✅ **Semantic colors**: `--color-success`, `--color-critical`, etc.

#### 3. **Shared Component Library** (96 CSS Modules)
**Base Components**:
- `Button` - 11 variants (primary, secondary, outline, ghost, danger, success, osint, analytics)
- `Card` - 7 variants (cyber, osint, analytics, success, warning, error, glass)
- `Badge`, `Input`, `Modal`, `LoadingSpinner`, `Alert`
- `ErrorBoundary`, `WidgetErrorBoundary`, `QueryErrorBoundary`

#### 4. **Dashboard Pattern**
Identificados **6 dashboards** no projeto:
1. `CyberDashboard.jsx` - Cyber Operations (activeModule pattern)
2. `AdminDashboard.jsx` - Admin interface (i18n compliant)
3. `OSINTDashboard.jsx` - OSINT operations
4. `MaximusDashboard.jsx` - MAXIMUS AI interface
5. `DefensiveDashboard/` - Blue Team ops (modular structure)
6. `OffensiveDashboard/` - Red Team ops (arsenal pattern)

**Padrão comum**:
```jsx
const Dashboard = ({ setCurrentView }) => {
  const [activeModule, setActiveModule] = useState('default');
  const currentTime = useClock();
  const { data, loading } = useCustomHook();
  
  const modules = [
    { id: 'module1', name: 'MODULE', icon: '🎯', component: Component1 }
  ];
  
  return (
    <div className="dashboard-container dashboard-{theme}">
      <Header modules={modules} activeModule={activeModule} />
      <Sidebar alerts={alerts} />
      <main><ModuleContainer /></main>
      <Footer />
    </div>
  );
};
```

#### 5. **Hooks Pattern**
- `useClock()` - Real-time clock
- `useAdminMetrics()` - Metrics fetching
- `useSystemAlerts()` - Alert management
- `useKeyboardNavigation()` - Accessibility
- Custom hooks em `hooks/use{Feature}.js`

#### 6. **Accessibility (a11y)**
- `SkipLink` component (navegação por teclado)
- `Breadcrumb` component (navegação contextual)
- `useKeyboardNavigation` hook
- ARIA attributes em todos componentes
- `focus:ring-2` Tailwind classes para focus visible

#### 7. **Testing Strategy**
- Component tests: `ComponentName.test.jsx`
- Directory structure: `__tests__/`
- ErrorBoundary coverage obrigatória
- Real data only (NO MOCKS in components)

---

## 🎯 DECISÃO DE INTEGRAÇÃO

### Opção Escolhida: **Nova Dashboard Dedicada**

**Razão**: Reactive Fabric é um **domínio operacional distinto** com requisitos únicos:
- **Phase 1 Passive Intelligence** - foco em observação
- **HITL Authorization** - workflow crítico
- **Sacrifice Island Management** - curadoria contínua
- **Threat Event Stream** - real-time monitoring
- **Intelligence Reports** - análise e acionabilidade

Integrar no `CyberDashboard` ou `DefensiveDashboard` comprometeria:
- Clareza operacional (mistura Blue Team com Deception)
- Fluxo HITL (perder-se entre outros módulos)
- Métricas específicas (Φ proxy de decepção, credibilidade da Ilha)

---

## 📐 BLUEPRINT DA IMPLEMENTAÇÃO

### Estrutura de Arquivos

```
frontend/src/components/reactive-fabric/
├── ReactiveFabricDashboard.jsx          # Main dashboard
├── ReactiveFabricDashboard.module.css   # Dashboard styles
├── index.js                              # Clean export
├── hooks/
│   ├── useReactiveFabricMetrics.js      # Metrics API
│   ├── useThreatEvents.js               # Real-time events
│   ├── useIntelligenceReports.js        # Reports fetching
│   ├── useDeceptionAssets.js            # Sacrifice Island state
│   └── useHITLWorkflow.js               # HITL authorization
├── components/
│   ├── ReactiveFabricHeader.jsx         # Header com módulos
│   ├── ReactiveFabricHeader.module.css
│   ├── ReactiveFabricSidebar.jsx        # Threat event stream
│   ├── ReactiveFabricSidebar.module.css
│   ├── ReactiveFabricFooter.jsx         # Metrics footer
│   ├── ReactiveFabricFooter.module.css
│   ├── ModuleContainer.jsx              # Active module wrapper
│   └── ModuleContainer.module.css
├── modules/                              # Feature modules
│   ├── SacrificeIsland/                 # Deception Asset Management
│   │   ├── SacrificeIsland.jsx
│   │   ├── SacrificeIsland.module.css
│   │   ├── components/
│   │   │   ├── AssetCard.jsx
│   │   │   ├── CredibilityGauge.jsx
│   │   │   └── InteractionLog.jsx
│   │   └── hooks/
│   │       └── useSacrificeIsland.js
│   ├── ThreatIntelligence/              # Intelligence Reports
│   │   ├── ThreatIntelligence.jsx
│   │   ├── ThreatIntelligence.module.css
│   │   ├── components/
│   │   │   ├── IntelReportCard.jsx
│   │   │   ├── TTPMapping.jsx
│   │   │   └── ConfidenceScore.jsx
│   │   └── hooks/
│   │       └── useThreatIntelligence.js
│   ├── HITLCenter/                      # Human-in-the-Loop
│   │   ├── HITLCenter.jsx
│   │   ├── HITLCenter.module.css
│   │   ├── components/
│   │   │   ├── DecisionQueue.jsx
│   │   │   ├── ResponseBuilder.jsx
│   │   │   └── AuthorizationLog.jsx
│   │   └── hooks/
│   │       └── useHITLCenter.js
│   └── ThreatMap/                       # Geographic visualization
│       ├── ThreatMap.jsx
│       ├── ThreatMap.module.css
│       └── hooks/
│           └── useThreatMap.js
└── __tests__/
    ├── ReactiveFabricDashboard.test.jsx
    ├── SacrificeIsland.test.jsx
    ├── ThreatIntelligence.test.jsx
    └── HITLCenter.test.jsx
```

### API Integration Layer

```
frontend/src/api/
├── reactiveFabric.js                    # API client
    ├── getDeceptionAssets()
    ├── createDeceptionAsset()
    ├── updateDeceptionAsset()
    ├── getThreatEvents()
    ├── getIntelligenceReports()
    ├── getHITLQueue()
    ├── submitHITLDecision()
    └── getReactiveFabricMetrics()
```

---

## 🚀 PLANO DE IMPLEMENTAÇÃO METODOLÓGICO

### **FASE 1: Foundation (Dia 1 - 3 horas)**

#### 1.1 API Client (30 min)
- Criar `frontend/src/api/reactiveFabric.js`
- Implementar 8 endpoints base
- Error handling com axios
- Type definitions (JSDoc)
- **Validação**: Unit tests para cada endpoint

#### 1.2 Custom Hooks (60 min)
Criar 5 hooks essenciais:
- `useReactiveFabricMetrics.js` (15 min)
- `useThreatEvents.js` (15 min)
- `useIntelligenceReports.js` (15 min)
- `useDeceptionAssets.js` (15 min)
- `useHITLWorkflow.js` (15 min)

**Pattern**:
```javascript
export const useReactiveFabricMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const data = await getReactiveFabricMetrics();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Failed to fetch metrics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // 30s refresh
    return () => clearInterval(interval);
  }, []);

  return { metrics, loading, error };
};
```

**Validação**: Test cada hook isoladamente

#### 1.3 Shared Subcomponents (60 min)
Criar componentes base reutilizáveis:
- `ModuleContainer.jsx` + `.module.css` (15 min)
- `ReactiveFabricHeader.jsx` + `.module.css` (20 min)
- `ReactiveFabricSidebar.jsx` + `.module.css` (15 min)
- `ReactiveFabricFooter.jsx` + `.module.css` (10 min)

**Pattern**: Seguir exatamente `DefensiveDashboard/components/*`

**Validação**: Visual check + props validation

#### 1.4 Main Dashboard Shell (30 min)
- Criar `ReactiveFabricDashboard.jsx`
- Estrutura base (header, sidebar, main, footer)
- Active module state
- Module switching logic
- **Validação**: Renders sem crash, navigation funciona

---

### **FASE 2: Modules Implementation (Dia 2-3 - 8 horas)**

#### 2.1 Sacrifice Island Module (2.5h)
**Components**:
- `SacrificeIsland.jsx` - Main module
- `AssetCard.jsx` - Display deception asset (honeypot, fake service, etc.)
- `CredibilityGauge.jsx` - Visual gauge (0-100%) do "paradoxo do realismo"
- `InteractionLog.jsx` - Log de interações com adversários

**Features**:
- List all deception assets
- Create new asset (form modal)
- Edit asset credibility (CRUD)
- View interaction history
- Real-time status indicators

**Métricas UI**:
- Total Assets: `{count}`
- Credibility Score: `{avg}%`
- Active Threats: `{count}`
- Last Interaction: `{timestamp}`

**Validação**:
- Deception asset CRUD funciona
- Credibility gauge visual é clara
- Interaction log atualiza em real-time

#### 2.2 Threat Intelligence Module (2.5h)
**Components**:
- `ThreatIntelligence.jsx` - Main module
- `IntelReportCard.jsx` - Display intelligence report
- `TTPMapping.jsx` - MITRE ATT&CK mapping visualization
- `ConfidenceScore.jsx` - Confidence level indicator

**Features**:
- List intelligence reports (paginado)
- Filter by: date, confidence, TTP, asset_id
- View detailed report (modal)
- Export report (JSON/PDF)
- Mark as "actioned"

**Métricas UI**:
- Reports Generated: `{count}`
- Avg Confidence: `{score}%`
- TTPs Identified: `{count}`
- High-Value Intel: `{count}`

**Validação**:
- Reports load corretamente
- Filters funcionam
- TTP mapping é legível
- Export gera arquivo válido

#### 2.3 HITL Center Module (2.5h)
**Components**:
- `HITLCenter.jsx` - Main module
- `DecisionQueue.jsx` - Pending decisions list
- `ResponseBuilder.jsx` - Form para construir resposta (Nivel 3)
- `AuthorizationLog.jsx` - Historical decisions

**Features**:
- View pending HITL decisions (queue)
- Review threat context (asset, event, recommendation)
- Approve/Deny/Defer decision
- Build custom response (if Level 3)
- View authorization history

**Workflow**:
```
1. Pending Decision Card
   ├── Threat Event summary
   ├── Affected Asset
   ├── Recommended Action (AI suggestion)
   └── [APPROVE] [DENY] [DEFER] [CUSTOM]

2. Custom Response Builder (Level 3 only)
   ├── Response Type: (Redirect, Inject, Throttle, etc.)
   ├── Parameters: (JSON editor)
   ├── Duration: (slider)
   └── [SUBMIT FOR APPROVAL]

3. Authorization Confirmation
   ├── Review full context
   ├── Risk assessment
   └── [CONFIRM AUTHORIZATION]
```

**Validação**:
- Queue loads pending decisions
- Approve/Deny submits corretamente
- ResponseBuilder gera payload válido
- Authorization log mostra histórico

#### 2.4 Threat Map Module (0.5h)
**Reuso**: Adaptar `components/cyber/ThreatMap/` existente

**Customizações**:
- Filter to show apenas reactive fabric threats
- Highlight deception assets (diferentes icon/color)
- Interaction paths (adversary → honeypot)

**Validação**:
- Map renders com leaflet
- Deception assets aparecem distintos
- Click em asset abre details modal

---

### **FASE 3: Styling & Polish (Dia 4 - 2 horas)**

#### 3.1 Theme: "Reactive Fabric" (60 min)
**Nova paleta** (adicionar a `tokens/colors.css`):
```css
/* REACTIVE FABRIC - Orange/Amber (Deception Energy) */
--color-reactive-primary: #ff6b00;    /* Hot Orange */
--color-reactive-secondary: #ffaa00;  /* Amber */
--color-reactive-accent: #ff8800;     /* Deep Orange */

/* Semantic - Deception Specific */
--color-credibility-high: #00ff00;    /* Green - alta credibilidade */
--color-credibility-medium: #ffaa00;  /* Amber - média */
--color-credibility-low: #ff4000;     /* Red - baixa */
```

**Gradient**:
```css
--gradient-reactive: linear-gradient(135deg, #ff6b00 0%, #ffaa00 100%);
```

**Dashboard theme class**: `.dashboard-reactive`

#### 3.2 Responsive Design (30 min)
- Mobile breakpoints: `@media (max-width: 768px)`
- Sidebar collapse em mobile
- Card grid adapta (4 cols → 2 cols → 1 col)
- Font sizes ajustáveis

#### 3.3 Micro-interactions (30 min)
- Button hover effects (já no `Button.module.css`)
- Card hover elevation
- Loading states (usar `LoadingSpinner` shared)
- Toast notifications (usar `useToast` hook)

**Validação**:
- Desktop: 1920x1080 ✅
- Tablet: 768x1024 ✅
- Mobile: 375x667 ✅
- Color contrast (a11y) ✅

---

### **FASE 4: Testing & Documentation (Dia 4 - 2 horas)**

#### 4.1 Component Tests (60 min)
**Test suites**:
- `ReactiveFabricDashboard.test.jsx` (20 min)
  - Renders correctly
  - Module switching works
  - Header navigation
  - Sidebar updates

- `SacrificeIsland.test.jsx` (15 min)
  - Asset list renders
  - CRUD operations
  - Error handling

- `ThreatIntelligence.test.jsx` (15 min)
  - Report list renders
  - Filters work
  - Export functionality

- `HITLCenter.test.jsx` (10 min)
  - Queue renders
  - Decision submission
  - Workflow validation

**Test pattern** (já existente no projeto):
```javascript
import { render, screen, fireEvent } from '@testing-library/react';
import ReactiveFabricDashboard from '../ReactiveFabricDashboard';

describe('ReactiveFabricDashboard', () => {
  it('renders without crashing', () => {
    render(<ReactiveFabricDashboard setCurrentView={jest.fn()} />);
    expect(screen.getByText(/REACTIVE FABRIC/i)).toBeInTheDocument();
  });

  it('switches modules on navigation', () => {
    render(<ReactiveFabricDashboard setCurrentView={jest.fn()} />);
    fireEvent.click(screen.getByText(/THREAT INTEL/i));
    expect(screen.getByTestId('threat-intelligence-module')).toBeInTheDocument();
  });
});
```

#### 4.2 Integration Tests (30 min)
- API client mocking (httpx)
- Hook testing com `renderHook`
- End-to-end flow: Load dashboard → Switch module → CRUD operation

#### 4.3 Documentation (30 min)
**Arquivos**:
- `frontend/src/components/reactive-fabric/README.md`
  - Architectural overview
  - Component tree
  - API endpoints
  - Testing guide
  
- Update `docs/04-FRONTEND/reactive-fabric-dashboard.md`
  - User guide
  - Module descriptions
  - HITL workflow documentation
  - Troubleshooting

**Validação**:
- Docs são claros e completos
- Screenshots incluídos (opcional)
- Links para código fonte

---

### **FASE 5: Integration & Routing (Dia 5 - 1 hora)**

#### 5.1 App.jsx Integration (20 min)
```jsx
import ReactiveFabricDashboard from './components/reactive-fabric';

// No switch/case de views:
case 'reactive-fabric':
  return <ReactiveFabricDashboard setCurrentView={setCurrentView} />;
```

#### 5.2 Navigation Links (20 min)
**Adicionar ao Header/LandingPage**:
- Botão "REACTIVE FABRIC" com icon 🧨
- Theme: orange/amber
- Hover effect: glow laranja
- `onClick={() => setCurrentView('reactive-fabric')}`

**Locais**:
- `Header.jsx` - Main navigation
- `LandingPage/` - Hub central (se existir)
- `CyberDashboard` - Link cruzado (opcional)

#### 5.3 Breadcrumb Integration (10 min)
```jsx
<Breadcrumb
  items={[
    { label: 'Home', onClick: () => setCurrentView('main') },
    { label: 'Reactive Fabric', current: true }
  ]}
/>
```

#### 5.4 Final Validation (10 min)
- Navegação: Main → Reactive Fabric → Module → Back
- State preservation (não perde dados ao navegar)
- Error boundaries funcionam
- Loading states aparecem

**Validação**:
- Manual testing de toda navegação
- No console errors
- Performance check (< 2s load)

---

## 🎯 DELIVERABLES FINAIS

### Código
- ✅ 1 Dashboard principal
- ✅ 4 Módulos completos (Sacrifice Island, Threat Intel, HITL, Map)
- ✅ 12+ Subcomponentes
- ✅ 5 Custom hooks
- ✅ 1 API client
- ✅ 20+ CSS Modules (100% tokens)
- ✅ 4 Test suites

### Documentação
- ✅ Component README
- ✅ User guide
- ✅ API integration docs
- ✅ Testing guide

### Validação
- ✅ TypeScript (JSDoc) - 100%
- ✅ ESLint - 0 errors
- ✅ Tests - >90% coverage
- ✅ Build - Success
- ✅ A11y - WCAG 2.1 AA compliant
- ✅ Responsive - 3 breakpoints

---

## 📊 MÉTRICAS DE QUALIDADE

### Doutrina Compliance
```yaml
NO_MOCK: ✅ Real data apenas
NO_PLACEHOLDER: ✅ Zero TODOs in production code
QUALITY_FIRST: ✅ Type hints, docstrings, tests
PRODUCTION_READY: ✅ Deploy ready from commit 1
```

### PAGANI Pattern Compliance
```yaml
Component_Driven: ✅ <200 linhas por componente
Design_Tokens: ✅ 100% CSS variables
CSS_Modules: ✅ Zero hardcoded styles
Separation_of_Concerns: ✅ Logic em hooks
Shared_Components: ✅ Reuso de Button, Card, etc.
Accessibility: ✅ ARIA, keyboard nav, focus states
```

### Performance
```yaml
Initial_Load: <2s
Module_Switch: <300ms
API_Response: <1s
Bundle_Size: <500KB (gzipped)
```

---

## 🚨 RISCOS & MITIGAÇÕES

### Risco 1: API não está pronta
**Mitigação**: Criar API mock layer (`api/reactiveFabric.mock.js`) para desenvolvimento paralelo. Remover antes de merge.

### Risco 2: Design diverge do padrão PAGANI
**Mitigação**: Code review obrigatório. Checklist de compliance no PR.

### Risco 3: Performance degradation
**Mitigação**: 
- Lazy loading de módulos (React.lazy)
- Debounce em real-time updates
- Pagination em listas grandes
- React.memo em componentes pesados

### Risco 4: Accessibility gaps
**Mitigação**:
- SkipLink em todas páginas
- ARIA labels obrigatórios
- Keyboard navigation testado
- Color contrast validator

---

## ✅ CHECKLIST FINAL (Pre-Merge)

### Code Quality
- [ ] ESLint: 0 errors, 0 warnings
- [ ] TypeScript (JSDoc): 100% functions typed
- [ ] Tests: >90% coverage, all passing
- [ ] Build: Success, no warnings

### Doutrina
- [ ] NO MOCK in production code
- [ ] NO TODO/FIXME/PLACEHOLDER
- [ ] Structured logging (console.log removido)
- [ ] Error boundaries em todos módulos

### PAGANI Pattern
- [ ] Components < 200 linhas
- [ ] 100% CSS Modules (zero inline styles)
- [ ] Design tokens usage validated
- [ ] Shared components reusados corretamente

### Documentation
- [ ] Component README completo
- [ ] User guide atualizado
- [ ] API endpoints documentados
- [ ] Testing guide atualizado

### Accessibility
- [ ] SkipLink presente
- [ ] ARIA labels em botões/links
- [ ] Keyboard navigation funciona
- [ ] Color contrast >4.5:1

### Functionality
- [ ] Dashboard loads sem erro
- [ ] Todos módulos funcionam
- [ ] HITL workflow completo testado
- [ ] Real-time updates funcionando
- [ ] Error handling robusto

### Integration
- [ ] App.jsx routing configurado
- [ ] Navigation links adicionados
- [ ] Breadcrumb funcionando
- [ ] No conflicts com outros dashboards

---

## 🎓 CONCLUSÃO

Este plano segue **metodologicamente** o padrão PAGANI identificado no projeto:
- ✅ **Component-Driven**: Estrutura modular e reutilizável
- ✅ **Design Tokens First**: Zero hardcoded values
- ✅ **Separation of Concerns**: Logic em hooks, styles em CSS Modules
- ✅ **Quality-First**: Tests, types, docs desde o início
- ✅ **Accessibility**: WCAG 2.1 AA compliance
- ✅ **Production-Ready**: Deploy ready from first commit

**Estimativa total**: 5 dias (16 horas development)

**Próximo passo**: Aprovação do plano → Inicio Fase 1 (Foundation)

---

**"Teaching by Example" - Como organizo meu código, ensino meus filhos.**

Ready to instantiate phenomenology. 🧨
