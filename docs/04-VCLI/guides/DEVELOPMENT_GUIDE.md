
# 🛠️ Guia de Desenvolvimento do Vértice CLI

Este guia é destinado a desenvolvedores que desejam entender a arquitetura do Vértice CLI e como adicionar novas funcionalidades.

## 1. Visão Geral da Arquitetura

A CLI é construída sobre três pilares principais:

1.  **Camada de Comandos (`vertice/commands/`):**
    - Define a interface do usuário da CLI usando `typer`.
    - Cada arquivo neste diretório corresponde a um subcomando (ex: `vcli ip ...`, `vcli scan ...`).
    - A principal responsabilidade desta camada é: receber input do usuário, chamar a camada de serviço/conector apropriada e usar o módulo `utils/output.py` para formatar a saída.

2.  **Camada de Conectores (`vertice/connectors/`):**
    - Abstrai a comunicação com os microserviços de backend.
    - Cada conector herda de `BaseConnector` e é responsável por interagir com um serviço específico (ex: `IPIntelConnector` fala com o serviço de IP Intelligence).
    - Eles usam `httpx` para fazer requisições assíncronas.

3.  **Camada de Utilitários (`vertice/utils/`):**
    - Fornece funcionalidades compartilhadas por toda a aplicação, como:
        - `auth.py`: Gerenciamento de autenticação e permissões.
        - `config.py`: Carregamento de configurações.
        - `output.py`: Funções para exibir dados na UI.
        - `cache.py`: (Atualmente um placeholder) para caching de respostas.

## 2. Como Adicionar um Novo Comando

Vamos supor que você queira adicionar um novo comando `vcli domain resolve <DOMAIN_NAME>`.

**Passo 1: Crie o Conector (se necessário)**

Se o novo comando precisa de um serviço de backend que ainda não tem um conector, crie-o primeiro em `vertice/connectors/`.

```python
# vertice/connectors/domain_connector.py
from .base import BaseConnector

class DomainConnector(BaseConnector):
    def __init__(self):
        # Supondo que o serviço rode na porta 8020
        super().__init__(service_name="Domain Service", base_url="http://localhost:8020")

    async def health_check(self) -> bool: ...

    async def resolve_domain(self, domain: str):
        return await self._get(f"/api/domain/resolve/{domain}")
```

**Passo 2: Crie o Módulo do Comando**

Crie um novo arquivo `vertice/commands/domain.py`.

```python
# vertice/commands/domain.py
import typer
import asyncio
from typing_extensions import Annotated
from ..connectors.domain_connector import DomainConnector
from ..utils.output import print_json, spinner_task, print_error
from ..utils.auth import require_auth

# Crie o app Typer para o novo grupo de comandos
app = typer.Typer(
    name="domain",
    help="Operações relacionadas a domínios."
)

@app.command()
def resolve(
    domain_name: Annotated[str, typer.Argument(help="Nome do domínio a ser resolvido")],
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """Resolve um nome de domínio para um endereço de IP."""
    require_auth()

    async def _resolve():
        connector = DomainConnector()
        try:
            with spinner_task(f"Resolvendo {domain_name}..."):
                result = await connector.resolve_domain(domain_name)
            
            if json_output:
                print_json(result)
            else:
                # Formate a saída como desejar
                ip = result.get("ip_address", "Não resolvido")
                print(f"O domínio {domain_name} resolve para: {ip}")

        except Exception as e:
            print_error(f"Erro ao resolver o domínio: {e}")
        finally:
            await connector.close()

    asyncio.run(_resolve())
```

**Passo 3: Registre o Novo Módulo**

Abra o arquivo `vertice/cli.py` e adicione o nome do seu novo módulo à lista `COMMAND_MODULES`.

```python
# vertice/cli.py

# ...
COMMAND_MODULES = ["auth", "ip", "threat", "adr", "malware", "scan", "monitor", "hunt", "menu", "domain"] # Adicione aqui
# ...
```

**Passo 4: Teste**

Execute `vcli domain resolve google.com` para testar seu novo comando.

## 3. Como Testar Localmente

- **Testes Unitários:** Use `pytest` para executar os testes na pasta `tests/`. Os testes unitários devem mockar todas as dependências externas, especialmente os conectores.
- **Execução Manual:** Como o pacote é instalado em modo editável (`pip install -e .`), você pode simplesmente executar os comandos `vcli` no seu terminal para testar as mudanças em tempo real.

## 4. Dicas de Debugging

- **Verbose Mode:** Muitos comandos têm uma flag `-v` ou `--verbose`. Use-a para obter mais detalhes sobre o que está acontecendo nos bastidores.
- **JSON Output:** Use a flag `--json` para ver a resposta bruta da API. Isso é útil para entender os dados com os quais você está trabalhando antes de criar uma formatação de tabela bonita.
- **Print-Driven Development:** Não hesite em usar `print()` ou `console.log()` temporariamente no código para inspecionar variáveis durante o desenvolvimento. Apenas lembre-se de removê-los antes de commitar.
- **Erros de Conexão:** Se você receber erros de conexão, verifique se os serviços de backend (que rodam via `docker-compose`) estão online e acessíveis nas portas esperadas.
