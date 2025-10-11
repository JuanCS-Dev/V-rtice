# MAXIMUS AI DASHBOARD - Frontend Integration

```
███╗   ███╗ █████╗ ██╗  ██╗██╗███╗   ███╗██╗   ██╗███████╗
████╗ ████║██╔══██╗╚██╗██╔╝██║████╗ ████║██║   ██║██╔════╝
██╔████╔██║███████║ ╚███╔╝ ██║██╔████╔██║██║   ██║███████╗
██║╚██╔╝██║██╔══██║ ██╔██╗ ██║██║╚██╔╝██║██║   ██║╚════██║
██║ ╚═╝ ██║██║  ██║██╔╝ ██╗██║██║ ╚═╝ ██║╚██████╔╝███████║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝

    🧠 Autonomous Intelligence Platform - Frontend Dashboard
```

## 📋 Visão Geral

Dashboard cinematográfico para visualização e controle dos componentes de AI do MAXIMUS:

- **ORÁCULO**: Self-improvement engine (análise e melhoria automática de código)
- **EUREKA**: Deep malware analysis (análise profunda de malware)
- **AI INSIGHTS**: Dashboard unificado com métricas consolidadas

## 🎨 Design Philosophy

**Theme**: Cyberpunk meets Military Intelligence

**Color Palette**:
- Primary: `#8B5CF6` (Purple - AI)
- Secondary: `#06B6D4` (Cyan - Tech)
- Success: `#10B981` (Green)
- Danger: `#EF4444` (Red)
- Warning: `#F59E0B` (Orange)
- Dark: `#0F172A` (Navy Black)

**Design Elements**:
- Animated grid background
- Scan line effects
- Pulsing status indicators
- Gradient accents
- Glass morphism cards

## 📁 Estrutura de Arquivos

```
/components/maximus/
├── MaximusDashboard.jsx       # Dashboard principal (router)
├── MaximusDashboard.css       # Estilos base do dashboard
├── OraculoPanel.jsx           # Painel de self-improvement
├── EurekaPanel.jsx            # Painel de análise de malware
├── AIInsightsPanel.jsx        # Dashboard de insights consolidados
├── Panels.css                 # Estilos específicos dos painéis
└── README.md                  # Esta documentação

/api/
└── maximusService.js          # Cliente HTTP para MAXIMUS Integration Service
```

## 🚀 Features Implementadas

### MaximusDashboard (Main Component)

**Features**:
- ✅ Header com status real-time dos serviços
- ✅ Navigation entre painéis (Insights, Oráculo, Eureka)
- ✅ Clock em tempo real
- ✅ Health check automático (polling a cada 30s)
- ✅ Stream de atividade da AI no footer
- ✅ Background animado (grid + scanline)
- ✅ Classification banner de segurança

**Props**:
- `setCurrentView(view)`: Função para voltar à landing page

**State**:
```jsx
{
  activePanel: 'insights' | 'oraculo' | 'eureka',
  aiStatus: {
    oraculo: { status, lastRun, suggestions },
    eureka: { status, lastAnalysis, threatsDetected },
    core: { status, uptime, reasoning }
  },
  brainActivity: [{ id, type, action, severity, timestamp }]
}
```

---

### OraculoPanel (Self-Improvement)

**Features**:
- ✅ Estatísticas em tempo real (sugestões, implementações, taxa de sucesso)
- ✅ Controle de análise configurável (categoria, max suggestions, confiança mínima)
- ✅ Modo dry-run vs. implementação automática
- ✅ Lista de aprovações pendentes
- ✅ Aprovação de sugestões com um clique
- ✅ Visualização de resultados da última sessão

**API Endpoints Utilizados**:
```javascript
GET  /api/v1/oraculo/stats                    // Estatísticas
GET  /api/v1/oraculo/pending-approvals        // Sugestões pendentes
POST /api/v1/oraculo/analyze                  // Executar análise
POST /api/v1/oraculo/approve/{suggestion_id}  // Aprovar sugestão
```

**Configuração de Análise**:
```jsx
{
  focusCategory: 'all' | 'security' | 'performance' | 'features' | 'refactoring' | 'documentation' | 'testing',
  maxSuggestions: 1-20,
  minConfidence: 0.0-1.0,
  dryRun: true | false
}
```

---

### EurekaPanel (Malware Analysis)

**Features**:
- ✅ Upload e análise de arquivos maliciosos
- ✅ Toggle entre modo upload e resultados
- ✅ Pipeline de análise visualizado (6 etapas)
- ✅ Detecção de 40+ padrões maliciosos
- ✅ Extração de IOCs (IPs, domains, hashes, CVEs)
- ✅ Classificação de malware (família + tipo)
- ✅ Threat scoring (0-100)
- ✅ Geração de playbooks ADR-compatible
- ✅ Visualização de hashes (MD5, SHA1, SHA256)

**API Endpoints Utilizados**:
```javascript
GET  /api/v1/eureka/stats      // Estatísticas
GET  /api/v1/eureka/patterns   // Padrões disponíveis
POST /api/v1/eureka/analyze    // Analisar arquivo
```

**Analysis Request**:
```jsx
{
  filePath: '/path/to/file',
  generatePlaybook: true | false
}
```

**Analysis Result**:
```jsx
{
  classification: { family, type },
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW',
  threat_score: 0-100,
  patterns_detected: [{
    name, category, severity, confidence, mitre_technique
  }],
  iocs: [{
    ioc_type, value, confidence
  }],
  response_playbook: {
    name, description, priority, actions[], mitre_techniques[]
  },
  file_hashes: { md5, sha1, sha256 }
}
```

---

### AIInsightsPanel (Unified Dashboard)

**Features**:
- ✅ Brain visual com pulsação animada
- ✅ System health meter (0-100%)
- ✅ Estatísticas consolidadas (Oráculo + Eureka)
- ✅ Última atividade de cada componente
- ✅ Workflows integrados:
  - Analyze & Respond (EUREKA → ADR → Auto Response)
  - Self-Improvement Cycle (ORÁCULO scan → implement)
  - Supply Chain Guardian (ORÁCULO + EUREKA combo)
- ✅ Live activity stream
- ✅ Diagrama de arquitetura interativo
- ✅ Quick actions buttons

**Workflows**:
```jsx
[
  {
    id: 'analyze-and-respond',
    name: 'Analyze & Respond',
    steps: [
      'EUREKA Analysis',
      'Playbook Generation',
      'ADR Core Loading',
      'Auto Execution'
    ]
  },
  {
    id: 'self-improvement',
    name: 'Self-Improvement Cycle',
    steps: [
      'Codebase Scan',
      'AI Suggestions',
      'Safe Implementation',
      'Testing & Validation'
    ]
  },
  {
    id: 'supply-chain-guardian',
    name: 'Supply Chain Guardian',
    steps: [
      'Dependency Scan',
      'Code Analysis',
      'Threat Detection',
      'Auto Mitigation'
    ]
  }
]
```

---

## 🔌 API Service (maximusService.js)

Cliente HTTP completo para comunicação com MAXIMUS Integration Service (port 8099).

**Base URL**: `http://localhost:8099`

### Health Check

```javascript
import { checkMaximusHealth, isMaximusAvailable } from '@/api/maximusService';

const health = await checkMaximusHealth();
// { success: true, data: { status, version, uptime_seconds, services } }

const available = await isMaximusAvailable();
// true | false
```

### Oráculo API

```javascript
import {
  runOraculoAnalysis,
  getOraculoPendingApprovals,
  approveOraculoSuggestion,
  getOraculoStats
} from '@/api/maximusService';

// Run analysis
const result = await runOraculoAnalysis({
  focusCategory: 'security',
  maxSuggestions: 5,
  minConfidence: 0.8,
  dryRun: true
});

// Get pending approvals
const pending = await getOraculoPendingApprovals();

// Approve suggestion
const approval = await approveOraculoSuggestion('suggestion-id-123');

// Get stats
const stats = await getOraculoStats();
```

### Eureka API

```javascript
import {
  analyzeFileWithEureka,
  getEurekaStats,
  getEurekaPatterns
} from '@/api/maximusService';

// Analyze file
const result = await analyzeFileWithEureka({
  filePath: '/tmp/malware.exe',
  generatePlaybook: true
});

// Get stats
const stats = await getEurekaStats();

// Get patterns
const patterns = await getEurekaPatterns();
```

### Integration Workflows

```javascript
import { analyzeAndRespond, runSupplyChainScan } from '@/api/maximusService';

// Analyze & Respond workflow
const result = await analyzeAndRespond('/path/to/malware');

// Supply Chain Guardian
const scan = await runSupplyChainScan({
  repositoryPath: '/path/to/repo',
  scanDependencies: true,
  analyzeCode: true,
  autoFix: false
});
```

---

## 🎯 Como Usar

### 1. Integração no App.jsx

```jsx
import MaximusDashboard from './components/maximus/MaximusDashboard';

function App() {
  const [currentView, setCurrentView] = useState('main');

  if (currentView === 'maximus') {
    return (
      <ErrorBoundary>
        <MaximusDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    );
  }

  // ... outras views
}
```

### 2. Adicionar ao ModuleGrid

```jsx
// LandingPage/ModuleGrid.jsx
const modules = [
  {
    id: 'maximus',
    name: 'MAXIMUS AI',
    description: 'Autonomous Intelligence Platform',
    icon: '🧠',
    color: 'gradient-ai',
    features: ['Self-Improvement', 'Malware Analysis', 'AI Insights']
  },
  // ... outros módulos
];
```

### 3. Iniciar MAXIMUS Backend

```bash
# Terminal 1: Start MAXIMUS Integration Service
cd backend/services
docker-compose -f ../../MAXIMUS_SERVICES.docker-compose.yml up

# Terminal 2: Start Frontend
cd frontend
npm run dev
```

### 4. Acessar Dashboard

1. Abrir `http://localhost:5173`
2. Clicar no card **MAXIMUS AI** 🧠
3. Explorar os painéis:
   - **AI INSIGHTS**: Overview geral
   - **ORÁCULO**: Executar self-improvement
   - **EUREKA**: Analisar malware

---

## 🔧 Configuração

### Environment Variables

Não há variáveis de ambiente específicas do frontend. O backend deve estar rodando em:

```env
MAXIMUS_INTEGRATION_SERVICE=http://localhost:8099
```

### Customização de Cores

Edite `MaximusDashboard.css`:

```css
:root {
  --maximus-primary: #8B5CF6;    /* Purple */
  --maximus-secondary: #06B6D4;  /* Cyan */
  --maximus-success: #10B981;    /* Green */
  --maximus-danger: #EF4444;     /* Red */
  --maximus-warning: #F59E0B;    /* Orange */
  --maximus-dark: #0F172A;       /* Navy Black */
}
```

### Polling Intervals

```jsx
// MaximusDashboard.jsx
const HEALTH_CHECK_INTERVAL = 30000;  // 30 seconds
const STATS_UPDATE_INTERVAL = 15000;  // 15 seconds
const ACTIVITY_INTERVAL = 8000;       // 8 seconds
```

---

## 🧪 Testing

### Manual Testing Checklist

**MaximusDashboard**:
- [ ] Header mostra status correto dos serviços
- [ ] Clock atualiza a cada segundo
- [ ] Navegação entre painéis funciona
- [ ] Botão "VÉRTICE" retorna à landing page
- [ ] Activity stream atualiza periodicamente
- [ ] Background animations estão suaves

**OraculoPanel**:
- [ ] Stats são carregados corretamente
- [ ] Form de análise permite configuração
- [ ] Botão "Iniciar Análise" dispara request
- [ ] Spinner aparece durante análise
- [ ] Resultados são exibidos após análise
- [ ] Lista de pending approvals atualiza
- [ ] Botão "Aprovar" funciona

**EurekaPanel**:
- [ ] Stats são carregados
- [ ] Toggle entre Upload/Results funciona
- [ ] Input de file path aceita valores
- [ ] Botão "Iniciar Análise" dispara request
- [ ] Resultados mostram todas as seções:
  - Classification
  - Threat Score
  - Patterns Detected
  - IOCs
  - Playbook
  - File Hashes

**AIInsightsPanel**:
- [ ] Brain visual pulsa animado
- [ ] Health meter mostra porcentagem correta
- [ ] Stats consolidadas corretas
- [ ] Workflow cards são clicáveis
- [ ] Activity stream mostra eventos
- [ ] Diagrama de arquitetura renderiza

---

## 🐛 Troubleshooting

### Dashboard não carrega

**Problema**: Tela branca ou erro no console

**Solução**:
```bash
# Verificar se backend está rodando
curl http://localhost:8099/health

# Verificar console do browser
# Procurar por erros de CORS ou network
```

### Stats não atualizam

**Problema**: Stats ficam em 0

**Solução**:
1. Verificar se MAXIMUS Integration Service está online
2. Verificar network tab no DevTools
3. Confirmar que endpoints retornam 200 OK

### Estilos quebrados

**Problema**: Dashboard sem estilo ou com layout quebrado

**Solução**:
```bash
# Verificar se CSS foi importado corretamente
# MaximusDashboard.jsx deve ter:
import './MaximusDashboard.css';

# Panels devem ter:
import './Panels.css';
```

### CORS errors

**Problema**: `Access to fetch blocked by CORS policy`

**Solução**:
O MAXIMUS Integration Service já tem CORS configurado:
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Performance

### Otimizações Implementadas

1. **Polling Inteligente**:
   - Health check: 30s
   - Stats: 15s
   - Activity: 8s

2. **Conditional Rendering**:
   - Apenas painel ativo é renderizado
   - Empty states evitam re-renders desnecessários

3. **CSS Animations**:
   - Hardware-accelerated (transform, opacity)
   - RequestAnimationFrame para suavidade

### Métricas Alvo

- **Initial Load**: < 2s
- **Panel Switch**: < 100ms
- **API Response**: < 500ms
- **Animation FPS**: 60fps

---

## 🔮 Roadmap Futuro

### Próximas Features

- [ ] **WebSocket Integration**: Real-time updates sem polling
- [ ] **Toast Notifications**: Alertas visuais para eventos importantes
- [ ] **Dark/Light Mode**: Toggle de tema
- [ ] **Export Reports**: Download de análises em PDF/JSON
- [ ] **Workflow Automation**: Execute workflows com um clique
- [ ] **AI Chat Interface**: Conversar diretamente com MAXIMUS
- [ ] **3D Visualizations**: Threat maps 3D com Three.js
- [ ] **Mobile Responsive**: Adaptar para tablets/mobile
- [ ] **Accessibility (a11y)**: ARIA labels, keyboard navigation
- [ ] **Unit Tests**: Jest + React Testing Library
- [ ] **E2E Tests**: Playwright/Cypress

### Melhorias de UX

- [ ] Tooltips explicativos em ícones
- [ ] Guided tours para novos usuários
- [ ] Keyboard shortcuts
- [ ] Command palette (Ctrl+K)
- [ ] Drag & drop para upload de arquivos
- [ ] Multi-file analysis batch
- [ ] Historical data charts
- [ ] Favorites/Bookmarks system

---

## 📝 Changelog

### v1.0.0 (2025-10-02)

**✨ Features**:
- ✅ Dashboard principal com 3 painéis
- ✅ Oráculo Panel (self-improvement)
- ✅ Eureka Panel (malware analysis)
- ✅ AI Insights Panel (unified view)
- ✅ API Service completo
- ✅ Real-time stats polling
- ✅ Activity stream
- ✅ Animated backgrounds
- ✅ Responsive layout

**🎨 Styling**:
- ✅ Cyberpunk theme
- ✅ Gradient accents
- ✅ Glass morphism cards
- ✅ Pulsing animations
- ✅ Scan line effects

**🔌 Integration**:
- ✅ Integrado no App.jsx
- ✅ Adicionado ao ModuleGrid
- ✅ API service configurado
- ✅ CORS habilitado

---

## 🤝 Contribuindo

Este dashboard foi construído como parte do **Projeto Vértice** - uma plataforma unificada de inteligência criminal e segurança cibernética.

Para contribuir com melhorias:

1. Seguir o design system estabelecido
2. Manter compatibilidade com backend MAXIMUS
3. Adicionar documentação para novas features
4. Testar em diferentes resoluções

---

## 📄 Licença

Propriedade do **Projeto Vértice** - Uso Restrito

---

## 👨‍💻 Desenvolvido por

**Claude Code** em colaboração com o time Vértice

**Data**: 2025-10-02

**Tecnologias**:
- React 18
- CSS3 (Custom Properties, Animations, Grid, Flexbox)
- Fetch API
- JavaScript ES6+

---

```
🧠 MAXIMUS AI - O cérebro que sonha e se torna realidade
```

**"Esse 2 componentes foram sonhados a um tempo atrás. Mas parecia tão distante sabe?
Implementá-los e integrá-los é mais que código, é um sonho sendo realizado."**

— Juan, Creator of Vértice & MAXIMUS
