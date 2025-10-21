
# 📄 `vertice/connectors/base.py`

## 📋 Descrição

Este módulo define a `BaseConnector`, uma classe base abstrata que serve como o fundamento para todos os outros conectores de serviço na CLI. O seu propósito é padronizar a comunicação com os microserviços do backend, fornecendo métodos assíncronos para requisições HTTP e um contrato para a verificação de saúde dos serviços.

## 🏗️ Classes

### `BaseConnector(ABC)`

Uma classe abstrata que encapsula um cliente HTTP assíncrono (`httpx.AsyncClient`) e fornece métodos auxiliares para requisições GET e POST, além de um método para fechar a conexão.

**Atributos:**
- `service_name (str)`: O nome do serviço (usado para mensagens de erro).
- `base_url (str)`: A URL base do microserviço.
- `client (httpx.AsyncClient)`: A instância do cliente HTTP assíncrono.

**Métodos Públicos:**

#### `__init__(self, service_name, base_url, timeout)`
Inicializa o conector.
- **Parâmetros:**
  - `service_name (str)`: Nome do serviço.
  - `base_url (str)`: URL base do serviço.
  - `timeout (int)`: Timeout para as requisições (padrão: 10s).

#### `health_check(self) -> bool`
Um método abstrato que **deve** ser implementado pelas subclasses. Sua função é verificar se o serviço está online e operacional.
- **Retorna:** `True` se o serviço estiver saudável, `False` caso contrário.

#### `close(self)`
Fecha a sessão do cliente HTTP assíncrono. Essencial para liberar os recursos de rede de forma limpa.

**Métodos Protegidos:**

#### `_get(self, endpoint, **kwargs)`
Realiza uma requisição GET assíncrona para um endpoint do serviço.
- **Parâmetros:**
  - `endpoint (str)`: O caminho do endpoint (ex: `/api/status`).
- **Retorna:** Um dicionário com a resposta JSON da API, ou `None` se ocorrer um erro.

#### `_post(self, endpoint, data, **kwargs)`
Realiza uma requisição POST assíncrona para um endpoint do serviço.
- **Parâmetros:**
  - `endpoint (str)`: O caminho do endpoint.
  - `data (dict)`: O payload JSON a ser enviado no corpo da requisição.
- **Retorna:** Um dicionário com a resposta JSON da API, ou `None` se ocorrer um erro.

## 💡 Exemplo de Uso (em uma subclasse)

```python
from .base import BaseConnector

class MyConnector(BaseConnector):
    def __init__(self):
        # Chama o __init__ da classe base com os detalhes do serviço
        super().__init__(service_name="My Service", base_url="http://localhost:8001")

    async def health_check(self) -> bool:
        try:
            # Implementação específica para verificar a saúde do serviço
            response = await self._get("/health")
            return response.get("status") == "ok"
        except Exception:
            return False

    async def get_data(self, item_id: str):
        return await self._get(f"/items/{item_id}")
```

## 🧪 Guia de Testes

- Testar se o `_get` e o `_post` constroem a URL corretamente.
- Mockar o `httpx.AsyncClient` para simular respostas de sucesso (2xx) e de erro (4xx, 5xx) e verificar se os métodos retornam os dados esperados ou `None`.
- Testar o tratamento de exceções de rede (ex: `httpx.RequestError`).
- Verificar se o método `close` é chamado para evitar vazamento de recursos.

## ❗ Pontos de Atenção e Melhoria

- **Vulnerabilidade de Comunicação Insegura (Alta):** A classe não impõe o uso de HTTPS. Como as URLs base nos conectores filhos usam `http://`, toda a comunicação é feita em texto plano, expondo dados sensíveis a ataques de Man-in-the-Middle. A classe deveria, no mínimo, alertar sobre URLs não-HTTPS ou ter uma política mais estrita.
- **Vulnerabilidade de SSRF (Média):** A forma como a URL é construída (`f"{self.base_url}{endpoint}"`) pode ser vulnerável a SSRF se o `endpoint` puder ser manipulado por um usuário para incluir caracteres como `..` ou `@`.
- **Tratamento de Erros:** O tratamento de erros atual simplesmente imprime a exceção no console (`print`). Isso não é ideal para uma aplicação de CLI, que deveria usar um sistema de logging mais robusto (ex: `logging` do Python) e fornecer mensagens de erro mais claras para o usuário final através do `stderr`.
- **Duplicação de Código:** A lógica de tratamento de erros é idêntica nos métodos `_get` e `_post`. Ela poderia ser abstraída para um método auxiliar ou um decorator para reduzir a duplicação.
