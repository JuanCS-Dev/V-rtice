
# 📄 `vertice/connectors/adr_core.py`

## 📋 Descrição

Este módulo define o `ADRCoreConnector`, a classe responsável por se comunicar com o microserviço **ADR Core Service**. Este serviço parece ser o núcleo do sistema de Detecção e Resposta a Ameaças (Ameaça Digital em Redes). O conector herda da `BaseConnector` e implementa os métodos para interagir com a API do serviço de ADR.

Ao contrário do `IPIntelConnector`, este conector volta ao padrão de ter a URL do serviço completamente hardcoded.

## 🏗️ Classes

### `ADRCoreConnector(BaseConnector)`

Implementação concreta da `BaseConnector` para o serviço de ADR.

**Métodos Públicos:**

#### `__init__(self)`
Inicializa o conector. A URL do serviço é hardcoded para `http://localhost:8014`.

#### `health_check(self) -> bool`
Verifica a saúde do serviço de ADR fazendo uma requisição GET para o endpoint `/`. Espera que a resposta JSON contenha `{"status": "operational"}`.
- **Retorna:** `True` se o serviço estiver saudável, `False` caso contrário.

#### `get_status(self) -> Dict[str, Any]`
Busca e retorna o status detalhado do sistema ADR.
- **Retorna:** Um dicionário contendo os dados de status do sistema.

## 💡 Exemplo de Uso

```python
import asyncio
from .adr_core import ADRCoreConnector

async def main():
    connector = ADRCoreConnector()

    if await connector.health_check():
        # Obtém o status do sistema ADR
        status = await connector.get_status()
        print(status)

    await connector.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Guia de Testes

- Mockar os métodos `_get` e `_post` da `BaseConnector` para simular as respostas da API para `health_check` e `get_status`.
- Testar o tratamento de erro quando a API retorna um status de erro ou quando há uma falha de rede.
- Validar que o construtor está chamando `super().__init__` com a URL correta.

## ❗ Pontos de Atenção e Melhoria

- **Comunicação Insegura (Alta):** A URL hardcoded usa `http`, expondo toda a comunicação a riscos de interceptação.
- **URL Hardcoded (Média):** A URL do serviço está fixa no código. Isso dificulta a configuração do ambiente e a implantação em produção. A abordagem usada no `IPIntelConnector` (usando `config.get`) é superior e deveria ser aplicada aqui.
- **Duplicação de Código:** A lógica de tratamento de erros no `health_check` é idêntica à de outros conectores e deveria ser centralizada.
- **Número Mágico:** A porta `8014` é um "número mágico".
