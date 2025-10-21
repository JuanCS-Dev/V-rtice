
# 📄 `vertice/commands/adr.py`

## 📋 Descrição

Este módulo implementa os comandos da CLI para interagir com o serviço de ADR (Ameaça Digital em Redes). Ele permite obter o status e as métricas do sistema, além de submeter arquivos, tráfego de rede e processos para análise manual.

**Dependências Principais:**
- `typer`: Para a criação dos comandos e subcomandos da CLI.
- `ADRCoreConnector`: Para a comunicação com o microserviço de ADR.
- `output.py`: Para a formatação da saída em tabelas e JSON.
- `auth.py`: Para o controle de acesso aos comandos.

## 🏗️ Funções Públicas (Comandos da CLI)

### `status(json_output, verbose)`

Verifica e exibe o status atual do sistema ADR.

**Parâmetros:**
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Verifica a saúde do `ADRCoreConnector`.
3.  Chama o método `get_status` do conector.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `metrics(json_output, verbose)`

Obtém e exibe as principais métricas de performance do sistema ADR, como MTTR (Mean Time to Respond) e taxa de detecção.

**Parâmetros:**
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Verifica a saúde do conector.
3.  Chama o endpoint `/api/adr/metrics`.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `analyze file(path, json_output, verbose)`

Submete um arquivo local para análise pelo serviço de ADR.

**Parâmetros:**
- `path (str)`: O caminho do arquivo a ser analisado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Envia o **caminho** do arquivo para o endpoint `/api/adr/analyze/file`.
3.  Exibe o resultado da análise.

---

### `analyze network(ip, json_output, verbose)`

Submete um endereço de IP para análise de tráfego de rede pelo serviço de ADR.

**Parâmetros:**
- `ip (str)`: O endereço de IP a ser analisado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Envia o IP para o endpoint `/api/adr/analyze/network`.
3.  Exibe o resultado da análise.

---

### `analyze process(cmd, json_output, verbose)`

Submete uma string de comando de processo para análise pelo serviço de ADR.

**Parâmetros:**
- `cmd (str)`: O comando ou processo a ser analisado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Envia a string do comando para o endpoint `/api/adr/analyze/process`.
3.  Exibe o resultado da análise.

## 💡 Exemplos de Uso

**Verificar o status do sistema ADR:**
```bash
vcli adr status
```

**Analisar um arquivo suspeito:**
```bash
vcli adr analyze file /tmp/suspicious.exe
```

**Analisar um processo em execução:**
```bash
vcli adr analyze process "powershell -enc ..."
```

## 🧪 Guia de Testes

1.  **Testes Unitários:**
    - Mockar o `ADRCoreConnector`.
    - Verificar se cada comando chama o endpoint correto do conector com os parâmetros adequados.
    - Testar o tratamento de erro quando o conector está offline.

2.  **Testes de Integração:**
    - Executar os comandos contra uma instância real do serviço de ADR.
    - Para `analyze file`, testar com caminhos de arquivos válidos e inválidos.
    - Para `analyze network`, testar com IPs válidos e inválidos.
    - Para `analyze process`, testar com strings de comando simples e complexas.
    - Validar se a resposta da API é corretamente formatada e exibida.

## ❗ Pontos de Atenção e Melhoria

- **Vulnerabilidade de Path Traversal (Potencial/Alta):** O comando `analyze file` envia um caminho de arquivo local para o servidor. Se o servidor for ingênuo e usar esse caminho diretamente, isso pode levar a uma vulnerabilidade de Path Traversal, permitindo que um invasor leia arquivos arbitrários no servidor. A implementação do backend é crucial para a segurança aqui.
- **Vulnerabilidade de Injeção de Comando (Potencial/Alta):** O comando `analyze process` envia uma string de comando para o servidor. Se o servidor executar essa string sem a devida sanitização, isso pode levar a uma vulnerabilidade de Injeção de Comando. A implementação do backend é crítica.
- **Duplicação de Código (Crítica):** A lógica de execução (health check, spinner, chamada, etc.) é quase idêntica em todos os cinco comandos deste arquivo. Este é um débito técnico severo que viola o princípio DRY e torna a manutenção extremamente difícil. A lógica deve ser abstraída para um decorator ou função auxiliar.
- **Falta de Validação de Entrada:** Nenhuma das entradas (`path`, `ip`, `cmd`) é validada no lado do cliente antes de ser enviada ao backend.
