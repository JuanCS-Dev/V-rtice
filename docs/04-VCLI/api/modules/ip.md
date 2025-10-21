
# 📄 `vertice/commands/ip.py`

## 📋 Descrição

Este módulo contém os comandos da CLI relacionados a operações de Inteligência de IP (IP Intelligence). Ele permite aos usuários analisar endereços de IP, detectar seu próprio IP público e realizar análises em massa a partir de um arquivo.

**Dependências Principais:**
- `typer`: Para a criação dos comandos da CLI.
- `IPIntelConnector`: Para se comunicar com o microserviço de IP Intelligence.
- `output.py`: Para formatação da saída (tabelas, JSON, etc.).
- `auth.py`: Para garantir que o usuário esteja autenticado antes de executar os comandos.

## 🏗️ Funções Públicas (Comandos da CLI)

### `analyze(ip_address, json_output, quiet, verbose)`

Analisa um único endereço de IP para obter informações de geolocalização, reputação e rede.

**Parâmetros:**
- `ip_address (str)`: O endereço de IP a ser analisado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída completa em formato JSON. (Opcional)
- `quiet (bool)`: Se `True`, exibe apenas o nível de ameaça (ex: `CLEAN`, `MALICIOUS`). (Opcional)
- `verbose (bool)`: Se `True`, exibe logs detalhados sobre o processo de análise. (Opcional)

**Lógica:**
1.  Requer autenticação do usuário.
2.  Verifica a saúde do serviço `IPIntelConnector`.
3.  Chama o método `analyze_ip` do conector.
4.  Formata e exibe o resultado como uma tabela rica, JSON ou uma única palavra, dependendo das flags.

---

### `my_ip(json_output)`

Detecta e exibe o endereço de IP público do usuário.

**Parâmetros:**
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Chama o método `get_my_ip` do `IPIntelConnector`.
3.  Exibe o IP detectado no console.

---

### `bulk(file, json_output, verbose)`

Realiza a análise de múltiplos endereços de IP contidos em um arquivo de texto.

**Parâmetros:**
- `file (str)`: O caminho para o arquivo de texto contendo um IP por linha. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída completa de todos os IPs em um único array JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs para cada IP sendo analisado. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Lê o arquivo e extrai a lista de IPs.
3.  Itera sobre a lista, chamando o comando `analyze_ip` para cada IP de forma **sequencial**.
4.  Agrega e exibe os resultados.

## 🔬 Funções Internas

Dentro de cada comando (`analyze`, `my_ip`, `bulk`), há uma função `async` aninhada (`_analyze`, `_my_ip`, `_bulk`) que contém a lógica principal. Este padrão é usado para permitir a execução de código assíncrono dentro dos comandos `typer` que são síncronos por padrão.

## 💡 Exemplos de Uso

**Analisar um IP e exibir em formato de tabela:**
```bash
vcli ip analyze 8.8.8.8
```

**Analisar um IP e obter a saída em JSON:**
```bash
vcli ip analyze 1.1.1.1 --json
```

**Detectar o IP público:**
```bash
vcli ip my-ip
```

**Analisar uma lista de IPs de um arquivo:**
```bash
# Crie um arquivo ips.txt com:
# 8.8.8.8
# 1.1.1.1
# 9.9.9.9

vcli ip bulk ips.txt
```

## 🧪 Guia de Testes

Para testar este módulo, os seguintes cenários devem ser cobertos:

1.  **Testes Unitários:**
    - Mockar o `IPIntelConnector`.
    - Verificar se a função `analyze` chama `connector.analyze_ip` com o IP correto.
    - Verificar se a função `my_ip` chama `connector.get_my_ip`.
    - Verificar se a função `bulk` lê o arquivo corretamente e chama `analyze_ip` para cada linha.
    - Testar as diferentes flags de saída (`--json`, `--quiet`).

2.  **Testes de Integração:**
    - Executar os comandos contra uma instância real (ou mock) do serviço de IP Intelligence.
    - Validar se a saída formatada (tabela, JSON) corresponde aos dados retornados pela API.
    - Testar o tratamento de erros quando o serviço está offline.
    - Testar o comando `bulk` com um arquivo contendo IPs válidos e inválidos.

## ❗ Pontos de Atenção e Melhoria

- **Vulnerabilidade de Path Traversal:** O comando `bulk` aceita um caminho de arquivo diretamente, o que é um risco de segurança. A entrada deve ser sanitizada.
- **Performance:** O comando `bulk` processa os IPs de forma sequencial. Para listas grandes, isso é muito lento. A implementação deveria ser refatorada para usar `asyncio.gather` e realizar as chamadas em paralelo.
- **Duplicação de Código:** A estrutura de `try/except/finally` e a inicialização do conector são repetidas em todas as funções. Isso deve ser abstraído para um decorator ou função auxiliar.
