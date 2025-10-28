# 🎨 Widget Library - Guia de Uso

**Projeto Vértice - Frontend Components**
**Versão:** 1.0.0
**Local:** `/frontend/src/components/shared/widgets/`

---

## 📦 Instalação / Importação

```javascript
// Importar widgets individuais
import { MetricCard } from '@/components/shared/widgets';
import { ModuleStatusCard } from '@/components/shared/widgets';
import { ActivityItem } from '@/components/shared/widgets';
import { PanelCard } from '@/components/shared/widgets';

// Ou importar tudo
import * as Widgets from '@/components/shared/widgets';
```

---

## 1️⃣ MetricCard

### **Descrição**
Exibe uma métrica com label e valor. Suporta 5 variantes de cor e estado de loading.

### **Props**

| Prop | Type | Required | Default | Descrição |
|------|------|----------|---------|-----------|
| `label` | string | ✅ | - | Texto do label da métrica |
| `value` | number \| string | ✅ | - | Valor da métrica a exibir |
| `loading` | boolean | ❌ | false | Mostra estado de carregamento |
| `variant` | string | ❌ | 'primary' | Cor do card: 'primary', 'success', 'warning', 'danger', 'info' |
| `className` | string | ❌ | '' | Classes CSS adicionais |
| `loadingText` | string | ❌ | '...' | Texto exibido durante loading |
| `ariaLabel` | string | ❌ | auto | Label de acessibilidade |

### **Variantes de Cor**

- **primary** (azul) - Métricas gerais
- **success** (verde) - Métricas positivas
- **warning** (amarelo) - Alertas moderados
- **danger** (vermelho) - Alertas críticos
- **info** (roxo) - Informações complementares

### **Exemplos de Uso**

#### Básico
```jsx
<MetricCard
  label="Active Scans"
  value={42}
/>
```

#### Com Variante
```jsx
<MetricCard
  label="Threats Detected"
  value={127}
  variant="danger"
/>
```

#### Com Loading
```jsx
<MetricCard
  label="Total Requests"
  value={metrics.totalRequests}
  loading={isLoading}
  loadingText="Loading..."
/>
```

#### Grid de Métricas
```jsx
<div className="metrics-grid">
  <MetricCard label="ACTIVE SCANS" value={12} variant="primary" />
  <MetricCard label="EXPLOITS FOUND" value={5} variant="warning" />
  <MetricCard label="TARGETS" value={8} variant="info" />
  <MetricCard label="C2 SESSIONS" value={3} variant="success" />
</div>
```

### **Estilo CSS**
- **Hover:** Elevação e shadow
- **Responsive:** Font sizes adaptáveis
- **Animação:** Transição suave (0.3s)

---

## 2️⃣ ModuleStatusCard

### **Descrição**
Exibe status de um módulo/serviço com indicador visual (dot pulsante) e descrição de atividade.

### **Props**

| Prop | Type | Required | Default | Descrição |
|------|------|----------|---------|-----------|
| `name` | string | ✅ | - | Nome do módulo/serviço |
| `status` | string | ❌ | 'online' | Status: 'online', 'offline', 'degraded', 'idle', 'running' |
| `activity` | string | ❌ | - | Descrição da atividade atual |
| `className` | string | ❌ | '' | Classes CSS adicionais |

### **Status Disponíveis**

| Status | Cor | Animação | Uso |
|--------|-----|----------|-----|
| `online` | Verde | Pulse 2s | Serviço funcionando normalmente |
| `offline` | Vermelho | - | Serviço fora do ar |
| `degraded` | Amarelo | Pulse 1.5s | Serviço com problemas |
| `idle` | Azul | - | Serviço inativo/standby |
| `running` | Roxo | Pulse 1s | Serviço executando tarefa |

### **Exemplos de Uso**

#### Básico
```jsx
<ModuleStatusCard
  name="Maximus AI Engine"
  status="online"
  activity="Analyzing patterns..."
/>
```

#### Diferentes Status
```jsx
<ModuleStatusCard
  name="Network Scanner"
  status="running"
  activity="Scanning 192.168.1.0/24"
/>

<ModuleStatusCard
  name="Threat Intelligence"
  status="degraded"
  activity="High API latency detected"
/>

<ModuleStatusCard
  name="Backup Service"
  status="idle"
/>
```

#### Grid de Módulos (OSINT)
```jsx
<div className="grid grid-cols-3 gap-4">
  <ModuleStatusCard name="Maximus AI" status="online" activity="Analisando padrões" />
  <ModuleStatusCard name="Username Hunter" status="online" activity="2,847 perfis" />
  <ModuleStatusCard name="Email Analyzer" status="online" activity="1,293 emails" />
  <ModuleStatusCard name="Phone Intel" status="running" activity="847 números" />
  <ModuleStatusCard name="Social Scraper" status="online" activity="Tempo real" />
  <ModuleStatusCard name="Dark Web Monitor" status="online" activity="Varredura ativa" />
</div>
```

### **Estilo CSS**
- **Hover:** Border color change
- **Dot Animation:** Pulse nos status ativos
- **Responsive:** Layout adaptável

---

## 3️⃣ ActivityItem

### **Descrição**
Item de log/atividade com timestamp, tipo e ação. Suporta 4 níveis de severidade com cores distintas.

### **Props**

| Prop | Type | Required | Default | Descrição |
|------|------|----------|---------|-----------|
| `timestamp` | string | ✅ | - | Timestamp da atividade (ex: "14:23:45") |
| `type` | string | ✅ | - | Tipo/fonte da atividade (ex: "CORE", "EUREKA") |
| `action` | string | ✅ | - | Descrição da ação/evento |
| `severity` | string | ❌ | 'info' | Severidade: 'info', 'success', 'warning', 'critical' |
| `className` | string | ❌ | '' | Classes CSS adicionais |

### **Níveis de Severidade**

| Severity | Cor | Border | Uso |
|----------|-----|--------|-----|
| `info` | Azul | #60A5FA | Informações gerais |
| `success` | Verde | #4ADE80 | Ações bem-sucedidas |
| `warning` | Amarelo | #FACC15 | Alertas/avisos |
| `critical` | Vermelho | #F87171 | Erros críticos |

### **Exemplos de Uso**

#### Básico
```jsx
<ActivityItem
  timestamp="14:23:45"
  type="CORE"
  action="Chain-of-thought reasoning initiated"
  severity="info"
/>
```

#### Stream de Atividades
```jsx
{brainActivity.slice(0, 5).map(activity => (
  <ActivityItem
    key={activity.id}
    timestamp={activity.timestamp}
    type={activity.type}
    action={activity.action}
    severity={activity.severity}
  />
))}
```

#### Diferentes Severidades
```jsx
<ActivityItem
  timestamp="14:20:12"
  type="ORÁCULO"
  action="Suggestion generated: Security enhancement"
  severity="warning"
/>

<ActivityItem
  timestamp="14:21:33"
  type="EUREKA"
  action="IOC extracted: Suspicious domain detected"
  severity="critical"
/>

<ActivityItem
  timestamp="14:22:01"
  type="ADR"
  action="Playbook execution completed"
  severity="success"
/>
```

### **Estilo CSS**
- **Hover:** TranslateX(4px) e background darker
- **Border-left:** 3px com cor da severidade
- **Monospace:** Fonte Courier New
- **Responsive:** Font sizes adaptáveis

---

## 4️⃣ PanelCard

### **Descrição**
Container genérico para painéis com header (título + ícone + ações) e conteúdo. Suporta 3 variantes de estilo.

### **Props**

| Prop | Type | Required | Default | Descrição |
|------|------|----------|---------|-----------|
| `title` | string | ❌ | - | Título do painel |
| `icon` | string | ❌ | - | Ícone (emoji ou font icon) |
| `variant` | string | ❌ | 'primary' | Variante: 'primary', 'secondary', 'dark' |
| `actions` | ReactNode | ❌ | - | Botões/ações no header |
| `children` | ReactNode | ✅ | - | Conteúdo do painel |
| `className` | string | ❌ | '' | Classes CSS adicionais |

### **Variantes**

| Variant | Border Color | Uso |
|---------|--------------|-----|
| `primary` | Azul (#3B82F6) | Painéis principais |
| `secondary` | Roxo (#A855F7) | Painéis secundários |
| `dark` | Cinza (#64748B) | Painéis informativos |

### **Exemplos de Uso**

#### Básico
```jsx
<PanelCard title="Network Scanner" icon="🔍">
  <p>Panel content goes here...</p>
</PanelCard>
```

#### Com Actions
```jsx
<PanelCard
  title="Threat Intelligence"
  icon="🎯"
  variant="primary"
  actions={
    <>
      <button>Refresh</button>
      <button>Export</button>
    </>
  }
>
  <ThreatList threats={threats} />
</PanelCard>
```

#### Sem Header
```jsx
<PanelCard variant="dark">
  <SimpleContent />
</PanelCard>
```

#### Exemplo Completo (Dashboard Module)
```jsx
<PanelCard
  title="MALWARE ANALYSIS"
  icon="🦠"
  variant="secondary"
  actions={
    <button className="btn-refresh">
      🔄 Refresh
    </button>
  }
>
  <div className="malware-stats">
    <MetricCard label="Samples Analyzed" value={247} variant="info" />
    <MetricCard label="Threats Found" value={12} variant="danger" />
  </div>

  <div className="malware-recent">
    {samples.map(sample => (
      <ActivityItem
        key={sample.id}
        timestamp={sample.time}
        type="ANALYSIS"
        action={sample.description}
        severity={sample.threat ? 'critical' : 'success'}
      />
    ))}
  </div>
</PanelCard>
```

### **Estilo CSS**
- **Hover:** Elevação e shadow
- **Header:** Background darker
- **Border:** 2px solid com cor da variante
- **Responsive:** Layout adaptável mobile

---

## 🎨 Composição de Widgets

### **Exemplo 1: Dashboard Header com Métricas**
```jsx
import { MetricCard } from '@/components/shared/widgets';

const DashboardHeader = ({ metrics, loading }) => {
  return (
    <header className="dashboard-header">
      <div className="metrics-grid">
        <MetricCard
          label="ACTIVE SCANS"
          value={metrics.activeScans}
          loading={loading}
          variant="primary"
        />
        <MetricCard
          label="EXPLOITS FOUND"
          value={metrics.exploitsFound}
          loading={loading}
          variant="warning"
        />
        <MetricCard
          label="TARGETS"
          value={metrics.targets}
          loading={loading}
          variant="info"
        />
        <MetricCard
          label="SESSIONS"
          value={metrics.sessions}
          loading={loading}
          variant="success"
        />
      </div>
    </header>
  );
};
```

### **Exemplo 2: Status Grid (OSINT Overview)**
```jsx
import { ModuleStatusCard } from '@/components/shared/widgets';

const modules = [
  { name: 'AI Engine', status: 'online', activity: 'Analyzing patterns' },
  { name: 'Username Hunter', status: 'running', activity: '2,847 profiles' },
  { name: 'Email Analyzer', status: 'online', activity: '1,293 emails' },
  { name: 'Dark Web Monitor', status: 'degraded', activity: 'API timeout' }
];

const StatusGrid = () => (
  <div className="grid grid-cols-3 gap-4">
    {modules.map((module, idx) => (
      <ModuleStatusCard key={idx} {...module} />
    ))}
  </div>
);
```

### **Exemplo 3: Activity Stream**
```jsx
import { ActivityItem } from '@/components/shared/widgets';

const ActivityStream = ({ activities }) => (
  <div className="activity-stream">
    {activities.slice(0, 5).map(activity => (
      <ActivityItem
        key={activity.id}
        timestamp={activity.timestamp}
        type={activity.type}
        action={activity.action}
        severity={activity.severity}
      />
    ))}
  </div>
);
```

### **Exemplo 4: Panel Completo**
```jsx
import { PanelCard, MetricCard, ActivityItem } from '@/components/shared/widgets';

const ThreatIntelPanel = ({ threats, metrics }) => (
  <PanelCard
    title="THREAT INTELLIGENCE"
    icon="🎯"
    variant="primary"
    actions={<button>🔄 Refresh</button>}
  >
    <div className="metrics-row">
      <MetricCard label="IOCs" value={metrics.iocs} variant="warning" />
      <MetricCard label="Threats" value={metrics.threats} variant="danger" />
    </div>

    <div className="threat-feed">
      {threats.map(threat => (
        <ActivityItem
          key={threat.id}
          timestamp={threat.detected}
          type={threat.source}
          action={threat.description}
          severity={threat.level}
        />
      ))}
    </div>
  </PanelCard>
);
```

---

## 🌍 Internacionalização (i18n)

Todos os widgets suportam i18n através de props:

```jsx
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();

<MetricCard
  label={t('dashboard.offensive.metrics.activeScans')}
  value={metrics.activeScans}
/>

<ModuleStatusCard
  name={t('modules.maximus.name')}
  status="online"
  activity={t('modules.maximus.activity')}
/>
```

---

## ♿ Acessibilidade

Todos os widgets seguem **WCAG 2.1 AA**:

- ✅ **ARIA labels** automáticos
- ✅ **Color contrast** verificado (AA compliant)
- ✅ **Keyboard accessible** (quando interativo)
- ✅ **Screen reader friendly**

**Exemplo com aria-label customizado:**
```jsx
<MetricCard
  label="Active Scans"
  value={42}
  ariaLabel="Active network scans: 42 in progress"
/>
```

---

## 🎨 Customização CSS

### **Override de Estilos**
```jsx
<MetricCard
  label="Custom Metric"
  value={100}
  className="my-custom-metric"
/>

// CSS
.my-custom-metric {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
}
```

### **Variáveis CSS Globais**
```css
:root {
  --metric-card-padding: 1rem;
  --metric-card-border-radius: 8px;
  --metric-card-transition: 0.3s ease;
}
```

---

## 📊 TypeScript Support

**PropTypes** para validação em runtime:

```javascript
import PropTypes from 'prop-types';

MetricCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]).isRequired,
  loading: PropTypes.bool,
  variant: PropTypes.oneOf(['primary', 'success', 'warning', 'danger', 'info']),
  // ...
};
```

---

## 🚀 Performance

- ✅ **Code Splitting:** Widget library = 1.72 kB (gzip: 0.66 kB)
- ✅ **Tree Shaking:** Importar apenas widgets usados
- ✅ **Memoization:** Usar React.memo se necessário
- ✅ **CSS Optimizado:** Classes reutilizáveis

---

## 📦 Estrutura de Arquivos

```
src/components/shared/widgets/
├── MetricCard.jsx
├── MetricCard.css
├── ModuleStatusCard.jsx
├── ModuleStatusCard.css
├── ActivityItem.jsx
├── ActivityItem.css
├── PanelCard.jsx
├── PanelCard.css
└── index.js          # Export centralizado
```

**Import centralizado:**
```javascript
// index.js
export { MetricCard } from './MetricCard';
export { ModuleStatusCard } from './ModuleStatusCard';
export { ActivityItem } from './ActivityItem';
export { PanelCard } from './PanelCard';
```

---

## 🔗 Links Úteis

- **Código fonte:** `/frontend/src/components/shared/widgets/`
- **Relatório de Refatoração:** `/frontend/REFACTORING_REPORT.md`
- **Dashboards usando widgets:**
  - `MaximusDashboard.jsx` (ActivityItem)
  - `OSINTDashboard.jsx` (ModuleStatusCard)
  - `OffensiveDashboard.jsx` (potencial uso futuro)

---

## 📝 Changelog

### v1.0.0 (2025-10-04)
- ✅ Criação inicial da Widget Library
- ✅ 4 widgets base (MetricCard, ModuleStatusCard, ActivityItem, PanelCard)
- ✅ Export centralizado
- ✅ PropTypes completos
- ✅ WCAG 2.1 AA compliance
- ✅ i18n support
- ✅ Responsive design

---

**Autor:** Claude Code (Anthropic)
**Licença:** Projeto Vértice
**Contribuições:** Aberto para melhorias via PR
