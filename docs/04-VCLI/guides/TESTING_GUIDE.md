
# 🧪 Guia de Testes do Vértice CLI

Testes são um componente crítico do Vértice CLI para garantir a estabilidade, a confiabilidade e a segurança da aplicação. Usamos o framework `pytest` para escrever e executar testes.

## 1. Estratégia de Testes

Nossa estratégia é baseada em dois níveis principais de testes:

1.  **Testes Unitários:**
    - **Foco:** Testar uma única unidade de código (uma função ou uma classe) de forma isolada.
    - **Características:** São rápidos, não dependem de serviços externos (banco de dados, APIs) e constituem a maior parte da nossa suíte de testes.
    - **Localização:** `tests/unit/`

2.  **Testes de Integração:**
    - **Foco:** Testar a interação entre diferentes componentes do sistema (ex: um comando da CLI e seu conector, ou o conector e um serviço de backend mockado).
    - **Características:** São mais lentos que os testes unitários e podem depender de serviços externos (geralmente mockados).
    - **Localização:** `tests/integration/`

## 2. Como Escrever Testes Unitários

A principal ferramenta para testes unitários é o **mocking**, que nos permite simular o comportamento de dependências externas.

### Exemplo: Testando um Comando Simples

Vamos supor que queremos testar o comando `vcli ip my-ip`.

```python
# tests/unit/test_ip_commands.py

from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

# Importe o "app" Typer do módulo que você quer testar
from vertice.commands.ip import app as ip_app

# Crie um runner para invocar os comandos da CLI em um ambiente de teste
runner = CliRunner()

# Use o decorator @patch para substituir o IPIntelConnector por um Mock
@patch('vertice.commands.ip.IPIntelConnector')
def test_my_ip_success(MockIPIntelConnector):
    # Arrange: Configure o comportamento do seu mock
    mock_instance = MockIPIntelConnector.return_value
    mock_instance.get_my_ip.return_value = "123.45.67.89"

    # Act: Execute o comando da CLI
    result = runner.invoke(ip_app, ["my-ip"])

    # Assert: Verifique se o resultado foi o esperado
    assert result.exit_code == 0
    assert "Your IP: 123.45.67.89" in result.stdout
    
    # Verifique se o método mockado foi chamado
    mock_instance.get_my_ip.assert_called_once()

@patch('vertice.commands.ip.IPIntelConnector')
def test_my_ip_json_output(MockIPIntelConnector):
    # Arrange
    mock_instance = MockIPIntelConnector.return_value
    mock_instance.get_my_ip.return_value = "123.45.67.89"

    # Act
    result = runner.invoke(ip_app, ["my-ip", "--json"])

    # Assert
    assert result.exit_code == 0
    assert '"ip": "123.45.67.89"' in result.stdout
```

### Diretrizes para Mocking

- **Seja Específico:** Faça o patch no local onde o objeto é **usado**, não onde ele é definido. (ex: `vertice.commands.ip.IPIntelConnector`, não `vertice.connectors.ip_intel.IPIntelConnector`).
- **Use `MagicMock`:** Para mocks mais complexos que precisam simular métodos assíncronos ou outros "métodos mágicos".
- **Teste o Contrato:** Seus testes devem verificar se os seus mocks foram chamados com os argumentos corretos. Isso garante que a integração entre as suas unidades de código está correta.

## 3. Como Escrever Testes de Integração

Os testes de integração são similares, mas mockam em um nível mais baixo (ex: a camada HTTP em vez do conector).

- **Mock de API:** Use bibliotecas como `pytest-httpx` para interceptar as chamadas de rede feitas pelo `httpx` e retornar respostas JSON predefinidas. Isso permite testar toda a lógica do conector e do comando sem depender de um serviço de backend real.
- **Testes End-to-End (E2E):** Para um nível ainda mais alto, podemos ter testes que executam contra um ambiente Docker real, provisionado via `docker-compose`. Esses testes são os mais lentos e frágeis, e devem ser usados com moderação para os fluxos mais críticos.

## 4. Executando os Testes

Para executar toda a suíte de testes, use o `pytest` na raiz do projeto:

```bash
pytest
```

### Cobertura de Testes

Para gerar um relatório de cobertura de testes, use o `pytest-cov`:

```bash
pytest --cov=vertice --cov-report=html
```

Isso gerará um relatório em `htmlcov/index.html` que você pode abrir no navegador para ver quais linhas de código não foram cobertas pelos testes.

**Nosso objetivo é manter a cobertura de testes acima de 80%.**
