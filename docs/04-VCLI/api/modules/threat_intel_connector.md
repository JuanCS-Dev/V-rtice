
# 📄 `vertice/connectors/threat_intel.py`

## 📋 Descrição

Este módulo define o `ThreatIntelConnector`, a classe de comunicação com o microserviço de **Threat Intelligence**. Ele herda da `BaseConnector` e fornece os métodos para consultar indicadores de ameaça (IPs, domínios, hashes, etc.).

## 🏗️ Classes

### `ThreatIntelConnector(BaseConnector)`

Implementação concreta da `BaseConnector` para o serviço de Threat Intelligence.

**Métodos Públicos:**

#### `__init__(self)`
Inicializa o conector. A URL do serviço é hardcoded para `http://localhost:8013`.

#### `health_check(self) -> bool`
Verifica a saúde do serviço de Threat Intelligence. Espera que o endpoint `/` retorne um JSON com `{"status": "operational"}`.
- **Retorna:** `True` se o serviço estiver saudável, `False` caso contrário.

#### `lookup_threat(self, indicator: str) -> Dict[str, Any]`
Envia um indicador de ameaça para o serviço para obter informações detalhadas sobre ele.
- **Parâmetros:**
  - `indicator (str)`: O indicador a ser consultado (ex: "evil.com", "1.2.3.4", "...hash...").
- **Retorna:** Um dicionário contendo as informações de ameaça encontradas.

## 💡 Exemplo de Uso

```python
import asyncio
from .threat_intel import ThreatIntelConnector

async def main():
    connector = ThreatIntelConnector()

    if await connector.health_check():
        # Consulta um domínio
        threat_info = await connector.lookup_threat("google.com")
        print(threat_info)

    await connector.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Guia de Testes

- Mockar o método `_post` e verificar se `lookup_threat` o chama com o JSON contendo `{"indicator": ...}`.
- Testar o `health_check` para respostas de sucesso e erro.
- Testar o tratamento de erro quando a API retorna um status de erro ou quando há uma falha de rede.

## ❗ Pontos de Atenção e Melhoria

- **Comunicação Insegura (Alta):** A URL usa `http`, o que é inseguro.
- **URL Hardcoded (Média):** A URL do serviço está fixa no código.
- **Duplicação de Código:** A lógica de tratamento de erros no `health_check` é repetida.
- **Número Mágico:** A porta `8013` está hardcoded.
- **Falta de Validação:** O indicador não é validado no lado do cliente antes de ser enviado. A implementação poderia, no mínimo, verificar se a string não está vazia.
