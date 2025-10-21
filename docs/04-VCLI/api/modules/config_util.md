
# 📄 `vertice/utils/config.py`

## 📋 Descrição

Este módulo fornece a classe `Config`, um gerenciador de configuração para a CLI. Ele é responsável por carregar uma configuração padrão (distribuída com a aplicação) e sobrepô-la com uma configuração personalizada do usuário, localizada em `~/.vertice/config.yaml`.

O sistema usa uma abordagem de "deep merge" para que o usuário precise especificar apenas as chaves que deseja alterar, herdando o resto do padrão.

## 🏗️ Classes

### `Config`

Gerencia o carregamento e o acesso às configurações da aplicação.

**Atributos:**
- `config_dir (Path)`: O diretório `~/.vertice`.
- `config_file (Path)`: O caminho para o arquivo de configuração do usuário (`~/.vertice/config.yaml`).
- `default_config_path (Path)`: O caminho para o arquivo de configuração padrão, localizado dentro do pacote Python.
- `config (dict)`: O dicionário final, contendo a fusão das configurações padrão e do usuário.

**Métodos Públicos:**

#### `__init__(self)`
Inicializa o gerenciador, define os caminhos e chama `_load()` para carregar a configuração na memória.

#### `get(self, key: str, default: Any = None) -> Any`
Recupera um valor da configuração usando uma notação de ponto para acessar chaves aninhadas.
- **Parâmetros:**
  - `key (str)`: A chave a ser recuperada (ex: `services.ip_intelligence.url`).
  - `default (Any)`: O valor a ser retornado se a chave não for encontrada.
- **Retorna:** O valor da configuração ou o valor padrão.

**Métodos Protegidos:**

#### `_load(self) -> Dict[str, Any]`
Orquestra o processo de carregamento. Primeiro, carrega o arquivo YAML padrão. Em seguida, se o arquivo do usuário existir, ele o carrega e chama `_deep_merge` para fundir as duas configurações.

#### `_deep_merge(self, default_dict: Dict, user_dict: Dict)`
Realiza uma fusão recursiva de dois dicionários. Os valores do `user_dict` têm precedência sobre os do `default_dict`.

## 🌎 Variáveis Globais

- `config (Config)`: Uma instância global da classe `Config`, permitindo acesso fácil à configuração de qualquer lugar da aplicação (ex: `from ..utils.config import config`).

## 💡 Exemplo de Uso

**Acessando uma configuração:**
```python
from .config import config

# Recupera a URL do serviço de IP, com um fallback caso não exista
api_url = config.get("services.ip_intelligence.url", "http://localhost:8004")

# Recupera o nível de log
log_level = config.get("logging.level", "INFO")
```

**Exemplo de `config.yaml` do usuário:**
```yaml
# ~/.vertice/config.yaml

# Altera apenas a URL de um serviço, o resto é herdado do padrão
services:
  ip_intelligence:
    url: https://my-custom-ip-intel-service.com
```

## 🧪 Guia de Testes

- Testar se `_load` carrega corretamente o arquivo padrão.
- Testar se `_load` lida corretamente com um arquivo de usuário ausente.
- Testar se `_deep_merge` funciona para chaves de primeiro nível e aninhadas.
- Testar se `get` recupera valores de primeiro nível e aninhados corretamente.
- Testar se `get` retorna o valor padrão para chaves inexistentes.
- Testar o tratamento de erro para um arquivo `config.yaml` malformado (inválido).

## ❗ Pontos de Atenção e Melhoria

- **Estado Global:** A instância `config` global é um anti-pattern que dificulta os testes e o desacoplamento. O ideal seria usar injeção de dependência para fornecer o objeto de configuração aos componentes que precisam dele.
- **Falta de Validação de Schema:** O sistema não valida a estrutura do arquivo de configuração do usuário. Um usuário pode inserir chaves com tipos de dados errados, causando erros em tempo de execução em outras partes do código. A implementação de uma validação com uma biblioteca como `jsonschema` tornaria o sistema mais robusto.
- **Tratamento de Erros:** Erros de parsing no YAML do usuário apenas imprimem um aviso no console. Dependendo da criticidade da configuração, uma falha no carregamento poderia justificar o encerramento da aplicação com uma mensagem de erro clara.
- **Segurança:** O uso de `yaml.safe_load` é uma excelente prática de segurança que previne a execução de código arbitrário a partir do arquivo de configuração.
