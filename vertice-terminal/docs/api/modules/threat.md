
# 📄 `vertice/commands/threat.py`

## 📋 Descrição

Este módulo agrupa os comandos da CLI para operações de *Threat Intelligence*. Ele permite aos usuários consultar indicadores de ameaça, checar alvos contra ameaças conhecidas, escanear arquivos e acessar feeds de inteligência.

**IMPORTANTE:** A implementação deste módulo é **altamente problemática**. Além de ter funcionalidades ausentes, ele utiliza a API do conector de forma incorreta e duplica código massivamente.

**Dependências Principais:**
- `typer`: Para a criação dos comandos da CLI.
- `ThreatIntelConnector`: Para a comunicação com o serviço de Threat Intelligence.
- `output.py`: Para formatação da saída.
- `auth.py`: Para controle de acesso.

## 🏗️ Funções Públicas (Comandos da CLI)

### `lookup(indicator, json_output, verbose)`

Consulta um indicador de ameaça (como um IP, domínio ou hash) no serviço de Threat Intelligence.

**Parâmetros:**
- `indicator (str)`: O indicador a ser consultado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

**Lógica:**
1.  Requer autenticação.
2.  Verifica a saúde do `ThreatIntelConnector`.
3.  Chama o método `lookup_threat` do conector com o indicador fornecido.
4.  Exibe o resultado em uma tabela ou em JSON.

---

### `check(target, json_output, verbose)`

Verifica um alvo (um arquivo, um domínio, etc.) contra ameaças conhecidas. **Atualmente, este comando está implementado de forma incorreta**, pois simplesmente chama o mesmo método `lookup_threat` do comando `lookup`.

**Parâmetros:**
- `target (str)`: O alvo a ser verificado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

---

### `scan(file_path, json_output, verbose)`

Escaneia um arquivo em busca de ameaças. **Este comando também está implementado de forma incorreta**, pois passa um caminho de arquivo para o método `lookup_threat`, que espera um indicador.

**Parâmetros:**
- `file_path (str)`: O caminho do arquivo a ser escaneado. (Obrigatório)
- `json_output (bool)`: Se `True`, exibe a saída em formato JSON. (Opcional)
- `verbose (bool)`: Se `True`, exibe logs de atividade. (Opcional)

---

### `feed(json_output, follow)`

Placeholder para um futuro comando que acessará um feed de Threat Intelligence. Atualmente, apenas exibe uma mensagem "coming soon".

## 💡 Exemplos de Uso

**Consultar um domínio:**
```bash
vcli threat lookup suspicious-domain.com
```

**Escanear um arquivo (uso incorreto na implementação atual):**
```bash
vcli threat scan /path/to/file.exe
```

## 🧪 Guia de Testes

1.  **Testes Unitários:**
    - Mockar o `ThreatIntelConnector`.
    - Verificar se o comando `lookup` chama `lookup_threat` com o indicador correto.
    - **Corrigir e testar** os comandos `check` e `scan` para que chamem os endpoints corretos da API (que provavelmente não existem ainda).

2.  **Testes de Integração:**
    - Executar o comando `lookup` com indicadores conhecidos (IPs, domínios, hashes maliciosos e benignos) e validar os resultados.
    - Após a correção, testar os comandos `check` e `scan` contra alvos e arquivos reais.

## ❗ Pontos de Atenção e Melhoria

- **Duplicação de Código (Crítica):** Os comandos `lookup`, `check`, e `scan` são cópias quase exatas um do outro. A lógica de execução precisa ser abstraída para uma função auxiliar ou decorator para seguir o princípio DRY.
- **Uso Incorreto da API (Crítico):** Os comandos `check` e `scan` estão usando o endpoint `lookup_threat` de forma completamente errada. Isso torna a funcionalidade deles, na melhor das hipóteses, imprevisível e, na pior, perigosa. Eles precisam ser reescritos para interagir com os endpoints corretos do serviço de backend.
- **Vulnerabilidade de Path Traversal (Potencial/Alta):** O comando `scan` passa um `file_path` para o backend. Se o backend (mesmo que incorretamente) tentar usar esse caminho, isso pode levar a uma vulnerabilidade de Path Traversal no servidor.
- **Funcionalidade Inexistente:** O comando `feed` não está implementado.
