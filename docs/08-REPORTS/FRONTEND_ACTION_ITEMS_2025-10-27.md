# 🎯 ACTION ITEMS - FRONTEND VÉRTICE
**Data:** 2025-10-27 | **Status:** Ready to Execute

---

## 🔴 PRIORIDADE CRÍTICA - FAZER HOJE (2.5h)

### C01: Remover IPs Hardcoded (30 min)

**Arquivos a modificar:**
1. `/home/juan/vertice-dev/frontend/src/components/reactive-fabric/HITLDecisionConsole.jsx` (linha 86)
2. `/home/juan/vertice-dev/frontend/src/components/maximus/EurekaPanel.jsx` (linha 143)

**Código Atual:**
```javascript
// ❌ HITLDecisionConsole.jsx:86
const ws = new WebSocket(`ws://34.148.161.131:8000/ws/${username}`);

// ❌ EurekaPanel.jsx:143
ws = new WebSocket('ws://34.148.161.131:8000/ws/wargaming');
```

**Código Correto:**
```javascript
// ✅ HITLDecisionConsole.jsx
import { WS_ENDPOINTS } from '@/config/api';
const ws = new WebSocket(`${WS_ENDPOINTS.hitl}/${username}`);

// ✅ EurekaPanel.jsx
import { WS_ENDPOINTS } from '@/config/api';
ws = new WebSocket(WS_ENDPOINTS.maximus); // ou criar WS_ENDPOINTS.wargaming
```

**Validação:**
```bash
# Após mudança, verificar se não há mais IPs hardcoded:
grep -r "148.161.131" frontend/src --include="*.jsx" --include="*.js"
# Deve retornar vazio
```

**Impacto:** CRÍTICO - Serviço não funcionará se IP mudar ou infraestrutura migrar.

---

### C02: Substituir console.error() por logger (2h)

**Arquivos a modificar (~20 arquivos):**

#### Grupo 1: Reactive Fabric (6 erros)
```javascript
// ❌ ANTES
// reactive-fabric/ReactiveFabricDashboard.jsx:48,58,68
console.error('Failed to fetch honeypot status:', err);
console.error('Failed to fetch threat events:', err);
console.error('Failed to fetch intelligence fusion:', err);

// reactive-fabric/HITLDecisionConsole.jsx:66,76,86,113,124,135
console.error('Failed to fetch pending decisions:', err);
console.error('Failed to fetch stats:', err);
console.error('WebSocket error:', error);
console.error('Failed to approve decision:', err);
console.error('Failed to reject decision:', err);
console.error('Failed to escalate decision:', err);
```

```javascript
// ✅ DEPOIS
import logger from '@/utils/logger';

logger.error('Failed to fetch honeypot status:', { error: err });
logger.error('Failed to fetch threat events:', { error: err });
logger.error('Failed to fetch intelligence fusion:', { error: err });
logger.error('Failed to fetch pending decisions:', { error: err });
logger.error('Failed to fetch stats:', { error: err });
logger.error('WebSocket error:', { error });
logger.error('Failed to approve decision:', { error: err });
logger.error('Failed to reject decision:', { error: err });
logger.error('Failed to escalate decision:', { error: err });
```

#### Grupo 2: HITL Console (5 erros)
```javascript
// ❌ ANTES
// admin/HITLConsole/hooks/useWebSocket.js:35,43,49,57,63
console.warn('[useWebSocket] Cannot send message: WebSocket not connected');
console.error('[useWebSocket] Failed to parse message:', error);
console.error('[useWebSocket] Error:', error);
console.error('[useWebSocket] Max reconnection attempts reached');
console.error('[useWebSocket] Failed to create WebSocket:', error);
```

```javascript
// ✅ DEPOIS
import logger from '@/utils/logger';

logger.warn('[useWebSocket] Cannot send message: WebSocket not connected');
logger.error('[useWebSocket] Failed to parse message:', { error });
logger.error('[useWebSocket] Error:', { error });
logger.error('[useWebSocket] Max reconnection attempts reached');
logger.error('[useWebSocket] Failed to create WebSocket:', { error });
```

#### Grupo 3: Cockpit Soberano (5 erros)
```javascript
// ❌ ANTES
// dashboards/CockpitSoberano/components/CommandConsole/CommandConsole.jsx:34
console.error('[CommandConsole] Command failed:', err);

// dashboards/CockpitSoberano/hooks/useCockpitMetrics.js
console.error('[CockpitMetrics] Failed to fetch:', err);

// dashboards/CockpitSoberano/hooks/useCommandBus.js
console.error('[CommandBus] Failed to get status:', err);

// dashboards/CockpitSoberano/hooks/useVerdictStream.js (2x)
console.error('[VerdictStream] Failed to parse verdict:', err);
console.error('[VerdictStream] WebSocket error:', err);
```

```javascript
// ✅ DEPOIS
import logger from '@/utils/logger';

logger.error('[CommandConsole] Command failed:', { error: err });
logger.error('[CockpitMetrics] Failed to fetch:', { error: err });
logger.error('[CommandBus] Failed to get status:', { error: err });
logger.error('[VerdictStream] Failed to parse verdict:', { error: err });
logger.error('[VerdictStream] WebSocket error:', { error: err });
```

#### Grupo 4: Admin Dashboard (2 erros)
```javascript
// ❌ ANTES
// components/admin/HITLConsole/components/DecisionPanel.jsx:34
console.error('Decision failed:', err);
```

```javascript
// ✅ DEPOIS
import logger from '@/utils/logger';

logger.error('Decision failed:', { error: err });
```

**Script de Busca e Substituição (Opcional):**
```bash
#!/bin/bash
# find_console_errors.sh

echo "Procurando console.error() em produção..."

find frontend/src -type f \( -name "*.js" -o -name "*.jsx" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/test/*" \
  -not -path "*/__tests__/*" \
  -exec grep -l "console\.error\|console\.warn" {} \; | \
  grep -v "test.jsx" | \
  sort

echo ""
echo "Total de arquivos com console.error/warn:"
find frontend/src -type f \( -name "*.js" -o -name "*.jsx" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/test/*" \
  -not -path "*/__tests__/*" \
  -exec grep -l "console\.error\|console\.warn" {} \; | \
  grep -v "test.jsx" | \
  wc -l
```

**Validação:**
```bash
# Após mudanças, verificar que não há mais console.error() fora de testes:
grep -r "console\.error" frontend/src --include="*.jsx" --include="*.js" | \
  grep -v test | \
  grep -v node_modules | \
  grep -v "// ✅" # comentários OK
# Deve retornar apenas linhas de teste
```

**Impacto:** ALTO - Console poluído em produção, possível exposição de informações sensíveis.

---

## ⚠️ PRIORIDADE ALTA - FAZER ESTA SEMANA (6.5h)

### A01: Otimizar Bundle Size (1h)

**Arquivo a modificar:**
`/home/juan/vertice-dev/frontend/vite.config.js`

**Adicionar:**
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],

  // ✅ ADICIONAR ESTA SEÇÃO
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React core
          'vendor-react': ['react', 'react-dom'],

          // State management
          'vendor-query': ['@tanstack/react-query'],
          'vendor-store': ['zustand'],

          // Visualization (HEAVY)
          'vendor-viz': ['d3', 'leaflet', 'leaflet.heat', 'leaflet.markercluster'],
          'vendor-charts': ['recharts'],

          // i18n
          'vendor-i18n': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],

          // UI Components
          'vendor-ui': ['@radix-ui/react-label', '@radix-ui/react-slot', '@radix-ui/react-switch', '@radix-ui/react-toast'],

          // Terminal (HEAVY)
          'vendor-terminal': ['@xterm/xterm', '@xterm/addon-fit', '@xterm/addon-search', '@xterm/addon-web-links'],

          // Utils
          'vendor-utils': ['axios', 'clsx', 'tailwind-merge'],
        },
      },
    },

    // Increase chunk size warning limit (temporário)
    chunkSizeWarningLimit: 1000,
  },

  // ... resto da config
})
```

**Validação:**
```bash
npm run build

# Verificar que agora há múltiplos chunks:
ls -lh dist/assets/vendor-*.js

# Esperado:
# vendor-react-*.js    ~150KB
# vendor-viz-*.js      ~350KB
# vendor-terminal-*.js ~200KB
# vendor-query-*.js    ~100KB
# index-*.js           ~600KB (antes era 1.6MB)
```

**Benefício:** Redução de 40-50% no bundle inicial, melhor caching.

---

### A02: Implementar manifest.json (1h)

**Criar arquivo:**
`/home/juan/vertice-dev/frontend/public/manifest.json`

```json
{
  "name": "Vértice - Cybersecurity Platform",
  "short_name": "Vértice",
  "description": "Advanced Cybersecurity Operations Platform with AI-powered threat intelligence",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0e1a",
  "theme_color": "#00ff41",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "categories": ["security", "productivity", "utilities"],
  "screenshots": [
    {
      "src": "/screenshots/desktop-home.png",
      "sizes": "1920x1080",
      "type": "image/png",
      "form_factor": "wide"
    },
    {
      "src": "/screenshots/mobile-home.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow"
    }
  ],
  "lang": "pt-BR",
  "dir": "ltr",
  "prefer_related_applications": false
}
```

**Adicionar ao index.html:**
```html
<!-- /home/juan/vertice-dev/frontend/index.html -->
<head>
  <!-- ... existing tags ... -->

  <!-- ✅ ADICIONAR PWA MANIFEST -->
  <link rel="manifest" href="/manifest.json">

  <!-- iOS Meta Tags -->
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Vértice">
  <link rel="apple-touch-icon" href="/icons/icon-192x192.png">

  <!-- Theme Color -->
  <meta name="theme-color" content="#00ff41">
</head>
```

**Criar ícones:**
```bash
# Você precisará gerar os ícones a partir do logo Vértice
# Ferramentas recomendadas:
# - https://realfavicongenerator.net/
# - https://www.pwabuilder.com/imageGenerator

mkdir -p frontend/public/icons
# Colocar os ícones gerados aqui
```

**Validação:**
```bash
# Testar manifest válido:
npm run build
npm run preview

# Abrir DevTools > Application > Manifest
# Deve aparecer sem erros
```

---

### A03: Adicionar CSP Headers (30 min)

**Opção 1: Meta Tag (desenvolvimento)**
`/home/juan/vertice-dev/frontend/index.html`

```html
<head>
  <!-- ... existing tags ... -->

  <!-- ✅ ADICIONAR CSP -->
  <meta http-equiv="Content-Security-Policy"
        content="
          default-src 'self';
          connect-src 'self'
            wss://api.vertice-maximus.com
            https://api.vertice-maximus.com
            ws://localhost:*
            http://localhost:*;
          script-src 'self' 'unsafe-inline' 'unsafe-eval';
          style-src 'self' 'unsafe-inline';
          img-src 'self' data: blob: https:;
          font-src 'self' data:;
          frame-src 'none';
          object-src 'none';
          base-uri 'self';
          form-action 'self';
        ">
</head>
```

**Opção 2: Server Headers (produção - recomendado)**

Se estiver usando Cloud Run:
```yaml
# /home/juan/vertice-dev/.gcloudignore ou configurar no Cloud Run
# Adicionar headers via nginx ou Cloud Run config:

Content-Security-Policy: default-src 'self'; connect-src 'self' wss://api.vertice-maximus.com https://api.vertice-maximus.com; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:;
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Validação:**
```bash
# Verificar CSP funcionando:
curl -I https://vertice-frontend-172846394274.us-east1.run.app

# Ou no DevTools > Network > Headers
# Procurar por Content-Security-Policy
```

---

### A04: Ajustar Testes com Falha (4h)

**Testes falhando:** 122 testes (24 arquivos)

**Estratégia:**
1. Categorizar falhas (30 min)
2. Corrigir snapshots desatualizados (1h)
3. Ajustar mocks de backend (1.5h)
4. Resolver timing issues (1h)

**Comandos:**
```bash
# 1. Rodar testes e ver falhas detalhadas
npm run test:run > test_output.txt

# 2. Atualizar snapshots
npm run test -- -u

# 3. Rodar testes específicos
npm run test -- VirtualizedExecutionsList.test.jsx

# 4. Coverage report
npm run test:coverage
```

**Arquivos com mais falhas (priorizar):**
- `VirtualizedExecutionsList.test.jsx` (múltiplas falhas de texto não encontrado)
- Testes de integração de dashboards

**Nota:** Estas falhas **não afetam produção**, são apenas testes desatualizados.

---

## 🟡 PRIORIDADE MÉDIA - FAZER ESTE MÊS (2 dias)

### M01: Centralizar WebSocket Management (2h)

**Objetivo:** Migrar WebSockets diretos para hook centralizado

**Arquivos a refatorar:**
1. `dashboards/CockpitSoberano/hooks/useVerdictStream.js`
2. `components/admin/HITLConsole/hooks/useWebSocket.js`

**Antes:**
```javascript
// ❌ useVerdictStream.js:24
const ws = new WebSocket(WS_URL);
```

**Depois:**
```javascript
// ✅ useVerdictStream.js
import { useWebSocket } from '@/hooks/useWebSocket';

const { data, isConnected, error } = useWebSocket(WS_URL, {
  reconnect: true,
  heartbeat: true,
  onMessage: (data) => {
    // Handle verdict data
  },
});
```

**Benefícios:**
- Reconnection automática
- Heartbeat/keepalive
- Error handling consistente
- Código DRY

---

### M02: Melhorar Empty States (2h)

**Criar componente:**
`/home/juan/vertice-dev/frontend/src/components/shared/EmptyState.jsx`

```javascript
/**
 * EmptyState - Componente reutilizável para estados vazios
 */
import React from 'react';
import PropTypes from 'prop-types';

export const EmptyState = ({
  icon = '📭',
  title = 'Nenhum dado disponível',
  description = 'Não há informações para exibir no momento.',
  action = null,
  illustration = null
}) => {
  return (
    <div className="empty-state">
      {illustration ? (
        <div className="empty-illustration">{illustration}</div>
      ) : (
        <div className="empty-icon" aria-hidden="true">{icon}</div>
      )}

      <h3 className="empty-title">{title}</h3>
      <p className="empty-description">{description}</p>

      {action && (
        <div className="empty-action">
          {action}
        </div>
      )}
    </div>
  );
};

EmptyState.propTypes = {
  icon: PropTypes.string,
  title: PropTypes.string,
  description: PropTypes.string,
  action: PropTypes.node,
  illustration: PropTypes.node,
};
```

**Usar em:**
- Listas vazias (executions, alerts, threats)
- Dashboards sem dados
- Resultados de busca vazios

---

### M03: Testes E2E Básicos (1 dia)

**Instalar Playwright:**
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

**Criar testes:**
`/home/juan/vertice-dev/frontend/e2e/critical-paths.spec.js`

```javascript
import { test, expect } from '@playwright/test';

test.describe('Critical User Paths', () => {
  test('Landing page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('VÉRTICE');
  });

  test('Navigate to Offensive Dashboard', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Offensive Operations');
    await expect(page.locator('h2')).toContainText('OFFENSIVE');
  });

  test('Navigate to Defensive Dashboard', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Defensive Operations');
    await expect(page.locator('h2')).toContainText('DEFENSIVE');
  });

  test('MAXIMUS Dashboard loads', async ({ page }) => {
    await page.goto('/');
    await page.click('text=MAXIMUS');
    await expect(page.locator('h2')).toContainText('MAXIMUS');
  });
});
```

**Rodar:**
```bash
npx playwright test
npx playwright test --ui # modo interativo
```

---

## 🟢 PRIORIDADE BAIXA - BACKLOG (2 semanas)

### L01: Otimizar Responsividade Mobile (1 semana)

**Testar em:**
- iPhone SE (375px)
- iPhone 12 (390px)
- Pixel 5 (393px)
- iPad (768px)

**Ajustar:**
- Dashboards (grid responsivo)
- Modals (full-screen em mobile)
- Tabelas (scroll horizontal)
- Navegação (hamburger menu)

---

### L02: Adicionar Storybook (2 dias)

**Instalar:**
```bash
cd frontend
npx storybook@latest init
```

**Documentar:**
- Componentes UI (Button, Card, Badge, etc.)
- Componentes shared (ErrorBoundary, Toast, etc.)
- Widgets (MetricCard, ChartWidget, etc.)

---

## 📋 CHECKLIST DE EXECUÇÃO

### Dia 1 (Hoje - 2.5h)
- [ ] C01: Remover IPs hardcoded (30 min)
  - [ ] HITLDecisionConsole.jsx
  - [ ] EurekaPanel.jsx
  - [ ] Validar: `grep -r "148.161.131"`
- [ ] C02: Substituir console.error() (2h)
  - [ ] Reactive Fabric (6 arquivos)
  - [ ] HITL Console (5 arquivos)
  - [ ] Cockpit Soberano (5 arquivos)
  - [ ] Admin Dashboard (2 arquivos)
  - [ ] Validar: `grep -r "console\.error" | grep -v test`

### Semana 1 (Esta Semana - 6.5h)
- [ ] A01: Otimizar Bundle Size (1h)
  - [ ] vite.config.js manualChunks
  - [ ] Build e validar chunks
- [ ] A02: Implementar manifest.json (1h)
  - [ ] Criar manifest.json
  - [ ] Adicionar ao index.html
  - [ ] Gerar ícones PWA
- [ ] A03: Adicionar CSP Headers (30 min)
  - [ ] Meta tag ou server headers
  - [ ] Validar no DevTools
- [ ] A04: Ajustar Testes (4h)
  - [ ] Atualizar snapshots
  - [ ] Corrigir mocks
  - [ ] Resolver timing issues

### Mês 1 (Este Mês - 2 dias)
- [ ] M01: Centralizar WebSocket (2h)
- [ ] M02: Melhorar Empty States (2h)
- [ ] M03: Testes E2E (1 dia)

### Backlog (Próximos meses)
- [ ] L01: Mobile otimizado (1 semana)
- [ ] L02: Storybook (2 dias)

---

## 🚀 QUICK WIN - 1 COMANDO

Se você quiser fazer tudo de uma vez (não recomendado, mas possível):

```bash
#!/bin/bash
# quick_fix_critical.sh

echo "🔴 Executando correções críticas..."

# C01: Remover IPs hardcoded
sed -i 's|ws://34.148.161.131:8000|${WS_ENDPOINTS.hitl}|g' \
  frontend/src/components/reactive-fabric/HITLDecisionConsole.jsx

sed -i 's|ws://34.148.161.131:8000/ws/wargaming|${WS_ENDPOINTS.maximus}|g' \
  frontend/src/components/maximus/EurekaPanel.jsx

# C02: Substituir console.error() (apenas alguns exemplos)
find frontend/src/components/reactive-fabric -type f -name "*.jsx" \
  -exec sed -i "s|console.error(|logger.error(|g" {} \;

echo "✅ Correções críticas aplicadas!"
echo "⚠️  ATENÇÃO: Revisar manualmente os imports de logger!"
```

**⚠️ NÃO USE O SCRIPT ACIMA SEM REVISAR!**
É melhor fazer manualmente para garantir qualidade.

---

## 📊 PROGRESSO TRACKING

Copie este template para um novo arquivo e vá marcando:

```markdown
# Frontend Vértice - Progresso de Correções
Data Início: ___________

## CRÍTICO ⏱️ 2.5h
- [ ] C01: IPs hardcoded (30 min) - Status: _____
- [ ] C02: console.error() (2h) - Status: _____

## ALTO ⏱️ 6.5h
- [ ] A01: Bundle size (1h) - Status: _____
- [ ] A02: manifest.json (1h) - Status: _____
- [ ] A03: CSP headers (30 min) - Status: _____
- [ ] A04: Testes (4h) - Status: _____

## MÉDIO ⏱️ 2 dias
- [ ] M01: WebSocket (2h) - Status: _____
- [ ] M02: Empty states (2h) - Status: _____
- [ ] M03: E2E tests (1 dia) - Status: _____

Data Conclusão: ___________
```

---

**Preparado por:** Claude Code (Sonnet 4.5)
**Data:** 2025-10-27
**Para:** Juan (Developer)

**Próximo Passo:** Começar por C01 e C02 (CRÍTICO) 🚀
