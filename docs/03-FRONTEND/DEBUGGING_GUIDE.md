# 🔍 GUIA DE DEBUGGING - FRONTEND VÉRTICE

## 📋 Índice

1. [Setup de Ferramentas](#setup-de-ferramentas)
2. [Debugging React](#debugging-react)
3. [Debugging CSS](#debugging-css)
4. [Debugging Performance](#debugging-performance)
5. [Debugging API](#debugging-api)
6. [Problemas Comuns](#problemas-comuns)
7. [Logs e Monitoramento](#logs-e-monitoramento)

---

## 🛠️ SETUP DE FERRAMENTAS

### React DevTools

**Instalação:**
- Chrome: https://chrome.google.com/webstore (React Developer Tools)
- Firefox: https://addons.mozilla.org/firefox (React Developer Tools)

**Uso:**
```
1. Abra DevTools (F12)
2. Aba "Components" - Árvore de componentes
3. Aba "Profiler" - Performance profiling
```

**Dicas:**
- Clique em componente para ver props/state
- Use "Highlight Updates" para ver re-renders
- Use filtro para encontrar componentes específicos

### Vite DevServer

**Console Warnings:**
```bash
# Desabilitar warnings específicos em desenvolvimento
# vite.config.js
export default {
  server: {
    hmr: {
      overlay: true  // Mostra erros em overlay
    }
  }
}
```

### ESLint + Prettier

```bash
# Verificar problemas
npm run lint

# Autofix
npm run lint:fix
```

---

## ⚛️ DEBUGGING REACT

### 1. Componente Não Renderiza

**Checklist:**
```jsx
// ✅ Exportado corretamente?
export const Component = () => { };
export default Component;

// ✅ Importado corretamente?
import { Component } from './Component';
// ou
import Component from './Component';

// ✅ Usado corretamente?
<Component />  // ✅
<component />  // ❌ Minúsculo = HTML tag
```

**Debug:**
```jsx
const Component = (props) => {
  console.log('Component rendered with props:', props);

  // Verifica se está retornando JSX
  return (
    <div>Content</div>
  );
};
```

### 2. Props Não Chegam

**Debug:**
```jsx
// No componente pai
<ChildComponent
  prop1={value1}
  prop2={value2}
  {...console.log('Sending props:', { prop1: value1, prop2: value2 })}
/>

// No componente filho
const ChildComponent = (props) => {
  console.log('Received props:', props);
  console.table(props);  // Tabela formatada

  const { prop1, prop2 } = props;
  console.log('Destructured:', { prop1, prop2 });

  return <div>{prop1}</div>;
};
```

### 3. Estado Não Atualiza

**Problema Comum:**
```jsx
// ❌ ERRADO - Mutação direta
const handleClick = () => {
  state.push(item);
  setState(state);  // Não atualiza!
};

// ✅ CORRETO - Novo objeto/array
const handleClick = () => {
  setState([...state, item]);
};

// ✅ CORRETO - Functional update
const handleClick = () => {
  setState(prev => [...prev, item]);
};
```

**Debug:**
```jsx
const [state, setState] = useState(initialValue);

const updateState = (newValue) => {
  console.log('Estado ANTES:', state);
  setState(newValue);
  console.log('Estado DEPOIS (pode não estar atualizado ainda):', state);
};

// Verificar atualização
useEffect(() => {
  console.log('Estado MUDOU para:', state);
}, [state]);
```

### 4. Re-renders Infinitos

**Causa Comum:**
```jsx
// ❌ ERRADO - Dependência que sempre muda
useEffect(() => {
  fetchData();
}, [{ filter: value }]);  // Novo objeto a cada render

// ✅ CORRETO - Dependências primitivas
useEffect(() => {
  fetchData();
}, [value]);

// ❌ ERRADO - Callback sem memoização
const callback = () => console.log('hi');
useEffect(() => {
  doSomething(callback);
}, [callback]);  // Nova função a cada render

// ✅ CORRETO - useCallback
const callback = useCallback(() => {
  console.log('hi');
}, []);

useEffect(() => {
  doSomething(callback);
}, [callback]);
```

**Debug:**
```jsx
// Detectar re-renders excessivos
const Component = (props) => {
  const renderCount = useRef(0);
  renderCount.current++;

  console.log(`Component rendered ${renderCount.current} times`);
  console.log('Props:', props);

  // Detectar qual prop mudou
  const prevProps = useRef(props);
  useEffect(() => {
    Object.keys(props).forEach(key => {
      if (props[key] !== prevProps.current[key]) {
        console.log(`Prop "${key}" mudou:`, {
          old: prevProps.current[key],
          new: props[key]
        });
      }
    });
    prevProps.current = props;
  });

  return <div>Content</div>;
};
```

### 5. useEffect Não Executa

**Checklist:**
```jsx
// ✅ Array de dependências presente?
useEffect(() => {
  console.log('Runs on every render');
});  // ❌ Sem array = executa sempre

useEffect(() => {
  console.log('Runs once on mount');
}, []);  // ✅ Array vazio = executa 1x

useEffect(() => {
  console.log('Runs when dep changes');
}, [dep]);  // ✅ Com dependências

// ✅ Cleanup retornado?
useEffect(() => {
  const timer = setTimeout(() => {}, 1000);

  return () => clearTimeout(timer);  // Cleanup
}, []);
```

**Debug:**
```jsx
useEffect(() => {
  console.log('Effect EXECUTOU');
  console.log('Dependências:', { dep1, dep2 });

  return () => {
    console.log('Effect CLEANUP');
  };
}, [dep1, dep2]);
```

### 6. Hooks em Ordem Errada

**❌ ERRO:**
```jsx
const Component = ({ condition }) => {
  if (condition) {
    const [state, setState] = useState(null);  // ❌ Hook condicional
  }

  return <div>...</div>;
};
```

**✅ CORRETO:**
```jsx
const Component = ({ condition }) => {
  const [state, setState] = useState(null);  // ✅ Sempre no topo

  if (!condition) return null;

  return <div>...</div>;
};
```

---

## 🎨 DEBUGGING CSS

### 1. Estilos Não Aplicam

**Checklist:**
```jsx
// ✅ Importou o CSS Module?
import styles from './Component.module.css';

// ✅ Extensão .module.css?
Component.module.css  // ✅
Component.css         // ❌ Não é CSS Module

// ✅ Classe aplicada corretamente?
<div className={styles.container}>  // ✅
<div className="container">         // ❌ String literal não funciona com modules
```

**Debug:**
```jsx
import styles from './Component.module.css';

const Component = () => {
  console.log('CSS Module:', styles);
  // { container: "Component_container__a1b2c", title: "Component_title__d3e4f" }

  return (
    <div
      className={styles.container}
      {...console.log('ClassName aplicada:', styles.container)}
    >
      Content
    </div>
  );
};
```

### 2. Design Tokens Não Funcionam

**Problema:**
```css
/* Component.module.css */
.container {
  color: var(--color-cyber-primary);  /* Não funciona! */
}
```

**Solução:**
```css
/* ✅ CORRETO - Importar tokens */
@import '../../../styles/tokens/colors.css';
@import '../../../styles/tokens/spacing.css';

.container {
  color: var(--color-cyber-primary);  /* Agora funciona! */
}
```

### 3. Especificidade CSS

**Debug com DevTools:**
```
1. Inspecionar elemento (Ctrl+Shift+C)
2. Ver "Computed" tab
3. Ver quais estilos estão sendo aplicados
4. Ver quais estão sendo sobrescritos (riscados)
```

**Solução:**
```css
/* ❌ Baixa especificidade */
.button {
  color: red;
}

/* ✅ Alta especificidade */
.container .button {
  color: red;
}

/* ✅ !important (último recurso) */
.button {
  color: red !important;
}
```

### 4. Layout Quebrado

**Debug Box Model:**
```css
/* Adicione temporariamente */
* {
  outline: 1px solid red !important;
}

/* Ou em elemento específico */
.container * {
  outline: 1px solid lime !important;
}
```

**Ferramentas DevTools:**
```
1. Inspecionar elemento
2. Ver "Box Model" (margin, border, padding, content)
3. Ver "Layout" (Flexbox/Grid inspector)
```

---

## ⚡ DEBUGGING PERFORMANCE

### 1. Identificar Componentes Lentos

**React DevTools Profiler:**
```
1. Abra React DevTools
2. Aba "Profiler"
3. Clique "Record"
4. Interaja com a aplicação
5. Clique "Stop"
6. Analise flame chart
```

**Console Timing:**
```jsx
const Component = () => {
  console.time('Component Render');

  // Lógica do componente
  const data = expensiveCalculation();

  console.timeEnd('Component Render');

  return <div>{data}</div>;
};
```

### 2. Otimizar Re-renders

**React.memo:**
```jsx
// ❌ ANTES - Re-renderiza sempre que pai renderiza
const Child = ({ value }) => {
  console.log('Child rendered');
  return <div>{value}</div>;
};

// ✅ DEPOIS - Re-renderiza apenas se props mudarem
const Child = React.memo(({ value }) => {
  console.log('Child rendered');
  return <div>{value}</div>;
});
```

**useMemo:**
```jsx
// ❌ ANTES - Recalcula a cada render
const Component = ({ items }) => {
  const sorted = items.sort((a, b) => a - b);  // Caro!
  return <List items={sorted} />;
};

// ✅ DEPOIS - Recalcula apenas quando items mudar
const Component = ({ items }) => {
  const sorted = useMemo(() => {
    console.log('Sorting items...');
    return items.sort((a, b) => a - b);
  }, [items]);

  return <List items={sorted} />;
};
```

**useCallback:**
```jsx
// ❌ ANTES - Nova função a cada render
const Component = () => {
  const handleClick = () => console.log('clicked');
  return <Button onClick={handleClick} />;  // Button re-renderiza
};

// ✅ DEPOIS - Mesma função
const Component = () => {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <Button onClick={handleClick} />;  // Button não re-renderiza
};
```

### 3. Bundle Size

**Analisar Bundle:**
```bash
npm run build
npx vite-bundle-visualizer
```

**Code Splitting:**
```jsx
// ❌ ANTES - Tudo carregado de uma vez
import HeavyComponent from './HeavyComponent';

// ✅ DEPOIS - Lazy loading
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));

const App = () => (
  <Suspense fallback={<LoadingSpinner />}>
    <HeavyComponent />
  </Suspense>
);
```

---

## 🌐 DEBUGGING API

### 1. Requisições HTTP

**Axios Interceptor:**
```js
// api/config.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

// Request interceptor
api.interceptors.request.use(
  config => {
    console.log('📤 REQUEST:', {
      method: config.method,
      url: config.url,
      data: config.data
    });
    return config;
  },
  error => {
    console.error('❌ REQUEST ERROR:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  response => {
    console.log('📥 RESPONSE:', {
      status: response.status,
      data: response.data
    });
    return response;
  },
  error => {
    console.error('❌ RESPONSE ERROR:', {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message
    });
    return Promise.reject(error);
  }
);

export default api;
```

### 2. CORS Issues

**Sintoma:**
```
Access to fetch at 'http://localhost:8000/api' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Debug:**
```bash
# Verificar headers no Network tab
# Deve ter:
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

**Solução (Desenvolvimento):**
```js
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
}
```

### 3. Estado de Loading

**Pattern Completo:**
```jsx
const useApi = () => {
  const [state, setState] = useState({
    data: null,
    loading: false,
    error: null
  });

  const execute = async () => {
    console.log('🔄 API call started');
    setState({ data: null, loading: true, error: null });

    try {
      const response = await api.get('/endpoint');
      console.log('✅ API call success:', response.data);
      setState({ data: response.data, loading: false, error: null });
    } catch (error) {
      console.error('❌ API call failed:', error);
      setState({ data: null, loading: false, error: error.message });
    }
  };

  return { ...state, execute };
};
```

---

## 🐛 PROBLEMAS COMUNS

### 1. "Cannot read property of undefined"

**Causa:**
```jsx
const Component = ({ data }) => {
  return <div>{data.name}</div>;  // ❌ data pode ser null/undefined
};
```

**Solução:**
```jsx
const Component = ({ data }) => {
  // ✅ Optional chaining
  return <div>{data?.name}</div>;

  // ✅ Default value
  return <div>{data?.name || 'N/A'}</div>;

  // ✅ Early return
  if (!data) return null;
  return <div>{data.name}</div>;
};
```

### 2. "Maximum update depth exceeded"

**Causa:**
```jsx
// ❌ setState dentro do render
const Component = () => {
  const [count, setCount] = useState(0);
  setCount(count + 1);  // Loop infinito!
  return <div>{count}</div>;
};
```

**Solução:**
```jsx
// ✅ setState em event handler
const Component = () => {
  const [count, setCount] = useState(0);

  const increment = () => {
    setCount(count + 1);
  };

  return <button onClick={increment}>{count}</button>;
};

// ✅ setState em useEffect
const Component = () => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    setCount(1);
  }, []);  // Apenas no mount

  return <div>{count}</div>;
};
```

### 3. "Objects are not valid as React child"

**Causa:**
```jsx
const Component = ({ user }) => {
  return <div>{user}</div>;  // ❌ user é objeto
};
```

**Solução:**
```jsx
const Component = ({ user }) => {
  // ✅ Renderizar propriedades do objeto
  return <div>{user.name}</div>;

  // ✅ JSON.stringify para debug
  return <pre>{JSON.stringify(user, null, 2)}</pre>;
};
```

### 4. "Each child should have unique key prop"

**Causa:**
```jsx
// ❌ Sem key ou key duplicada
const List = ({ items }) => (
  <div>
    {items.map(item => <div>{item.name}</div>)}
  </div>
);
```

**Solução:**
```jsx
// ✅ Key única
const List = ({ items }) => (
  <div>
    {items.map(item => (
      <div key={item.id}>{item.name}</div>
    ))}
  </div>
);

// ⚠️ Usar index apenas se lista nunca mudar
const List = ({ items }) => (
  <div>
    {items.map((item, index) => (
      <div key={index}>{item.name}</div>
    ))}
  </div>
);
```

---

## 📊 LOGS E MONITORAMENTO

### Logging Estratégico

```jsx
// ❌ RUIM - Console.log genérico
console.log(data);

// ✅ BOM - Console estruturado
console.group('🔍 Component Debug');
console.log('Props:', props);
console.log('State:', state);
console.table(data);  // Dados tabulares
console.groupEnd();

// ✅ BOM - Console condicional
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', data);
}

// ✅ BOM - Console com estilo
console.log('%c✅ Success', 'color: green; font-weight: bold', data);
console.log('%c❌ Error', 'color: red; font-weight: bold', error);
console.log('%c🔄 Loading', 'color: blue; font-weight: bold');
```

### Debug Helper

```jsx
// utils/debug.js
export const debug = {
  log: (label, data) => {
    if (process.env.NODE_ENV === 'development') {
      console.group(`🔍 ${label}`);
      console.log(data);
      console.trace();  // Stack trace
      console.groupEnd();
    }
  },

  render: (componentName, props) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(
        `%c[RENDER] ${componentName}`,
        'background: #222; color: #bada55; padding: 2px 5px; border-radius: 2px',
        props
      );
    }
  },

  api: (method, url, data) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(
        `%c[API] ${method.toUpperCase()} ${url}`,
        'background: #3b82f6; color: white; padding: 2px 5px; border-radius: 2px',
        data
      );
    }
  }
};

// Uso
import { debug } from '../utils/debug';

const Component = (props) => {
  debug.render('Component', props);

  const handleClick = async () => {
    debug.api('post', '/api/endpoint', { data });
    await api.post('/endpoint', data);
  };

  return <div>...</div>;
};
```

### Error Boundary

```jsx
// components/ErrorBoundary.jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('❌ Error Boundary caught:', {
      error,
      errorInfo,
      componentStack: errorInfo.componentStack
    });

    // Enviar para serviço de logging
    // logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: 'red' }}>
          <h2>Algo deu errado.</h2>
          <details>
            <summary>Detalhes do erro</summary>
            <pre>{this.state.error.toString()}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

// Uso
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

---

## 🎯 CHECKLIST DE DEBUGGING

Quando encontrar um bug:

1. **Reproduzir**
   - [ ] Consigo reproduzir consistentemente?
   - [ ] Em qual navegador/ambiente?
   - [ ] Quais passos levam ao bug?

2. **Isolar**
   - [ ] Qual componente está com problema?
   - [ ] Qual linha de código?
   - [ ] É problema de estado, props, ou rendering?

3. **Debug**
   - [ ] Adicionei console.logs estratégicos?
   - [ ] Verifiquei React DevTools?
   - [ ] Verifiquei Network tab?
   - [ ] Verifiquei Console errors/warnings?

4. **Corrigir**
   - [ ] Entendi a causa raiz?
   - [ ] Corrigi o problema?
   - [ ] Testei a correção?
   - [ ] Preveni regressão?

5. **Documentar**
   - [ ] Documentei a solução?
   - [ ] Atualizei testes?
   - [ ] Adicionei validação?

---

**Última atualização:** 2025-09-30
**Versão:** 1.0
