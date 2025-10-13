# Sprint 2 - Fase 3.1: Inteligência Tática Dashboard - Plano de Implementação

**Data**: 2025-10-13  
**Sprint**: 2 | **Fase**: 3.1 Frontend  
**Objetivo**: Criar dashboard de Inteligência Tática seguindo **Padrão PAGANI** (obra de arte frontend)

---

## 📊 ANÁLISE DO PADRÃO PAGANI

### Estrutura Identificada
```
components/dashboards/[Dashboard]/
├── [Dashboard].jsx              # Componente principal (coordenação)
├── [Dashboard].module.css       # Estilos isolados
├── components/                  # Subcomponentes específicos
│   ├── Header.jsx
│   ├── Sidebar.jsx
│   ├── Footer.jsx
│   └── ModuleContainer.jsx
├── hooks/                       # Lógica de negócio isolada
│   ├── use[Dashboard]Metrics.js
│   └── useRealTime[Feature].js
└── __tests__/                   # Testes unitários
```

### Princípios PAGANI
1. **Component-Driven**: Componentes <150 linhas, responsabilidade única
2. **Separation of Concerns**: JSX / CSS / Logic totalmente separados
3. **Design Tokens First**: Zero hardcode, 100% tokens
4. **Lazy Loading**: Suspense + ErrorBoundary para módulos
5. **i18n Native**: useTranslation em todos componentes
6. **Accessibility**: ARIA, Skip Links, semantic HTML

### Tokens System
```css
/* Cores temáticas */
--color-cyber-primary: #00ffff
--color-osint-primary: #a855f7
--color-analytics-primary: #3b82f6

/* Tactical Intelligence = Nova categoria? */
--color-tactical-primary: #fbbf24 (Amarelo/Gold - inteligência/alerta)
--color-tactical-secondary: #f59e0b
--color-tactical-accent: #d97706

/* Backgrounds, borders, text seguem padrão existente */
```

---

## 🎯 ESTRATÉGIA DE LOCALIZAÇÃO

### Análise de Dashboards Existentes
- ✅ **OffensiveDashboard** - Red Team Operations (Cyber theme)
- ✅ **DefensiveDashboard** - Blue Team (não analisado ainda)
- ✅ **PurpleTeamDashboard** - Integrated Ops (não analisado ainda)

### Opção Escolhida: **NOVA DASHBOARD DEDICADA**

**Justificativa**:
1. **Isolation Deception** tem identidade própria (não é apenas offensive)
2. Métricas específicas: TTPs, ATT&CK mapping, threat actor profiles
3. Fluxo de trabalho único: Coleta passiva → Análise → HITL → (futuro) resposta
4. Tema visual próprio: Gold/Amber (alerta/inteligência)

**Localização**:
```
frontend/src/components/dashboards/TacticalIntelDashboard/
```

---

## 🏗️ ARQUITETURA DO COMPONENTE

### Estrutura Completa
```
TacticalIntelDashboard/
├── TacticalIntelDashboard.jsx
├── TacticalIntelDashboard.module.css
├── components/
│   ├── TacticalHeader.jsx          # Métricas gerais + navegação
│   ├── TacticalSidebar.jsx         # Módulos + filtros
│   ├── TacticalFooter.jsx          # Status + alertas
│   ├── ModuleContainer.jsx         # Wrapper de módulos
│   ├── MetricsBar.jsx              # KPIs em tempo real
│   ├── ThreatActorCard.jsx         # Card de threat actor
│   └── TTPTimeline.jsx             # Timeline de TTPs
├── hooks/
│   ├── useTacticalMetrics.js       # Fetch metrics do backend
│   ├── useDeceptionEvents.js       # Real-time events
│   ├── useThreatActors.js          # Threat actor profiles
│   └── useATTACKMapping.js         # MITRE ATT&CK correlation
└── __tests__/
    └── TacticalIntelDashboard.test.jsx
```

### Módulos da Dashboard
```javascript
const modules = [
  { 
    id: 'deception-overview', 
    name: 'Deception Overview',
    icon: '🎭',
    component: DeceptionOverview // Lazy loaded
  },
  { 
    id: 'threat-actors', 
    name: 'Threat Actors',
    icon: '🎯',
    component: ThreatActorProfiles
  },
  { 
    id: 'ttp-analysis', 
    name: 'TTP Analysis',
    icon: '🧬',
    component: TTPAnalysis
  },
  { 
    id: 'attack-mapping', 
    name: 'ATT&CK Mapping',
    icon: '🗺️',
    component: ATTACKMapping
  },
  { 
    id: 'intel-fusion', 
    name: 'Intelligence Fusion',
    icon: '🔬',
    component: IntelligenceFusion // De Sprint 1
  },
  { 
    id: 'hitl-queue', 
    name: 'HITL Queue',
    icon: '⚖️',
    component: HITLQueue // Futuro Sprint 3
  }
];
```

---

## 📝 PLANO DE IMPLEMENTAÇÃO (METODOLÓGICO)

### **ETAPA 1: Estrutura Base e Tokens** (30min)
**Objetivo**: Criar estrutura de diretórios e design tokens

**Ações**:
1. Criar estrutura de diretórios conforme arquitetura
2. Adicionar tokens de cor tactical em `styles/tokens/colors.css`
3. Criar `TacticalIntelDashboard.module.css` base
4. Criar arquivo principal `TacticalIntelDashboard.jsx` (skeleton)

**Validação**:
```bash
# Estrutura criada
ls -R frontend/src/components/dashboards/TacticalIntelDashboard/

# Dashboard importável (sem erros)
npm run dev
```

**Critério de Sucesso**:
- [ ] Estrutura de diretórios completa
- [ ] Tokens tactical adicionados
- [ ] Componente renderiza (vazio mas sem erros)

---

### **ETAPA 2: Header + Métricas** (45min)
**Objetivo**: Criar header com métricas em tempo real

**Ações**:
1. Criar `TacticalHeader.jsx` com estrutura
2. Criar `MetricsBar.jsx` para KPIs:
   - Active Honeypots
   - Events Today
   - Unique Threat Actors
   - TTPs Identified
3. Criar `useTacticalMetrics.js` hook:
   - Fetch de `/api/reactive-fabric/metrics`
   - Polling cada 5s
   - Error handling

**Validação**:
```bash
# Componente sem erros TypeScript/ESLint
npm run lint

# Métricas carregando do backend
# Verificar DevTools Network tab
```

**Critério de Sucesso**:
- [ ] Header renderiza com métricas
- [ ] Hook conecta ao backend Sprint 1
- [ ] Loading states implementados
- [ ] i18n configurado (pt-BR/en-US)

---

### **ETAPA 3: Sidebar + Navegação de Módulos** (30min)
**Objetivo**: Sidebar com lista de módulos e filtros

**Ações**:
1. Criar `TacticalSidebar.jsx`
2. Implementar lista de módulos (array de config)
3. Estado `activeModule` com React.useState
4. Highlight do módulo ativo
5. Botão "Voltar" para main dashboard

**Validação**:
```bash
# Navegação funciona
# Click em módulo muda activeModule state
```

**Critério de Sucesso**:
- [ ] Sidebar renderiza lista de módulos
- [ ] Click muda estado activeModule
- [ ] Visual feedback (hover, active)
- [ ] Acessibilidade (ARIA labels)

---

### **ETAPA 4: Module Container + Lazy Loading** (30min)
**Objetivo**: Container de módulos com Suspense e ErrorBoundary

**Ações**:
1. Criar `ModuleContainer.jsx` (wrapper genérico)
2. Implementar Lazy loading de módulos
3. LoadingFallback component (skeleton)
4. Integrar WidgetErrorBoundary (já existe no projeto)

**Validação**:
```bash
# Lazy loading funciona
# Suspense mostra skeleton
# ErrorBoundary captura erros
```

**Critério de Sucesso**:
- [ ] Módulos carregam dinamicamente
- [ ] Skeleton durante loading
- [ ] Erro não quebra dashboard

---

### **ETAPA 5: Componentes de Módulo - Deception Overview** (60min)
**Objetivo**: Criar primeiro módulo funcional

**Ações**:
1. Criar `DeceptionOverview/DeceptionOverview.jsx`
2. Conectar ao gateway de Sprint 1 (`/api/reactive-fabric/events`)
3. Exibir:
   - Eventos recentes (tabela)
   - Honeypots ativos (grid de cards)
   - Mapa de origem de ataques (usar ThreatMap?)
4. Criar `useDeceptionEvents.js` hook

**Validação**:
```bash
# Dados do backend aparecem
# Filtros funcionam
# Real-time update (WebSocket futuro, polling por agora)
```

**Critério de Sucesso**:
- [ ] Eventos carregam do backend
- [ ] UI responsiva e clara
- [ ] Filtros funcionais (severidade, tipo)

---

### **ETAPA 6: Footer + Status** (20min)
**Objetivo**: Footer com status de sistema

**Ações**:
1. Criar `TacticalFooter.jsx`
2. Mostrar:
   - Backend connectivity status
   - Last update timestamp
   - Active alerts count

**Validação**:
```bash
# Footer sempre visível
# Status atualiza
```

**Critério de Sucesso**:
- [ ] Footer renderiza
- [ ] Status reflete backend

---

### **ETAPA 7: Integração com Roteamento** (20min)
**Objetivo**: Adicionar rota para nova dashboard

**Ações**:
1. Adicionar em `App.jsx` ou router config:
   ```jsx
   <Route path="/tactical-intel" element={<TacticalIntelDashboard />} />
   ```
2. Adicionar link no menu principal
3. Adicionar no CyberDashboard como botão "Tactical Intel"

**Validação**:
```bash
# Rota acessível via URL
# Link no menu funciona
```

**Critério de Sucesso**:
- [ ] Dashboard acessível via navegação
- [ ] URL `/tactical-intel` funciona

---

### **ETAPA 8: Testes Unitários** (40min)
**Objetivo**: Cobertura de testes conforme Doutrina

**Ações**:
1. Criar `TacticalIntelDashboard.test.jsx`:
   - Render sem erros
   - Navegação entre módulos
   - Loading states
2. Testar hooks com `@testing-library/react-hooks`
3. Mock de API calls

**Validação**:
```bash
npm run test -- TacticalIntelDashboard
# Coverage >90%
```

**Critério de Sucesso**:
- [ ] Todos testes passam
- [ ] Coverage ≥90%

---

### **ETAPA 9: i18n + Acessibilidade** (30min)
**Objetivo**: Internacionalização e ARIA completo

**Ações**:
1. Adicionar keys em `i18n/locales/pt-BR.json`:
   ```json
   "dashboard": {
     "tactical": {
       "title": "Inteligência Tática",
       "modules": {
         "deceptionOverview": "Visão Geral",
         ...
       }
     }
   }
   ```
2. Adicionar ARIA labels em todos componentes interativos
3. Testar com leitor de tela

**Validação**:
```bash
# Trocar idioma funciona
# axe DevTools sem erros
```

**Critério de Sucesso**:
- [ ] i18n completo
- [ ] 0 erros de acessibilidade

---

### **ETAPA 10: Documentação + Validação Final** (30min)
**Objetivo**: Documentar componente e validar Doutrina

**Ações**:
1. Criar `TacticalIntelDashboard/README.md`
2. Adicionar JSDoc em todos componentes
3. Atualizar `COMPONENTS_API.md`
4. Validar checklist Doutrina:
   - ✅ NO MOCK
   - ✅ NO PLACEHOLDER
   - ✅ 100% type hints (PropTypes)
   - ✅ Docstrings
   - ✅ Error handling

**Validação**:
```bash
npm run lint
npm run test
npm run build
```

**Critério de Sucesso**:
- [ ] Build sem erros
- [ ] Lint sem warnings
- [ ] Documentação completa

---

## 📋 CHECKLIST FINAL - CONFORMIDADE DOUTRINA

### Qualidade de Código
- [ ] Componentes <150 linhas
- [ ] Zero CSS hardcoded
- [ ] 100% Design Tokens
- [ ] PropTypes em todos componentes
- [ ] JSDoc completo

### Funcionalidade
- [ ] Conecta ao backend Sprint 1
- [ ] Real-time metrics (polling)
- [ ] Error boundaries implementados
- [ ] Loading states em todos fetches

### Testes
- [ ] Coverage ≥90%
- [ ] Testes de integração
- [ ] Mock de APIs

### Acessibilidade
- [ ] ARIA labels
- [ ] Skip links
- [ ] Keyboard navigation
- [ ] 0 erros axe

### i18n
- [ ] pt-BR completo
- [ ] en-US completo
- [ ] useTranslation em todos componentes

### Performance
- [ ] Lazy loading de módulos
- [ ] useMemo/useCallback onde necessário
- [ ] Time to Interactive <2s

### Documentação
- [ ] README do componente
- [ ] JSDoc em funções
- [ ] COMPONENTS_API.md atualizado

---

## 🚀 PRÓXIMOS PASSOS (APÓS APROVAÇÃO)

Aguardando comando para executar **ETAPA 1**.

**Tempo Estimado Total**: 4h30min  
**Deploy Ready**: Sim, ao final de todas etapas  
**Compatibilidade**: 100% com Padrão PAGANI

---

**Status**: AGUARDANDO APROVAÇÃO  
**Autor**: MAXIMUS Team  
**Revisão**: Necessária antes de execução
