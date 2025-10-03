
# 📄 `vertice/connectors/ip_intel.py`

## 📋 Descrição

Este módulo define o `IPIntelConnector`, a classe responsável por se comunicar com o microserviço de **IP Intelligence**. Ele herda da `BaseConnector` e implementa os métodos específicos para obter informações sobre endereços de IP.

Uma característica notável deste conector é que ele tenta obter a URL do serviço a partir do sistema de configuração (`config.get`), o que é uma prática melhor do que ter a URL hardcoded. No entanto, ele ainda possui uma URL de fallback hardcoded.

## 🏗️ Classes

### `IPIntelConnector(BaseConnector)`

Implementação concreta da `BaseConnector` para o serviço de IP Intelligence.

**Métodos Públicos:**

#### `__init__(self)`
Inicializa o conector. Ele busca a URL do serviço no arquivo de configuração em `services.ip_intelligence.url`. Se não encontrar, usa `http://localhost:8004` como padrão.

#### `health_check(self) -> bool`
Verifica a saúde do serviço de IP Intelligence fazendo uma requisição GET para o endpoint `/`. Espera que a resposta JSON contenha `{"status": "operational"}`.
- **Retorna:** `True` se o serviço estiver saudável, `False` caso contrário.

#### `analyze_ip(self, ip: str) -> Dict[str, Any]`
Envia um endereço de IP para o serviço para uma análise completa (geolocalização, reputação, etc.).
- **Parâmetros:**
  - `ip (str)`: O endereço de IP a ser analisado.
- **Retorna:** Um dicionário contendo os resultados da análise.

#### `get_my_ip(self) -> str`
Solicita ao serviço que detecte e retorne o endereço de IP público do cliente.
- **Retorna:** Uma string contendo o IP público detectado.

#### `analyze_my_ip(self) -> Dict[str, Any]`
Um método de conveniência que solicita ao serviço que detecte e analise o IP público do cliente em uma única chamada.
- **Retorna:** Um dicionário contendo os resultados da análise do IP público.

## 💡 Exemplo de Uso

```python
import asyncio
from .ip_intel import IPIntelConnector

async def main():
    connector = IPIntelConnector()

    if await connector.health_check():
        # Analisa um IP específico
        analysis = await connector.analyze_ip("8.8.8.8")
        print(analysis)

        # Detecta o IP público
        my_ip = await connector.get_my_ip()
        print(f"My public IP is: {my_ip}")

    await connector.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Guia de Testes

- Mockar o `config.get` para testar tanto o caso em que a URL é encontrada quanto o caso do fallback.
- Mockar os métodos `_get` e `_post` da `BaseConnector` para simular as respostas da API para cada método (`health_check`, `analyze_ip`, etc.) e verificar se os dados corretos são retornados.
- Testar o tratamento de erro quando a API retorna um status de erro ou quando há uma falha de rede.

## ❗ Pontos de Atenção e Melhoria

- **Comunicação Insegura (Alta):** A URL de fallback (e provavelmente a URL no arquivo de configuração) usa `http`, o que significa que a comunicação não é criptografada. A aplicação deveria priorizar ou exigir HTTPS.
- **Duplicação de Código:** A lógica de tratamento de erros no `health_check` é repetida de outros conectores e poderia ser abstraída na `BaseConnector`.
- **Número Mágico:** A porta `8004` na URL de fallback é um "número mágico" e deveria ser definida como uma constante nomeada em um local central, se necessário.
