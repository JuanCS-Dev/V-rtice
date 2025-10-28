# Components & Hooks API Reference

**Versão**: 1.0.0
**Data**: 2025-01-XX

Documentação completa de componentes compartilhados, hooks customizados e utilitários do projeto VÉRTICE.

---

## 📚 Índice

1. [Hooks](#hooks)
   - [useWebSocket](#usewebsocket)
   - [useKeyboardNavigation](#usekeyboardnavigation)
   - [useFocusTrap](#usefocustrap)
   - [useRateLimit](#useratelimit)
2. [Componentes Compartilhados](#componentes-compartilhados)
   - [ErrorBoundary](#errorboundary)
   - [LanguageSwitcher](#languageswitcher)
   - [SkipLink](#skiplink)
3. [Utilitários](#utilitários)
   - [Security Utils](#security-utils)
   - [Accessibility Utils](#accessibility-utils)
4. [Stores (Zustand)](#stores)
   - [defensiveStore](#defensivestore)
   - [offensiveStore](#offensivestore)

---

## Hooks

### useWebSocket

Hook para conexão WebSocket otimizada com reconexão automática e fallback para polling.

#### Importação

```javascript
import { useWebSocket } from './hooks/useWebSocket';
```

#### Assinatura

```typescript
useWebSocket(
  url: string,
  options?: WebSocketOptions
): WebSocketReturn
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `url` | `string` | **required** | URL do WebSocket |
| `options.reconnect` | `boolean` | `true` | Ativar reconexão automática |
| `options.reconnectInterval` | `number` | `1000` | Intervalo inicial de reconexão (ms) |
| `options.maxReconnectAttempts` | `number` | `5` | Máximo de tentativas de reconexão |
| `options.heartbeatInterval` | `number` | `30000` | Intervalo de heartbeat (ms) |
| `options.heartbeatMessage` | `string` | `{type:'ping'}` | Mensagem de heartbeat |
| `options.onOpen` | `function` | `null` | Callback ao abrir conexão |
| `options.onMessage` | `function` | `null` | Callback ao receber mensagem |
| `options.onClose` | `function` | `null` | Callback ao fechar conexão |
| `options.onError` | `function` | `null` | Callback de erro |
| `options.fallbackToPolling` | `boolean` | `true` | Usar polling após falhas |
| `options.pollingInterval` | `number` | `5000` | Intervalo de polling (ms) |
| `options.debug` | `boolean` | `false` | Modo debug |

#### Retorno

```typescript
{
  data: any | null,           // Última mensagem recebida
  isConnected: boolean,        // Estado da conexão
  error: Error | null,         // Último erro
  send: (data: any) => void,   // Enviar mensagem
  reconnect: () => void,       // Forçar reconexão
  disconnect: () => void       // Desconectar
}
```

#### Exemplo de Uso

```javascript
function RealTimeMetrics() {
  const { data, isConnected, send, error } = useWebSocket(
    'ws://localhost:8000/metrics',
    {
      reconnect: true,
      maxReconnectAttempts: 5,
      onMessage: (msg) => console.log('Received:', msg),
      onError: (err) => console.error('WebSocket error:', err),
      debug: process.env.NODE_ENV === 'development'
    }
  );

  useEffect(() => {
    if (data) {
      console.log('New metrics:', data);
    }
  }, [data]);

  const handleSendCommand = () => {
    send({ type: 'command', action: 'refresh' });
  };

  return (
    <div>
      <div>Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}</div>
      {error && <div>Error: {error.message}</div>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
      <button onClick={handleSendCommand}>Send Command</button>
    </div>
  );
}
```

#### Features

- ✅ **Exponential Backoff**: Reconexão com delay crescente (1s → 2s → 4s → 8s → 30s max)
- ✅ **Heartbeat**: Ping/pong automático a cada 30s
- ✅ **Message Queue**: Armazena mensagens durante desconexão
- ✅ **Polling Fallback**: Muda para HTTP polling após 5 falhas
- ✅ **Error Recovery**: Tratamento robusto de erros

---

### useKeyboardNavigation

Hook para navegação por teclado em listas e menus (WCAG 2.1 compliance).

#### Importação

```javascript
import { useKeyboardNavigation } from './hooks/useKeyboardNavigation';
```

#### Assinatura

```typescript
useKeyboardNavigation(options: KeyboardNavOptions): KeyboardNavReturn
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `itemCount` | `number` | `0` | Número de itens navegáveis |
| `initialIndex` | `number` | `-1` | Índice inicial |
| `onSelect` | `function` | `null` | Callback ao selecionar (Enter/Space) |
| `onEscape` | `function` | `null` | Callback ao pressionar Escape |
| `orientation` | `'vertical' \| 'horizontal' \| 'both'` | `'vertical'` | Orientação da navegação |
| `loop` | `boolean` | `true` | Voltar ao início/fim |
| `autoFocus` | `boolean` | `false` | Auto-focus no primeiro item |

#### Retorno

```typescript
{
  focusedIndex: number,
  setFocusedIndex: (index: number) => void,
  handleKeyDown: (event: KeyboardEvent) => void,
  getItemRef: (index: number) => RefCallback,
  getItemProps: (index: number, additionalProps?: object) => object,
  focusItem: (index: number) => void,
  navigateNext: () => void,
  navigatePrevious: () => void,
  navigateFirst: () => void,
  navigateLast: () => void
}
```

#### Exemplo de Uso

```javascript
function DropdownMenu({ items, onSelect }) {
  const { getItemProps, focusedIndex } = useKeyboardNavigation({
    itemCount: items.length,
    onSelect: (index) => onSelect(items[index]),
    orientation: 'vertical',
    loop: true
  });

  return (
    <ul role="menu">
      {items.map((item, index) => (
        <li
          key={item.id}
          {...getItemProps(index, {
            role: 'menuitem',
            onClick: () => onSelect(item)
          })}
          className={focusedIndex === index ? 'focused' : ''}
        >
          {item.label}
        </li>
      ))}
    </ul>
  );
}
```

#### Teclas Suportadas

| Tecla | Ação (Vertical) | Ação (Horizontal) |
|-------|-----------------|-------------------|
| `↓ ArrowDown` | Próximo item | - |
| `↑ ArrowUp` | Item anterior | - |
| `→ ArrowRight` | - | Próximo item |
| `← ArrowLeft` | - | Item anterior |
| `Home` | Primeiro item | Primeiro item |
| `End` | Último item | Último item |
| `Enter / Space` | Selecionar | Selecionar |
| `Escape` | Fechar/cancelar | Fechar/cancelar |

---

### useFocusTrap

Hook para prender foco dentro de um container (modals, dialogs).

#### Importação

```javascript
import { useFocusTrap } from './hooks/useFocusTrap';
```

#### Assinatura

```typescript
useFocusTrap(options: FocusTrapOptions): RefObject
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `active` | `boolean` | `true` | Ativar focus trap |
| `autoFocus` | `boolean` | `true` | Auto-focus no primeiro elemento |
| `returnFocus` | `boolean` | `true` | Retornar foco ao fechar |
| `onEscape` | `function` | `null` | Callback ao pressionar Escape |
| `allowOutsideClick` | `boolean` | `false` | Permitir clique fora |

#### Retorno

```typescript
RefObject<HTMLElement> // Ref para o container
```

#### Exemplo de Uso

```javascript
function Modal({ isOpen, onClose, children }) {
  const trapRef = useFocusTrap({
    active: isOpen,
    autoFocus: true,
    returnFocus: true,
    onEscape: onClose,
    allowOutsideClick: true
  });

  if (!isOpen) return null;

  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div
        ref={trapRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="modal"
      >
        <h2 id="modal-title">Modal Title</h2>
        {children}
        <button onClick={onClose}>Close</button>
      </div>
    </>
  );
}
```

---

### useRateLimit

Hook para rate limiting client-side (Token Bucket algorithm).

#### Importação

```javascript
import { useRateLimit } from './hooks/useRateLimit';
```

#### Assinatura

```typescript
useRateLimit(key: string, options?: RateLimitOptions): RateLimitReturn
```

#### Parâmetros

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `key` | `string` | **required** | Identificador único |
| `options.maxRequests` | `number` | `60` | Máximo de requests |
| `options.windowMs` | `number` | `60000` | Janela de tempo (ms) |
| `options.skipSuccessful` | `boolean` | `false` | Não contar requests bem-sucedidos |
| `options.skipFailed` | `boolean` | `false` | Não contar requests falhados |

#### Retorno

```typescript
{
  execute: (fn: () => Promise<any>) => Promise<any>,
  remaining: number,
  resetIn: number,
  isLimited: boolean
}
```

#### Exemplo de Uso

```javascript
function SearchComponent() {
  const { execute, remaining, resetIn } = useRateLimit('search-api', {
    maxRequests: 10,
    windowMs: 60000 // 10 requests por minuto
  });

  const handleSearch = async (query) => {
    try {
      const results = await execute(async () => {
        const res = await fetch(`/api/search?q=${query}`);
        return res.json();
      });

      console.log('Results:', results);
    } catch (error) {
      if (error.message.includes('Rate limit')) {
        alert(`Rate limit exceeded. Try again in ${resetIn}s`);
      }
    }
  };

  return (
    <div>
      <input onChange={(e) => handleSearch(e.target.value)} />
      <small>{remaining} searches remaining</small>
    </div>
  );
}
```

---

## Componentes Compartilhados

### ErrorBoundary

Componente para capturar erros React e exibir fallback UI.

#### Importação

```javascript
import ErrorBoundary from './components/ErrorBoundary';
```

#### Props

| Prop | Tipo | Padrão | Descrição |
|------|------|--------|-----------|
| `children` | `ReactNode` | **required** | Componentes filhos |
| `fallback` | `ReactNode` | `null` | UI customizada de erro |
| `onError` | `function` | `null` | Callback de erro |
| `onReset` | `function` | `null` | Callback de reset |
| `context` | `string` | `'unknown'` | Contexto do erro |
| `title` | `string` | `'Error'` | Título do erro |

#### Exemplo de Uso

```javascript
function App() {
  return (
    <ErrorBoundary
      context="app-root"
      title="Application Error"
      onError={(error, errorInfo) => {
        console.error('Caught error:', error);
        // Send to logging service
      }}
    >
      <Dashboard />
    </ErrorBoundary>
  );
}

// Custom fallback
<ErrorBoundary
  fallback={({ error, resetError }) => (
    <div>
      <h1>Oops! {error.message}</h1>
      <button onClick={resetError}>Try Again</button>
    </div>
  )}
>
  <MyComponent />
</ErrorBoundary>
```

#### Features

- ✅ Captura erros durante render, lifecycle, construtores
- ✅ Telemetria automática (POST /api/errors/log)
- ✅ Retry mechanism
- ✅ Error count tracking (warn após 2+ erros)
- ✅ Custom fallback UI

---

### LanguageSwitcher

Seletor de idioma com dropdown e suporte completo a acessibilidade.

#### Importação

```javascript
import { LanguageSwitcher } from './components/shared/LanguageSwitcher';
```

#### Props

| Prop | Tipo | Padrão | Descrição |
|------|------|--------|-----------|
| `position` | `'top-right' \| 'top-left' \| 'bottom-right' \| 'bottom-left'` | `'top-right'` | Posição do seletor |

#### Exemplo de Uso

```javascript
function App() {
  return (
    <>
      <LanguageSwitcher position="top-right" />
      <MainContent />
    </>
  );
}
```

#### Features

- ✅ Detecção automática de idioma (browser → localStorage)
- ✅ Dropdown animado com flags
- ✅ Keyboard navigation (↑ ↓ Enter Escape)
- ✅ Focus trap
- ✅ Screen reader announcements
- ✅ ARIA completo (listbox pattern)
- ✅ Persistência em localStorage

#### Idiomas Suportados

- 🇧🇷 Português (Brasil) - `pt-BR`
- 🇺🇸 English (US) - `en-US`

---

### SkipLink

Link para pular navegação e ir direto ao conteúdo principal (WCAG 2.4.1).

#### Importação

```javascript
import { SkipLink } from './components/shared/SkipLink';
```

#### Props

| Prop | Tipo | Padrão | Descrição |
|------|------|--------|-----------|
| `href` | `string` | `'#main-content'` | ID do elemento alvo |
| `children` | `ReactNode` | `'Skip to main content'` | Texto do link |
| `className` | `string` | `''` | Classe CSS adicional |

#### Exemplo de Uso

```javascript
function App() {
  return (
    <>
      <SkipLink href="#main-content">Skip to main content</SkipLink>
      <nav>{/* Navigation */}</nav>
      <main id="main-content">
        {/* Main content */}
      </main>
    </>
  );
}
```

#### Features

- ✅ Visível apenas no keyboard focus
- ✅ High contrast focus indicator
- ✅ Smooth scroll
- ✅ Auto-focus no target
- ✅ Suporte a reduced motion

---

## Utilitários

### Security Utils

Utilitários de segurança (XSS, SQL injection, rate limiting).

#### Importação

```javascript
import {
  escapeHTML,
  sanitizeSQLInput,
  isValidEmail,
  sanitizeCVEId,
  OWASP
} from './utils/security';
```

#### API

```javascript
// XSS Prevention
const safe = escapeHTML('<script>alert(1)</script>');
// "&lt;script&gt;alert(1)&lt;/script&gt;"

// SQL Injection Prevention
const safe = sanitizeSQLInput("'; DROP TABLE users--");
// "DROP TABLE users"

// Email Validation
const valid = isValidEmail('user@example.com'); // true

// CVE ID Sanitization
const cve = sanitizeCVEId('cve-2024-1234'); // "CVE-2024-1234"

// OWASP Helpers
const safe = OWASP.preventXSS('<img src=x onerror=alert(1)>');
const masked = OWASP.maskSensitiveData('1234567890', 4); // "******7890"
```

Veja [SECURITY_HARDENING.md](./SECURITY_HARDENING.md) para documentação completa.

---

### Accessibility Utils

Utilitários de acessibilidade (screen reader, focus, contrast).

#### Importação

```javascript
import {
  announcer,
  focusElement,
  getContrastRatio,
  meetsContrastAA,
  skipToMain,
  validateAccessibility
} from './utils/accessibility';
```

#### API

```javascript
// Screen Reader Announcements
announcer.announce('Settings saved', 'polite');
announcer.announceError('Failed to load');
announcer.announceSuccess('Upload complete');

// Focus Management
focusElement('#search-input');
const first = getFirstFocusable(containerEl);

// Color Contrast
const ratio = getContrastRatio('#00f0ff', '#0a1929'); // 8.2
const passes = meetsContrastAA('#00f0ff', '#0a1929'); // true

// Skip to Main
skipToMain(); // Focus main content

// Validation
const results = validateAccessibility.runAll();
// { skipLink: true, images: { pass: true }, ... }
```

Veja [ACCESSIBILITY_IMPLEMENTATION.md](./ACCESSIBILITY_IMPLEMENTATION.md) para documentação completa.

---

## Stores

### defensiveStore

Zustand store para operações defensivas.

#### Importação

```javascript
import { useDefensiveStore } from './stores/defensiveStore';
```

#### State

```typescript
{
  metrics: {
    threats: number,
    suspiciousIPs: number,
    domains: number,
    monitored: number
  },
  alerts: Alert[],
  activeModule: string | null,
  lastUpdate: string | null
}
```

#### Actions

```javascript
// Get state
const metrics = useDefensiveStore(state => state.metrics);
const alerts = useDefensiveStore(state => state.alerts);

// Set state
const setMetrics = useDefensiveStore(state => state.setMetrics);
const addAlert = useDefensiveStore(state => state.addAlert);
const setActiveModule = useDefensiveStore(state => state.setActiveModule);
const clearAlerts = useDefensiveStore(state => state.clearAlerts);

// Usage
setMetrics({ threats: 42, suspiciousIPs: 15, ... });
addAlert({ id: 1, message: 'New threat detected', severity: 'high' });
```

#### Features

- ✅ DevTools integration
- ✅ LocalStorage persistence (activeModule)
- ✅ Auto-update timestamp
- ✅ Alert management (max 50)

Veja [STATE_MANAGEMENT_IMPROVEMENTS.md](./STATE_MANAGEMENT_IMPROVEMENTS.md) para documentação completa.

---

### offensiveStore

Zustand store para operações ofensivas.

Similar ao `defensiveStore`, veja documentação em [STATE_MANAGEMENT_IMPROVEMENTS.md](./STATE_MANAGEMENT_IMPROVEMENTS.md).

---

## 🧪 Testes

Todos os componentes e hooks possuem testes unitários. Veja:

- [ErrorBoundary.test.jsx](./src/components/ErrorBoundary.test.jsx)
- [useWebSocket.test.js](./src/hooks/useWebSocket.test.js)
- [defensiveStore.test.js](./src/stores/defensiveStore.test.js)
- [security.test.js](./src/utils/security.test.js)

Execute testes:

```bash
npm test                    # Run all tests
npm test -- --coverage      # With coverage
npm test -- --ui            # Interactive UI
```

---

## 📚 Documentação Adicional

- [PERFORMANCE_IMPROVEMENTS_LOG.md](./PERFORMANCE_IMPROVEMENTS_LOG.md) - Error boundaries, WebSocket, React.memo
- [STATE_MANAGEMENT_IMPROVEMENTS.md](./STATE_MANAGEMENT_IMPROVEMENTS.md) - Zustand + React Query
- [TESTING_COVERAGE_IMPLEMENTATION.md](./TESTING_COVERAGE_IMPLEMENTATION.md) - Vitest setup
- [SECURITY_HARDENING.md](./SECURITY_HARDENING.md) - OWASP Top 10
- [I18N_IMPLEMENTATION.md](./I18N_IMPLEMENTATION.md) - Internacionalização
- [ACCESSIBILITY_IMPLEMENTATION.md](./ACCESSIBILITY_IMPLEMENTATION.md) - WCAG 2.1 AA

---

**Versão**: 1.0.0
**Última Atualização**: 2025-01-XX
**Mantenedores**: Claude Code
