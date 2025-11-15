# MAV Detection - Guia de Integração Rápida

## 🚀 Quick Start

### 1. Importação Básica

```jsx
import { MAVDetection } from "@/components/cyber/MAVDetection";

function App() {
  return <MAVDetection />;
}
```

### 2. Integração no Offensive Dashboard

Adicione ao arquivo do dashboard (ex: `OffensiveDashboard.jsx`):

```jsx
import { MAVDetection } from "@/components/cyber/MAVDetection";

export const OffensiveDashboard = () => {
  return (
    <div className="dashboard">
      {/* Outros widgets */}

      <div className="widget-container">
        <MAVDetection />
      </div>
    </div>
  );
};
```

### 3. Verificação de Dependências

O componente requer:

```json
{
  "react": "^18.0.0",
  "react-i18next": "^13.0.0",
  "@/services/offensive/OffensiveService": "internal"
}
```

### 4. Verificação do Backend

Certifique-se de que o serviço MAV Detection está rodando:

```bash
# Verificar porta 8039
curl http://localhost:8039/health

# Verificar métricas
curl http://localhost:8039/api/social-defense/mav/metrics
```

## 🔧 Configuração do Endpoint

Se necessário, ajuste o endpoint no arquivo `ServiceEndpoints`:

```javascript
// frontend/src/config/endpoints.js
export const ServiceEndpoints = {
  offensive: {
    // ... outros endpoints
    mav: "/api/social-defense/mav", // Port 8039
  },
};
```

## 🧪 Teste Manual Rápido

1. Acesse o componente no frontend
2. Clique em "Carregar Exemplo"
3. Selecione plataforma: Twitter
4. Selecione janela: 24 horas
5. Clique em "Detectar Campanha MAV"
6. Verifique o resultado

## 📊 Formato de Dados Esperado

### Posts (Mínimo):

```json
[
  {
    "id": "1",
    "text": "Conteúdo do post",
    "author": "user_id",
    "timestamp": "2024-01-01T00:00:00Z",
    "engagement": {
      "likes": 100,
      "shares": 50
    }
  }
]
```

### Accounts (Opcional):

```json
[
  {
    "id": "user_id",
    "created_at": "2023-01-01T00:00:00Z",
    "followers_count": 100,
    "following_count": 500,
    "posts_count": 50
  }
]
```

## 🎨 Customização de Estilos

O componente usa CSS Modules. Para customizar:

1. Copie `MAVDetection.module.css`
2. Ajuste as variáveis de cor
3. Reimporte no componente

Cores principais:

- Primary: `#00ff88`
- Background gradient: `#1a1a2e → #16213e`
- Severidade CRITICAL: `#dc2626`
- Severidade HIGH: `#ea580c`
- Severidade MEDIUM: `#f59e0b`
- Severidade LOW: `#10b981`

## 🌐 Internacionalização

Adicione as chaves ao arquivo de tradução:

```json
{
  "defensive": {
    "mav": {
      "title": "MAV Detection",
      "subtitle": "Detecção de Manipulação e Amplificação Viralizada em redes sociais brasileiras"
    }
  }
}
```

## 🐛 Troubleshooting

### Problema: "getOffensiveService is not a function"

**Solução**: Verifique se o path alias `@/services` está configurado

```javascript
// vite.config.js ou tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Problema: "Failed to load metrics"

**Solução**: Verifique se o backend está rodando na porta 8039

```bash
docker ps | grep mav_detection
# ou
curl http://localhost:8039/health
```

### Problema: JSON parse error

**Solução**: Use o botão "Carregar Exemplo" para ver o formato correto

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs do console do navegador
2. Verifique os logs do backend (port 8039)
3. Consulte o README.md completo
4. Contate: security@vertice.com.br

---

**Status**: ✅ PRONTO PARA PRODUÇÃO
**Versão**: 1.0.0
**Última atualização**: 2024-10-27
