# MAV Detection Widget

## 🛡️🇧🇷 Detecção de Manipulação e Amplificação Viralizada

Widget essencial para defesa democrática brasileira contra fake news e ataques coordenados em redes sociais.

## Características

### Análises Realizadas

1. **Coordenação Temporal** ⏰
   - Detecção de posts publicados em intervalos suspeitos
   - Análise de sincronização entre múltiplas contas
   - Identificação de padrões temporais de bot farms

2. **Similaridade de Conteúdo** 📝
   - Análise semântica usando embeddings
   - Detecção de copy-paste e templates
   - Identificação de narrativas coordenadas

3. **Coordenação de Rede** 🕸️
   - Análise de grafos sociais (GNN)
   - Detecção de contas conectadas suspeitas
   - Identificação de astroturfing

### Tipos de Campanha Detectados

- **🎯 Assassinato de Reputação**: Ataques coordenados contra indivíduos
- **📢 Assédio em Massa**: Campanhas de assédio coletivo
- **🚨 Desinformação**: Propagação coordenada de fake news
- **🤖 Astroturfing**: Simulação artificial de movimentos orgânicos

### Níveis de Severidade

- **CRITICAL** 🔴 - Ameaça crítica (dc2626)
- **HIGH** 🟠 - Alta ameaça (ea580c)
- **MEDIUM** 🟡 - Ameaça média (f59e0b)
- **LOW** 🟢 - Baixa ameaça (10b981)

## Uso

### Importação

```javascript
import { MAVDetection } from '@/components/cyber/MAVDetection';

// Em seu componente
<MAVDetection />
```

### Formato dos Dados

#### Posts (JSON Array)

```json
[
  {
    "id": "1",
    "text": "Conteúdo do post",
    "author": "user1",
    "timestamp": "2024-01-01T00:00:00Z",
    "engagement": {
      "likes": 100,
      "shares": 50
    }
  }
]
```

**Campos obrigatórios:**
- `id`: Identificador único do post
- `text`: Conteúdo textual
- `author`: ID do autor
- `timestamp`: Data/hora no formato ISO 8601
- `engagement`: Objeto com `likes` e `shares`

#### Accounts (JSON Array - Opcional)

```json
[
  {
    "id": "user1",
    "created_at": "2023-01-01T00:00:00Z",
    "followers_count": 100,
    "following_count": 500,
    "posts_count": 50
  }
]
```

**Campos obrigatórios:**
- `id`: Identificador único da conta
- `created_at`: Data de criação no formato ISO 8601
- `followers_count`: Número de seguidores
- `following_count`: Número de seguindo
- `posts_count`: Total de posts

### Plataformas Suportadas

- 🐦 **Twitter** (X)
- 📘 **Facebook**
- 📷 **Instagram**

### Janelas de Tempo

- 1 hora
- 6 horas
- 24 horas
- 7 dias
- 30 dias

## API Backend

### Endpoints Utilizados

1. **POST** `/api/social-defense/mav/detect`
   - Detecta campanhas MAV
   - Retorna análise completa com sinais de coordenação

2. **GET** `/api/social-defense/mav/metrics`
   - Retorna métricas do sistema
   - Atualizado a cada 30 segundos

3. **GET** `/api/social-defense/mav/campaigns`
   - Lista campanhas detectadas
   - Filtros: severity, platform, limit

### Exemplo de Response

```json
{
  "success": true,
  "data": {
    "is_mav_campaign": true,
    "campaign_type": "disinformation",
    "severity": "HIGH",
    "confidence_score": 0.87,
    "platform": "twitter",
    "posts_analyzed": 50,
    "coordination_signals": {
      "temporal": 0.92,
      "content": 0.85,
      "network": 0.78
    },
    "suspicious_accounts": [
      {
        "account_id": "user1",
        "suspicion_score": 0.89
      }
    ],
    "recommendations": [
      {
        "action": "Reportar contas suspeitas às autoridades"
      },
      {
        "action": "Monitorar propagação da narrativa"
      }
    ],
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Validações

### Client-Side

- Validação de JSON syntax
- Verificação de arrays vazios
- Validação de campos obrigatórios
- Sanitização de inputs

### Error Handling

- Mensagens de erro claras em português
- Feedback visual de erros
- Logging de erros no console
- Graceful degradation

## Internacionalização (i18n)

### Chaves de Tradução

```javascript
t('defensive.mav.title', 'MAV Detection')
t('defensive.mav.subtitle', 'Detecção de Manipulação...')
```

## Estilos

### Padrão Pagani

- Gradient background: `#1a1a2e` → `#16213e`
- Primary color: `#00ff88`
- Border glow: `rgba(0, 255, 136, 0.2)`
- Monospace font: `'Courier New', monospace`

### Cores de Severidade

```css
CRITICAL: #dc2626
HIGH:     #ea580c
MEDIUM:   #f59e0b
LOW:      #10b981
```

### Responsivo

- Mobile-first design
- Grid adaptativo
- Breakpoint: 768px

## Performance

- Métricas carregadas a cada 30s
- Debounce em inputs (opcional)
- Lazy loading de listas longas
- AbortController para cancelamento

## Segurança

- Sanitização de JSON inputs
- Validação de tipos
- Error boundaries
- No eval() ou innerHTML

## Testing

### Manual Testing

1. Clicar em "Carregar Exemplo" para dados de teste
2. Selecionar plataforma e janela de tempo
3. Submeter análise
4. Verificar resultado e métricas

### Scenarios

- ✅ Detecção de campanha coordenada
- ✅ Sem coordenação detectada
- ✅ JSON inválido
- ✅ Array vazio
- ✅ Erro de backend
- ✅ Timeout de requisição

## Integrações

### Services

- `OffensiveService.js` - Serviço principal
- Métodos: `detectMAVCampaign()`, `getMAVMetrics()`

### Backend Services

- **MAV Detection Service** (Port 8039)
- Python/FastAPI
- ML Models: BERT, GNN, Statistical Analysis

## Roadmap

### Fase 1 - ✅ Completo
- [x] Componente base
- [x] Formulário de análise
- [x] Display de resultados
- [x] Métricas em tempo real

### Fase 2 - Planejado
- [ ] Visualização de grafos de rede
- [ ] Timeline de propagação
- [ ] Exportação de relatórios (PDF)
- [ ] Integração com TSE/PF

### Fase 3 - Futuro
- [ ] Real-time monitoring
- [ ] Alertas automáticos
- [ ] Dashboard executivo
- [ ] API pública

## Contribuindo

### Code Style

- ESLint + Prettier
- Comentários em português
- JSDoc para funções públicas
- Semantic commits

### Testing

```bash
npm test -- MAVDetection
npm run test:coverage
```

## Licença

Vértice Platform - Proprietary
© 2024 Vértice Team

---

## 🚨 IMPORTANTE

Este widget é **CRÍTICO** para defesa democrática brasileira. Qualquer modificação deve ser:

1. Revisada por security team
2. Testada extensivamente
3. Aprovada por compliance
4. Documentada completamente

**Contato de Emergência**: security@vertice.com.br
