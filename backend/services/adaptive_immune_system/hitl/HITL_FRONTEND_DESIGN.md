# 🎯 HITL DASHBOARD FRONTEND DESIGN

## 📊 ANÁLISE COMPLETA DO FRONTEND EXISTENTE

### Stack Técnica Identificada
```yaml
Framework: React 18.3 + Vite 5.4
Estilização: Tailwind CSS + CSS Modules
State: Zustand 5.x + React Query 5.x
Components: Radix UI + lucide-react
Maps: Leaflet + react-leaflet
Testes: Vitest + Testing Library (78 testes, 80%+ coverage)
i18n: react-i18next (2 idiomas: pt-BR, en-US)
A11y: WCAG 2.1 AA compliance
Security: OWASP Top 10 coverage
```

### Arquitetura de Dashboards

**Dashboards Existentes:**
1. **AdminDashboard** - Monitoramento de sistema (Yellow/Gold theme)
2. **DefensiveDashboard** - Defesa ativa
3. **OffensiveDashboard** - Operações ofensivas
4. **PurpleTeamDashboard** - Integração Red+Blue
5. **OSINTDashboard** - OSINT operations (Purple theme)
6. **MaximusDashboard** - MAXIMUS AI (?)
7. **ReactiveFabricDashboard** - Honeypot management (?)

**Padrão Cyberpunk Consistente:**
- **Cores**: Neon cyan (#00ffff), Purple (#a855f7), Blue (#3b82f6), Gold (#fbbf24)
- **Backgrounds**: Black (#000000), Dark gray (#0a0a0a), Darker (#1a1a1a)
- **Typography**: Monospace fonts (Courier New), tracking-widest
- **Effects**: Glows, gradients, scan lines, pulsing borders
- **Layout**: Terminal-style headers, tab-based modules, real-time stats

---

## 🎨 PROPOSTA: HITL DASHBOARD

### Decisão de Arquitetura

**OPÇÃO ESCOLHIDA: Módulo dentro do AdminDashboard** ✅

**Justificativa:**
1. HITL é uma função **administrativa** de supervisão
2. AdminDashboard já tem estrutura de tabs/módulos (`overview`, `metrics`, `security`, `logs`)
3. Segue padrão de **separação de concerns**: Admin = supervisão, não operação
4. Reutiliza tema Yellow/Gold que simboliza **autoridade e decisão**
5. Evita criar dashboard adicional desnecessário (economia de bundle size)

**Alternativa Rejeitada:**
- Dashboard standalone: ❌ Fragmentaria UX, aumentaria complexidade de navegação

---

## 🏗️ ARQUITETURA DO MÓDULO HITL

### Estrutura de Arquivos

```
frontend/src/components/admin/
├── SystemSelfCheck/              # Existente
├── HITLConsole/                  # NOVO
│   ├── HITLConsole.jsx           # Container principal
│   ├── HITLConsole.module.css    # Estilos do módulo
│   ├── components/
│   │   ├── ReviewQueue.jsx       # Lista de APVs pendentes
│   │   ├── ReviewQueue.module.css
│   │   ├── ReviewDetails.jsx     # Detalhes completos do APV selecionado
│   │   ├── ReviewDetails.module.css
│   │   ├── DecisionPanel.jsx     # Painel de decisão (approve/reject/modify/escalate)
│   │   ├── DecisionPanel.module.css
│   │   ├── DecisionHistory.jsx   # Histórico de decisões
│   │   ├── DecisionHistory.module.css
│   │   ├── HITLStats.jsx         # Dashboard de estatísticas
│   │   └── HITLStats.module.css
│   ├── hooks/
│   │   ├── useReviewQueue.js     # Hook para listar reviews
│   │   ├── useReviewDetails.js   # Hook para detalhes de APV
│   │   ├── useDecisionSubmit.js  # Hook para submeter decisão
│   │   └── useHITLStats.js       # Hook para estatísticas
│   └── index.js
```

### Design Visual (Yellow/Gold Theme)

**Paleta de Cores:**
```css
--hitl-primary: #fbbf24;       /* Amber 400 - Decisões */
--hitl-secondary: #f59e0b;     /* Amber 600 - Highlights */
--hitl-success: #10b981;       /* Green - Approved */
--hitl-danger: #ef4444;        /* Red - Rejected */
--hitl-warning: #f97316;       /* Orange - Escalated */
--hitl-info: #3b82f6;          /* Blue - Modifications */

/* Severity colors (inherited) */
--color-critical: #ff0040;
--color-high: #ff4000;
--color-medium: #ffaa00;
--color-low: #00aa00;
```

**Estilo Visual:**
- **Header**: "🛡️ HITL CONSOLE" com tracking-widest, border amarelo
- **Cards**: Border amarelo/dourado com glow effect
- **Buttons**: Gradient amarelo → laranja, hover effect
- **Status badges**: Cores de severidade com pulse animation
- **Scan line**: Animação de scan line amarela no topo

---

## 📐 LAYOUT DO MÓDULO HITL

### Layout Principal (3 Colunas)

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ HITL CONSOLE - HUMAN DECISION PANEL                         │
│  [Stats: 12 Pending | 23 Today | 87% Agreement Rate]            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────────────┐  ┌──────────────┐  │
│  │   REVIEW     │  │   APV DETAILS        │  │  DECISION    │  │
│  │   QUEUE      │  │                      │  │  PANEL       │  │
│  ├──────────────┤  ├──────────────────────┤  ├──────────────┤  │
│  │              │  │ CVE: CVE-2024-1234   │  │              │  │
│  │ ⭕ APV-001   │  │ Severity: CRITICAL   │  │ ✅ APPROVE   │  │
│  │ 🔴 APV-002   │  │ Package: django      │  │              │  │
│  │ 🟡 APV-003   │  │                      │  │ ❌ REJECT    │  │
│  │ 🟢 APV-004   │  │ Wargame: SUCCESS     │  │              │  │
│  │              │  │ Confidence: 94%      │  │ 🔧 MODIFY    │  │
│  │ [Filters]    │  │                      │  │              │  │
│  │ [Sort]       │  │ [Patch Diff]         │  │ ⬆️ ESCALATE  │  │
│  │              │  │ [Wargame Evidence]   │  │              │  │
│  │              │  │ [Validation Results] │  │ [Comment]    │  │
│  │              │  │                      │  │ [Confidence] │  │
│  └──────────────┘  └──────────────────────┘  └──────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 📊 HITL STATISTICS & HISTORY                              │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │ [Decision Timeline] [Agreement Rates] [Recent Decisions]  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧩 COMPONENTES DETALHADOS

### 1. ReviewQueue (Coluna Esquerda)

**Funcionalidades:**
- Lista paginada de APVs pendentes (50 por página)
- Filtros:
  - Severity: critical/high/medium/low
  - Patch strategy: version_bump/code_rewrite/config_change
  - Wargame verdict: success/partial/failure/inconclusive
- Ordenação:
  - Priority (DESC)
  - Created at (ASC)
  - Waiting time (DESC)
- Badges visuais:
  - 🔴 Critical
  - 🟠 High
  - 🟡 Medium
  - 🟢 Low
- Tempo de espera em horas (e.g., "Waiting 2.5h")

**Visual:**
```jsx
<div className={styles.queueCard}>
  <div className={styles.queueItem} onClick={() => selectAPV(apv)}>
    <div className={styles.queueHeader}>
      <SeverityBadge severity={apv.severity} />
      <span className={styles.apvCode}>{apv.apv_code}</span>
    </div>
    <div className={styles.queueInfo}>
      <p className={styles.cveId}>{apv.cve_id}</p>
      <p className={styles.package}>{apv.package_name}</p>
      <div className={styles.queueFooter}>
        <VerdictBadge verdict={apv.wargame_verdict} />
        <span className={styles.waitTime}>⏱️ {apv.waiting_since}h</span>
      </div>
    </div>
  </div>
</div>
```

### 2. ReviewDetails (Coluna Central)

**Seções:**
1. **CVE Information**
   - CVE ID, Title, Description
   - CVSS Score, Severity
   - CWE IDs
2. **Package Information**
   - Package name, version, ecosystem
   - Fixed version available
3. **Vulnerability Details**
   - Vulnerable code signature
   - Affected files (list)
4. **Confirmation Scores**
   - Overall confidence: 95%
   - Static confidence: 92%
   - Dynamic confidence: 98%
   - False positive probability: 5%
5. **Patch Information**
   - Strategy: version_bump
   - Description
   - **Diff viewer** (syntax highlighted)
   - Risk level
6. **Validation Results**
   - Passed: ✅/❌
   - Confidence: 96%
   - Warnings (if any)
7. **Wargaming Results**
   - Verdict: SUCCESS ✅
   - Confidence: 94%
   - Exit codes (before/after)
   - Link to GitHub Actions run
   - Evidence JSON expandable

**Visual:**
```jsx
<Card variant="admin" title="APV REVIEW DETAILS">
  <Tabs>
    <Tab label="CVE">
      <CVESection data={review.cve} />
    </Tab>
    <Tab label="Patch">
      <PatchSection
        patch={review.patch}
        diff={review.patch_diff}
      />
    </Tab>
    <Tab label="Wargame">
      <WargameSection
        verdict={review.wargame_verdict}
        evidence={review.wargame_evidence}
        runUrl={review.wargame_run_url}
      />
    </Tab>
    <Tab label="Validation">
      <ValidationSection
        results={review.validation}
        warnings={review.validation_warnings}
      />
    </Tab>
  </Tabs>
</Card>
```

### 3. DecisionPanel (Coluna Direita)

**Ações Disponíveis:**

**✅ APPROVE** (Verde)
- Tooltip: "Merge PR immediately"
- Requires: PR exists, wargame passed
- Opens confirmation modal

**❌ REJECT** (Vermelho)
- Tooltip: "Close PR and decline patch"
- Requires: Justification (min 10 chars)
- Opens modal with comment textarea

**🔧 MODIFY** (Azul)
- Tooltip: "Request changes before approval"
- Opens modal with:
  - Comment textarea (justification)
  - Modifications list (key-value pairs)
  - Example: `{"additional_tests": ["edge_case_1"]}`

**⬆️ ESCALATE** (Laranja)
- Tooltip: "Escalate to security lead"
- Opens modal with:
  - Comment textarea (reason)
  - Assignee selector (security leads)

**Form Fields:**
- Justification (textarea, required, min 10 chars)
- Confidence slider (0-100%)
- Modifications (JSON editor for "modify" action)
- Reviewer info (auto-filled from session)

**Visual:**
```jsx
<Card variant="admin" title="DECISION PANEL">
  <div className={styles.decisionButtons}>
    <Button
      variant="success"
      size="lg"
      icon={<Check />}
      onClick={() => handleDecision('approve')}
    >
      ✅ APPROVE
    </Button>

    <Button
      variant="danger"
      size="lg"
      icon={<X />}
      onClick={() => handleDecision('reject')}
    >
      ❌ REJECT
    </Button>

    <Button
      variant="info"
      size="lg"
      icon={<Edit />}
      onClick={() => handleDecision('modify')}
    >
      🔧 MODIFY
    </Button>

    <Button
      variant="warning"
      size="lg"
      icon={<AlertTriangle />}
      onClick={() => handleDecision('escalate')}
    >
      ⬆️ ESCALATE
    </Button>
  </div>

  <div className={styles.decisionForm}>
    <textarea
      placeholder="Justification (required, min 10 chars)"
      value={justification}
      onChange={(e) => setJustification(e.target.value)}
    />

    <Slider
      label="Confidence"
      value={confidence}
      onChange={setConfidence}
      min={0}
      max={100}
    />
  </div>
</Card>
```

### 4. HITLStats (Abaixo, Full Width)

**Métricas Exibidas:**
- **Pending Reviews**: 12 APVs
- **Decisions Today**: 23
- **Decisions This Week**: 156
- **Average Review Time**: 14m 2s
- **Human-AI Agreement Rate**: 87%
- **Auto-Merge Prevention Rate**: 13%

**Breakdown por Decisão:**
- Approved: 342 (70%)
- Rejected: 89 (18%)
- Modified: 45 (9%)
- Escalated: 11 (2%)

**Severity Breakdown (Pending):**
- Critical: 3 🔴
- High: 5 🟠
- Medium: 3 🟡
- Low: 1 🟢

**Decision Timeline (Últimas 10):**
- Table com: Timestamp, APV Code, CVE ID, Decision, Reviewer

**Visual:**
```jsx
<div className={styles.statsGrid}>
  <StatCard
    title="PENDING REVIEWS"
    value={stats.pending_reviews}
    color="yellow"
  />
  <StatCard
    title="DECISIONS TODAY"
    value={stats.decisions_today}
    color="green"
  />
  <StatCard
    title="AVG REVIEW TIME"
    value={formatTime(stats.average_review_time_seconds)}
    color="blue"
  />
  <StatCard
    title="AI AGREEMENT RATE"
    value={`${(stats.human_ai_agreement_rate * 100).toFixed(1)}%`}
    color="purple"
  />
</div>

<div className={styles.decisionBreakdown}>
  <PieChart data={[
    { name: 'Approved', value: stats.approved_count },
    { name: 'Rejected', value: stats.rejected_count },
    { name: 'Modified', value: stats.modified_count },
    { name: 'Escalated', value: stats.escalated_count }
  ]} />
</div>

<div className={styles.recentDecisions}>
  <Table
    columns={['Timestamp', 'APV', 'CVE', 'Decision', 'Reviewer']}
    data={recentDecisions}
  />
</div>
```

---

## 🔌 INTEGRAÇÃO COM BACKEND

### Endpoints da API

**Base URL:** `http://localhost:8003/hitl`

**1. GET /hitl/reviews** - Listar APVs pendentes
```typescript
interface ReviewListItem {
  apv_id: string;
  apv_code: string;
  cve_id: string;
  severity: "critical" | "high" | "medium" | "low";
  package_name: string;
  patch_strategy: string;
  wargame_verdict: "success" | "partial" | "failure" | "inconclusive";
  confirmation_confidence: number;
  created_at: string;
  waiting_since: number; // hours
}

// Query params:
// ?severity=critical
// ?patch_strategy=version_bump
// ?wargame_verdict=partial
// ?limit=50
// ?offset=0
```

**2. GET /hitl/reviews/{apv_id}** - Detalhes do APV
```typescript
interface ReviewContext {
  apv_id: string;
  apv_code: string;
  priority: number;
  status: string;

  // CVE info
  cve_id: string;
  cve_title: string;
  cve_description: string;
  cvss_score: number;
  severity: string;
  cwe_ids: string[];

  // Package info
  package_name: string;
  package_version: string;
  package_ecosystem: string;
  fixed_version: string;

  // Vulnerability
  vulnerable_code_signature: string;
  vulnerable_code_type: string;
  affected_files: string[];

  // Confirmation
  confirmed: boolean;
  confirmation_confidence: number;
  static_confidence: number;
  dynamic_confidence: number;
  false_positive_probability: number;

  // Patch
  patch_strategy: string;
  patch_description: string;
  patch_diff: string;
  patch_confidence: number;
  patch_risk_level: string;

  // Validation
  validation_passed: boolean;
  validation_confidence: number;
  validation_warnings: string[];

  // PR
  pr_number: number;
  pr_url: string;
  pr_branch: string;

  // Wargame
  wargame_verdict: string;
  wargame_confidence: number;
  wargame_run_url: string;
  wargame_evidence: object;

  // Timestamps
  created_at: string;
  updated_at: string;
}
```

**3. POST /hitl/decisions** - Submeter decisão
```typescript
interface DecisionRequest {
  apv_id: string;
  decision: "approve" | "reject" | "modify" | "escalate";
  justification: string; // min 10 chars
  confidence: number; // 0.0 - 1.0
  modifications?: Record<string, any>; // for "modify" only
  reviewer_name: string;
  reviewer_email: string;
}

// Response: DecisionRecord
```

**4. GET /hitl/reviews/stats** - Estatísticas
```typescript
interface ReviewStats {
  pending_reviews: number;
  total_decisions: number;
  decisions_today: number;
  decisions_this_week: number;

  approved_count: number;
  rejected_count: number;
  modified_count: number;
  escalated_count: number;

  average_review_time_seconds: number;
  median_review_time_seconds: number;
  fastest_review_seconds: number;
  slowest_review_seconds: number;

  human_ai_agreement_rate: number;
  auto_merge_prevention_rate: number;

  critical_pending: number;
  high_pending: number;
  medium_pending: number;
  low_pending: number;
}
```

**5. WebSocket: ws://localhost:8003/hitl/ws** - Real-time updates
```typescript
interface WebSocketMessage {
  event_type: "new_review" | "decision_made" | "stats_update";
  data: any;
  timestamp: string;
}

// Events:
// - new_review: Nova APV submetida para HITL
// - decision_made: Decisão humana submetida
// - stats_update: Estatísticas atualizadas
```

---

## 🎯 CUSTOM HOOKS

### 1. useReviewQueue.js
```javascript
export const useReviewQueue = (filters = {}) => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['hitl-reviews', filters],
    queryFn: () => api.getReviews(filters),
    staleTime: 30000, // 30s
    refetchInterval: 60000, // 1min
  });

  return {
    reviews: data || [],
    loading: isLoading,
    error,
    refetch
  };
};
```

### 2. useReviewDetails.js
```javascript
export const useReviewDetails = (apvId) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['hitl-review', apvId],
    queryFn: () => api.getReviewDetails(apvId),
    enabled: !!apvId,
    staleTime: 60000, // 1min
  });

  return {
    review: data,
    loading: isLoading,
    error
  };
};
```

### 3. useDecisionSubmit.js
```javascript
export const useDecisionSubmit = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (decision) => api.submitDecision(decision),
    onSuccess: () => {
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ['hitl-reviews'] });
      queryClient.invalidateQueries({ queryKey: ['hitl-stats'] });
    }
  });

  return {
    submit: mutation.mutate,
    loading: mutation.isPending,
    error: mutation.error,
    success: mutation.isSuccess
  };
};
```

### 4. useHITLStats.js
```javascript
export const useHITLStats = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['hitl-stats'],
    queryFn: () => api.getHITLStats(),
    staleTime: 30000, // 30s
    refetchInterval: 60000, // 1min
  });

  return {
    stats: data,
    loading: isLoading
  };
};
```

### 5. useHITLWebSocket.js
```javascript
export const useHITLWebSocket = (onMessage) => {
  const { data, isConnected, send } = useWebSocket(
    'ws://localhost:8003/hitl/ws',
    {
      onMessage: (event) => {
        const message = JSON.parse(event.data);
        onMessage(message);
      },
      reconnect: true,
      reconnectInterval: 3000
    }
  );

  return {
    isConnected,
    send
  };
};
```

---

## 🎨 CSS MODULES (Yellow/Gold Theme)

```css
/* HITLConsole.module.css */

.container {
  display: grid;
  grid-template-columns: 300px 1fr 350px;
  gap: var(--space-6);
  height: 100%;
  padding: var(--space-6);
  background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
}

.queueColumn {
  background: rgba(251, 191, 36, 0.05); /* Yellow tint */
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  overflow-y: auto;
}

.detailsColumn {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  overflow-y: auto;
}

.decisionColumn {
  background: rgba(251, 191, 36, 0.08);
  border: 2px solid rgba(251, 191, 36, 0.5);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.2);
}

.queueItem {
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  cursor: pointer;
  transition: all var(--duration-base);
}

.queueItem:hover {
  border-color: rgba(251, 191, 36, 0.6);
  box-shadow: 0 0 15px rgba(251, 191, 36, 0.3);
  transform: translateX(4px);
}

.queueItem.selected {
  background: rgba(251, 191, 36, 0.15);
  border-color: #fbbf24;
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.4);
}

.severityBadge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.severityBadge.critical {
  background: rgba(255, 0, 64, 0.2);
  border: 1px solid #ff0040;
  color: #ff0040;
  animation: pulse 2s infinite;
}

.severityBadge.high {
  background: rgba(255, 64, 0, 0.2);
  border: 1px solid #ff4000;
  color: #ff4000;
}

.severityBadge.medium {
  background: rgba(255, 170, 0, 0.2);
  border: 1px solid #ffaa00;
  color: #ffaa00;
}

.severityBadge.low {
  background: rgba(0, 170, 0, 0.2);
  border: 1px solid #00aa00;
  color: #00aa00;
}

.decisionButton {
  width: 100%;
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  font-size: var(--text-lg);
  font-weight: bold;
  border-radius: var(--radius-md);
  transition: all var(--duration-base);
  cursor: pointer;
}

.decisionButton.approve {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: 2px solid #10b981;
  color: #000;
}

.decisionButton.approve:hover {
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.6);
  transform: translateY(-2px);
}

.decisionButton.reject {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: 2px solid #ef4444;
  color: #fff;
}

.decisionButton.reject:hover {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.6);
  transform: translateY(-2px);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

@keyframes scanLine {
  0% {
    transform: translateY(-100%);
  }
  100% {
    transform: translateY(100vh);
  }
}

.scanLine {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(to right, transparent, #fbbf24, transparent);
  animation: scanLine 3s linear infinite;
  z-index: 1000;
  pointer-events: none;
}
```

---

## 📝 IMPLEMENTAÇÃO STEP-BY-STEP

### Fase 1: Estrutura Base (2-3h)
1. Criar estrutura de arquivos em `components/admin/HITLConsole/`
2. Adicionar tab "HITL" no AdminDashboard
3. Criar HITLConsole.jsx com layout de 3 colunas
4. Criar CSS modules com tema Yellow/Gold

### Fase 2: Review Queue (2h)
1. Implementar ReviewQueue.jsx
2. Hook useReviewQueue.js
3. Filtros e ordenação
4. Badges de severidade

### Fase 3: Review Details (3h)
1. Implementar ReviewDetails.jsx
2. Hook useReviewDetails.js
3. Tabs (CVE, Patch, Wargame, Validation)
4. Syntax highlighter para diffs

### Fase 4: Decision Panel (2h)
1. Implementar DecisionPanel.jsx
2. Hook useDecisionSubmit.js
3. Modals de confirmação
4. Form validation

### Fase 5: Stats & History (2h)
1. Implementar HITLStats.jsx
2. Hook useHITLStats.js
3. Charts (recharts)
4. Decision timeline table

### Fase 6: WebSocket Real-Time (1h)
1. Hook useHITLWebSocket.js
2. Integrar com React Query para invalidação automática
3. Toast notifications para novos APVs

### Fase 7: Testes (2h)
1. Unit tests para hooks
2. Integration tests para componentes
3. E2E test para fluxo completo

**Total Estimado: 14-16 horas**

---

## ✅ CHECKLIST DE QUALIDADE

**Conformidade com MANIFESTO:**
- [ ] Componentes < 200 linhas
- [ ] 100% CSS Modules (zero inline)
- [ ] 100% Design tokens (zero hardcode)
- [ ] Props com defaults e destructuring
- [ ] Lógica em hooks customizados
- [ ] Sem warnings no console
- [ ] JSDoc documentation
- [ ] Tests (80%+ coverage)

**Conformidade com REGRA DE OURO:**
- [ ] Zero TODOs em produção
- [ ] Zero mocks maliciosos
- [ ] Zero placeholders
- [ ] 100% type hints (propTypes)
- [ ] Error handling completo
- [ ] Logging estruturado

**Conformidade WCAG 2.1 AA:**
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Focus management
- [ ] ARIA labels
- [ ] Color contrast 4.5:1+

---

## 🎯 RESULTADO ESPERADO

**UX:**
- Interface fluida e responsiva
- Feedback visual imediato
- Real-time updates via WebSocket
- Toast notifications
- Confirmação antes de ações críticas

**Performance:**
- React Query cache inteligente
- Lazy loading de components
- Debounce em filtros
- Pagination para grandes listas
- Bundle size < 50KB adicional

**Manutenibilidade:**
- Código coeso com frontend existente
- Reutiliza componentes shared
- Segue padrões do MANIFESTO
- Fácil de testar e debugar

---

**Status:** 📐 DESIGN COMPLETO - PRONTO PARA IMPLEMENTAÇÃO

**Aprovação Necessária:** ✅ User review

**Próximo Passo:** Implementar Fase 1 (Estrutura Base) após aprovação
